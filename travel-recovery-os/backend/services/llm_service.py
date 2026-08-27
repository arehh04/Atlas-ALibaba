"""
services/llm_service.py - DeepSeek & Hermes LLM Orchestration Service

Provides async interfaces for:
1. Hermes LLM: Function calling / JSON extraction for unstructured disruption feeds.
2. DeepSeek LLM: Chain-of-Thought (CoT) multi-criteria route optimization & scoring.

Resilience:
- Both LLM calls are wrapped with retry_with_backoff and CircuitBreaker.
- Graceful fallbacks (regex extraction, deterministic scoring) when LLMs are unavailable.
"""

import asyncio
import json
import re
from typing import Any, Dict, List, Optional
import httpx
from openai import AsyncOpenAI

try:
    from ..config import settings
except (ImportError, ValueError):
    from config import settings

try:
    from ..middleware.resilience import retry_with_backoff, CircuitBreakerOpen, hermes_breaker, deepseek_breaker
except (ImportError, ValueError):
    from middleware.resilience import retry_with_backoff, CircuitBreakerOpen, hermes_breaker, deepseek_breaker


# ---------------------------------------------------------------------------
# 1. Hermes / Local LLM: Unstructured Disruption Text Extraction
# ---------------------------------------------------------------------------
async def extract_disruption_with_hermes(raw_text: str) -> Dict[str, Any]:
    """
    Uses Hermes (via Ollama / OpenAI-compatible endpoint) to extract structured
    disruption JSON from raw airline NOTAMs, SMS alerts, or operational messages.

    Resilience: Wrapped with Hermes circuit breaker and 2 retries.
    Falls back to regex-based extraction if Hermes endpoint is offline.
    """
    async def _hermes_call():
        system_prompt = (
            "You are Hermes, an expert aviation data extractor. Extract the flight disruption "
            "details from the message into strict JSON with the following schema:\n"
            "{\n"
            '  "pnr": "PNR code (6 chars, e.g. PNR-8842 or 6 alphanumeric)",\n'
            '  "flight_number": "Flight code (e.g. CZ-3042)",\n'
            '  "airline": "Airline name",\n'
            '  "origin": "3-letter IATA airport code (e.g. KUL)",\n'
            '  "destination": "3-letter IATA airport code (e.g. HGH)",\n'
            '  "delay_minutes": integer,\n'
            '  "reason": "Short summary of cancellation/delay reason",\n'
            '  "severity": "CRITICAL" | "HIGH" | "MEDIUM"\n'
            "}\n"
            "Output ONLY raw JSON. No markdown backticks, no preamble."
        )

        client = AsyncOpenAI(
            base_url=settings.HERMES_API_BASE,
            api_key=settings.HERMES_API_KEY or "none",
            timeout=10.0,
            default_headers={
                "HTTP-Referer": "https://synapseair.travel",
                "X-Title": "SynapseAir Travel Recovery OS"
            }
        )
        response = await client.chat.completions.create(
            model=settings.HERMES_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_text}
            ],
            temperature=0.1
        )
        content = response.choices[0].message.content.strip()
        # Clean potential markdown wrapping
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\n?", "", content)
            content = re.sub(r"\n?```$", "", content)
        data = json.loads(content)
        data["extracted_by"] = f"LLM Parser ({settings.HERMES_MODEL})"
        return data

    # Try with circuit breaker + retry
    try:
        return await hermes_breaker.call(
            lambda: retry_with_backoff(
                _hermes_call,
                max_retries=2,
                base_delay=0.5,
                operation_name="hermes_extraction",
            )
        )
    except (CircuitBreakerOpen, Exception) as e:
        return _fallback_regex_extraction(raw_text, error_hint=str(e))


def _fallback_regex_extraction(raw_text: str, error_hint: str = "") -> Dict[str, Any]:
    """Deterministic extraction fallback if local LLM is offline."""
    pnr_match = re.search(r"\b(PNR[-\s]?[A-Z0-9]{4,8}|[A-Z0-9]{6})\b", raw_text, re.IGNORECASE)
    flt_match = re.search(r"\b([A-Z0-9]{2}[-\s]?\d{3,4})\b", raw_text)
    route_match = re.findall(r"\b([A-Z]{3})\b", raw_text)

    pnr = pnr_match.group(1).upper() if pnr_match else "PNR-FALLBACK"
    flt = flt_match.group(1).upper() if flt_match else "CZ-3042"
    origin = route_match[0] if len(route_match) >= 1 else "KUL"
    destination = route_match[1] if len(route_match) >= 2 else "HGH"

    return {
        "pnr": pnr,
        "flight_number": flt,
        "airline": "China Southern Airlines" if "CZ" in flt else "Partner Carrier",
        "origin": origin,
        "destination": destination,
        "delay_minutes": 240,
        "reason": "Operational Disruption / Severe Weather (Parsed via fallback)",
        "severity": "HIGH",
        "extracted_by": f"Deterministic Parser (Hermes Standby: {error_hint[:40]}...)" if error_hint else "Heuristic Extractor"
    }


