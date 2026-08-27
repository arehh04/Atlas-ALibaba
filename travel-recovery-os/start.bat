@echo off
title SynapseAir - Operations Command Center Launcher
echo ======================================================================
echo       SYNAPSEAIR: AUTONOMOUS DISRUPTION RECOVERY SWARM
echo       Alibaba Cloud x Atlas Agentic AI Hackathon
echo ======================================================================
echo.

echo [1/2] Starting FastAPI + LangGraph Backend (Port 8001)...
start "SynapseAir Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload"

echo [2/2] Starting Vue 3 Command Center Dashboard (Port 5173)...
start "SynapseAir Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ======================================================================
echo All services launched!
echo - Command Center UI:  http://localhost:5173
echo - FastAPI Swagger:    http://127.0.0.1:8001/docs
echo - SSE Stream Stream:  http://127.0.0.1:8001/stream/:thread_id
echo ======================================================================
pause
