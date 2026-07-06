# CivicGuard AI: Production Deployment Guide

This guide provides instructions for deploying **CivicGuard AI (RoadGuard AI)** locally via Docker and to various cloud platforms.

---

## 📦 1. Local Deployment (Docker & Compose)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
- A Gemini API Key from [Google AI Studio](https://aistudio.google.com/h) (Optional: the system will run in high-fidelity simulation mode if not provided).

### Option A: Using Docker Compose (Recommended)
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and set your `GEMINI_API_KEY`:
   ```ini
   GEMINI_API_KEY=AIzaSy...
   ```
3. Build and launch the containerized application:
   ```bash
   docker-compose up --build
   ```
4. Access the dashboard at [http://localhost:5000](http://localhost:5000).

### Option B: Using Plain Docker CLI
1. Build the image:
   ```bash
   docker build -t civicguard-ai .
   ```
2. Run the container:
   ```bash
   docker run -d -p 5000:5000 -e GEMINI_API_KEY="your_api_key_here" civicguard-ai
   ```
3. Access the dashboard at [http://localhost:5000](http://localhost:5000).

---

## ☁️ 2. Deployment to Google Cloud Run

Google Cloud Run is the ideal production hosting choice as it natively supports serverless container deployment and integrates with Google services.

### Prerequisites
- [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install) installed.
- Docker installed and authenticated with Google Artifact Registry.

### Deployment Steps
1. **Initialize Google Cloud Project:**
   ```bash
   gcloud auth login
   gcloud config set project [YOUR_PROJECT_ID]
   ```
2. **Enable Required APIs:**
   ```bash
   gcloud services enable artifactregistry.googleapis.com run.googleapis.com
   ```
3. **Create an Artifact Registry Repository:**
   ```bash
   gcloud artifacts repositories create roadguard-repo \
     --repository-format=docker \
     --location=us-central1 \
     --description="CivicGuard Docker Repository"
   ```
4. **Configure Docker Authentication:**
   ```bash
   gcloud auth configure-docker us-central1-docker.pkg.dev
   ```
5. **Build and Tag Image:**
   ```bash
   docker build -t us-central1-docker.pkg.dev/[YOUR_PROJECT_ID]/roadguard-repo/civicguard-ai:v1 .
   ```
6. **Push Image to Registry:**
   ```bash
   docker push us-central1-docker.pkg.dev/[YOUR_PROJECT_ID]/roadguard-repo/civicguard-ai:v1
   ```
7. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy civicguard-service \
     --image=us-central1-docker.pkg.dev/[YOUR_PROJECT_ID]/roadguard-repo/civicguard-ai:v1 \
     --platform=managed \
     --region=us-central1 \
     --allow-unauthenticated \
     --set-env-vars=GEMINI_API_KEY="your_gemini_api_key" \
     --set-env-vars=JWT_SECRET="generate-a-secure-secret-key-string"
   ```
8. **Retrieve URL:** The terminal will output a secure URL (e.g. `https://civicguard-service-xxxx-uc.a.run.app`). Copy this link as your public dashboard deployment!

---

## 🚀 3. Deployment to Railway

Railway is a quick, git-integrated hosting platform.

1. Install the Railway CLI or use their web dashboard.
2. Link your GitHub repository to Railway.
3. In the Railway dashboard under **Variables**, add:
   - `GEMINI_API_KEY` = `your_gemini_api_key`
   - `JWT_SECRET` = `some_random_secure_string`
   - `PORT` = `5000`
4. Railway will automatically detect the `Dockerfile` and deploy it.
5. Under **Settings**, generate a domain to get your working public link!

---

## 🎨 4. Deployment to Render

Render is another cloud provider offering free/low-cost Web Service hosting.

1. Sign up on [Render](https://render.com/).
2. Click **New** -> **Web Service** and connect your GitHub repository.
3. Set the following configurations:
   - **Environment:** `Docker`
   - **Branch:** `main`
4. Under **Advanced**, add the following environment variables:
   - `GEMINI_API_KEY` = `your_gemini_api_key`
   - `JWT_SECRET` = `some_random_secure_string`
   - `PORT` = `5000`
5. Click **Deploy Web Service**.
6. Retrieve your public URL from the Render dashboard (e.g. `https://roadguard-ai.onrender.com`).
