# Deployment Guide - Agentic KPI Assistant

## Quick Deploy to Render.com (Recommended for Demo)

### Step 1: Push to GitHub
```bash
cd "/Users/devesh.b.sharma/Astra Zeneca/agentic-kpi-assistant"
git init
git add .
git commit -m "Initial commit - Agentic KPI Assistant"
git remote add origin https://github.com/YOUR_USERNAME/agentic-kpi-assistant.git
git push -u origin main
```

### Step 2: Deploy Backend on Render
1. Go to https://render.com and sign up/login
2. Click "New" → "Web Service"
3. Connect your GitHub repo
4. Configure:
   - **Name**: `agentic-kpi-backend`
   - **Root Directory**: `backend`
   - **Runtime**: Node
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start`
   - **Plan**: Free

5. Add Environment Variables:
   - `NODE_ENV` = `production`
   - `AWS_REGION` = `us-east-1`
   - `AWS_ACCESS_KEY_ID` = `<your-key>`
   - `AWS_SECRET_ACCESS_KEY` = `<your-secret>`
   - `BEDROCK_MODEL_ID` = `us.anthropic.claude-3-5-sonnet-20241022-v2:0`

6. Click "Create Web Service"
7. Copy the URL (e.g., `https://agentic-kpi-backend.onrender.com`)

### Step 3: Deploy Frontend on Render
1. Click "New" → "Static Site"
2. Connect the same GitHub repo
3. Configure:
   - **Name**: `agentic-kpi-frontend`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`

4. Add Environment Variable:
   - `VITE_API_BASE_URL` = `https://agentic-kpi-backend.onrender.com` (your backend URL)

5. Click "Create Static Site"

### Step 4: Access Your App
Your app will be live at: `https://agentic-kpi-frontend.onrender.com`

Login credentials:
- Username: `devesh`
- Password: `devesh123`

---

## Alternative: Deploy with Vercel + Railway

### Backend on Railway
1. Go to https://railway.app
2. New Project → Deploy from GitHub
3. Select `backend` folder
4. Add environment variables (same as above)

### Frontend on Vercel
1. Go to https://vercel.com
2. Import GitHub repo
3. Set root directory to `frontend`
4. Add `VITE_API_BASE_URL` env variable

---

## Local Demo with ngrok (Quickest)

If ngrok is installed:
```bash
# Terminal 1: Start backend
cd backend && npm run dev

# Terminal 2: Start frontend
cd frontend && npm run dev

# Terminal 3: Expose backend
ngrok http 3001

# Update frontend/.env with ngrok URL
echo "VITE_API_BASE_URL=https://xxxx.ngrok.io" > frontend/.env.local

# Restart frontend
```

---

## Environment Variables Reference

### Backend
| Variable | Value |
|----------|-------|
| `NODE_ENV` | `production` |
| `AWS_REGION` | `us-east-1` |
| `AWS_ACCESS_KEY_ID` | Your AWS key |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret |
| `BEDROCK_MODEL_ID` | `us.anthropic.claude-3-5-sonnet-20241022-v2:0` |

### Frontend
| Variable | Value |
|----------|-------|
| `VITE_API_BASE_URL` | Your backend URL |