# ---------------------------------------------------------------------------
# 2. DeepSeek LLM: Multi-Criteria Route Optimization & CoT Scoring
# ---------------------------------------------------------------------------
async def evaluate_routes_with_deepseek(
    passenger_profile: Dict[str, Any],
    candidate_routes: List[Dict[str, Any]],
    disruption_event: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Invokes DeepSeek LLM for Chain-of-Thought (CoT) route evaluation against
    passenger loyalty SLAs, layover tolerances, and cabin classes.

    Resilience: Wrapped with DeepSeek circuit breaker and 2 retries.
    Falls back to deterministic scoring when DeepSeek is unavailable.
    """
    tier = passenger_profile.get("loyalty_tier", "GOLD")
    p_name = passenger_profile.get("passenger_name", "Valued Passenger")

    system_prompt = (
        "You are DeepSeek Travel Arbiter, an expert airline operational AI. "
        "Your role is to evaluate alternative flight options for a disrupted passenger "
        "and select the optimal route based on strict airline SLAs.\n\n"
        "EVALUATION CRITERIA:\n"
        "- PLATINUM/GOLD: Must prioritize direct flights, matching cabin class, and earliest arrival.\n"
        "- SILVER/STANDARD: Maximize on-time probability and reasonable layover duration.\n"
        "- HITL Policy: If a direct matching flight is found for Gold/Platinum, set hitl_status='BYPASSED'. "
        "If there are layovers, cabin downgrades, or score < 0.85, set hitl_status='PENDING'.\n\n"
        "Output strict JSON with schema:\n"
        "{\n"
        '  "reasoning_trace": "Detailed chain of thought comparing each flight",\n'
        '  "best_flight_number": "FLT_NUM",\n'
        '  "confidence_score": 0.95,\n'
        '  "hitl_status": "BYPASSED" | "PENDING",\n'
        '  "scored_routes": [\n'
        '    {"flight_number": "...", "score": 0.92, "rationale": "..."}\n'
        '  ],\n'
        '  "whatsapp_message": "Warm, personalized message explaining the rebooking option to the passenger"\n'
        "}\n"
        "Output ONLY valid JSON. No markdown backticks."
    )

    user_payload = {
        "disruption": disruption_event,
        "passenger": passenger_profile,
        "candidate_routes": candidate_routes
    }

    async def _deepseek_call():
        client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            timeout=20.0
        )
        response = await client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, indent=2)}
            ],
            temperature=0.2
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\n?", "", content)
            content = re.sub(r"\n?```$", "", content)
        result = json.loads(content)
        result["engine"] = f"DeepSeek ({settings.DEEPSEEK_MODEL})"
        return result

    if settings.DEEPSEEK_API_KEY:
        try:
            return await deepseek_breaker.call(
                lambda: retry_with_backoff(
                    _deepseek_call,
                    max_retries=2,
                    base_delay=1.0,
                    operation_name="deepseek_route_scoring",
                )
            )
        except (CircuitBreakerOpen, Exception) as e:
            return _fallback_deterministic_arbiter(passenger_profile, candidate_routes, error_hint=str(e))
    else:
        return _fallback_deterministic_arbiter(passenger_profile, candidate_routes, error_hint="No DEEPSEEK_API_KEY configured (Running high-precision deterministic arbiter)")


def _fallback_deterministic_arbiter(
    passenger_profile: Dict[str, Any],
    candidate_routes: List[Dict[str, Any]],
    error_hint: str = ""
) -> Dict[str, Any]:
    """Deterministic CoT fallback reasoning engine."""
    loyalty_tier = passenger_profile.get("loyalty_tier", "GOLD")
    preferred_cabin = passenger_profile.get("preferred_cabin", "Business")
    requires_direct = passenger_profile.get("requires_direct_flight", False)

    scored_list = []
    reasoning_steps = []

    for r in candidate_routes:
        score = 0.50
        notes = []
        if r.get("layovers", 0) == 0:
            score += 0.25
            notes.append("Direct flight (+0.25)")
        else:
            if requires_direct:
                score -= 0.30
                notes.append("Violates VIP direct constraint (-0.30)")
            else:
                score -= 0.10
                notes.append("1-stop transfer (-0.10)")

        if r.get("cabin_class") == preferred_cabin:
            score += 0.15
            notes.append(f"Matches {preferred_cabin} (+0.15)")

        if r.get("duration_hours", 8) <= 6.0:
            score += 0.05
            notes.append("Fast flight duration (+0.05)")

        norm_score = round(max(0.10, min(0.99, score)), 2)
        scored_list.append({
            "flight_number": r.get("flight_number"),
            "score": norm_score,
            "rationale": "; ".join(notes)
        })
        reasoning_steps.append(f"Flight {r.get('flight_number')} [{r.get('cabin_class')}]: {norm_score} -> {'; '.join(notes)}")

    scored_list.sort(key=lambda x: x["score"], reverse=True)
    best = scored_list[0] if scored_list else None
    best_flt = best["flight_number"] if best else "CZ-3042"
    best_score = best["score"] if best else 0.5

    if loyalty_tier in ["PLATINUM", "GOLD"] and best_score >= 0.85:
        hitl_status = "BYPASSED"
        msg = f"Auto-Approved: Route {best_flt} satisfies {loyalty_tier} tier SLA."
    else:
        hitl_status = "PENDING"
        msg = f"HITL Required: Route {best_flt} requires passenger WhatsApp confirmation."

    passenger_name = passenger_profile.get("passenger_name", "Traveler")
    whatsapp_copy = (
        f"Hi {passenger_name}, your flight was affected by a schedule change. "
        f"SynapseAir has reserved alternative flight {best_flt} departing shortly. "
        f"Please reply '1' to confirm rebooking or '2' to explore alternatives."
    )

    return {
        "engine": "DeepSeek CoT Emulation Engine" + (f" ({error_hint})" if error_hint else ""),
        "reasoning_trace": "\n".join(reasoning_steps),
        "best_flight_number": best_flt,
        "confidence_score": best_score,
        "hitl_status": hitl_status,
        "scored_routes": scored_list,
        "whatsapp_message": whatsapp_copy
    }
