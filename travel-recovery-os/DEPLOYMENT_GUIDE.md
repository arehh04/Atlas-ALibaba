# 🚀 SynapseAir Full-Stack Deployment Guide

This guide covers deploying **SynapseAir** in under 5 minutes using modern free/low-cost platforms:
* **Frontend (Vue 3 + Vite SPA)**: [Vercel](#1-frontend-deployment-vercel-recommended) or [Cloudflare Pages](#2-frontend-deployment-cloudflare-pages)
* **Backend (FastAPI + LangGraph + WebSockets)**: [Hugging Face Spaces](#3-backend-deployment-hugging-face-spaces-docker-free) or [Render / Railway](#4-backend-deployment-render--railway)

---

## 🏗️ Architecture at a Glance

```
┌────────────────────────────────────────┐       HTTPS / WSS REST & WebSockets       ┌────────────────────────────────────────┐
│           FRONTEND (VUE 3)             ├───────────────────────────────────────────▶│           BACKEND (FASTAPI)            │
│  Hosted on: Vercel / Cloudflare Pages  │                                           │  Hosted on: Hugging Face Spaces / Render│
│  Config: `VITE_API_BASE_URL`           │◀───────────────────────────────────────────┤  Exposes: `/health`, `/ws/`, `/webhook`│
└────────────────────────────────────────┘       Real-Time Swarm Telemetry Stream    └────────────────────────────────────────┘
```

---

## 1. Backend Deployment: Hugging Face Spaces (Docker - 100% Free)

Hugging Face Spaces provides free 2-vCPU / 16GB RAM container hosting with full WebSocket support and HTTPS certificates.

### Step-by-Step Instructions:
1. Go to [huggingface.co/new-space](https://huggingface.co/new-space).
2. Set Space Name: `synapseair-backend` (or your preferred name).
3. Select **License**: `MIT` or `Apache 2.0`.
4. Select **Space SDK**: Choose **Docker** $\rightarrow$ **Blank**.
5. Choose **Public** (or Private).
6. Click **Create Space**.
7. Under **Settings** $\rightarrow$ **Variables and secrets**, add your environment variables:
   * `DEEPSEEK_API_KEY`: *(Optional - system includes fallback mocks if omitted)*
   * `DEEPSEEK_MODEL`: `deepseek-v4-flash`
   * `SYNAPSE_API_SECRET`: `default-insecure-secret-change-in-prod`
   * `ENVIRONMENT`: `production`
   * `ATLAS_CLIENT_ID`: `CTR12752_api_1`
   * `ATLAS_CLIENT_SECRET`: `sandbox-sk-CTR12752_api_1`
   * `ATLAS_BASE_URL`: `https://sandbox.atriptech.com`
8. Push the repository to your Hugging Face Space Git remote (or use the web UI upload):
   ```bash
   git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/synapseair-backend
   git push hf main
   ```
9. Once built, your backend URL will be:
   `https://YOUR_USERNAME-synapseair-backend.hf.space`

---

## 2. Frontend Deployment: Vercel (Recommended for Vue 3)

Vercel provides edge delivery with automatic CI/CD on every Git push.

### Step-by-Step Instructions:
1. Go to [vercel.com/new](https://vercel.com/new) and import your GitHub repository (`Atlas-ALibaba`).
2. Configure project settings:
   * **Framework Preset**: `Vite`
   * **Root Directory**: Click `Edit` and select `travel-recovery-os/frontend`
   * **Build Command**: `npm run build`
   * **Output Directory**: `dist`
3. Expand **Environment Variables** and add:
   * `VITE_API_BASE_URL`: `https://YOUR_USERNAME-synapseair-backend.hf.space` (or your backend domain)
   * `VITE_API_TOKEN`: `default-insecure-secret-change-in-prod`
4. Click **Deploy**.
5. In ~45 seconds, your live production frontend is ready (e.g., `https://synapseair.vercel.app`).

> **Note**: The included `vercel.json` automatically handles SPA routing rewrites so page reloads never produce 404 errors.

---

## 3. Alternative Frontend: Cloudflare Pages

1. In the Cloudflare Dashboard, go to **Workers & Pages** $\rightarrow$ **Create Application** $\rightarrow$ **Pages** $\rightarrow$ **Connect to Git**.
2. Select your GitHub repository (`Atlas-ALibaba`).
3. Set build configuration:
   * **Framework preset**: `Vue` / `Vite`
   * **Root directory**: `travel-recovery-os/frontend`
   * **Build command**: `npm run build`
   * **Build output directory**: `dist`
4. Under **Environment variables**, set:
   * `VITE_API_BASE_URL`: `https://your-backend-domain.com`
5. Click **Save and Deploy**. (The included `public/_redirects` ensures full SPA support).

---

## 4. Alternative Backend: Render / Railway

### Render:
1. Go to [dashboard.render.com](https://dashboard.render.com/) $\rightarrow$ **New Web Service**.
2. Connect your GitHub repository.
3. Select **Docker** environment.
4. Set **Root Directory**: `travel-recovery-os` (uses the root `Dockerfile`).
5. Choose **Free** instance type.
6. Under **Environment Variables**, add:
   * `PORT`: `8000`
   * `DEEPSEEK_MODEL`: `deepseek-v4-flash`
   * `SYNAPSE_API_SECRET`: `your-secret-key`
7. Click **Create Web Service**.

---

## 5. Local Production Smoke Test

Before pushing live, you can test the production build locally:

```bash
# 1. Build and preview frontend
cd travel-recovery-os/frontend
npm run build
npm run preview -- --port 4173

# 2. Run backend in production mode
cd travel-recovery-os
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
```

---

## 6. Verification Checklist

| Test Item | Verification Method | Expected Result |
| :--- | :--- | :--- |
| **Backend Health** | Open `https://<backend-url>/health` | `{"status": "online", ...}` |
| **System Status** | Open `https://<backend-url>/api/system/status` | `{"status": "HEALTHY", ...}` |
| **WebSocket Stream** | Launch SQ108 scenario on Frontend | Telemetry logs stream in real time |
| **WhatsApp HITL** | Launch MH128 scenario $\rightarrow$ click Accept | Graph resumes and e-ticket is rendered |

