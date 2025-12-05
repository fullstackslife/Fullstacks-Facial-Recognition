# 🚀 Quick Start: Deploy to Railway + Vercel

This is a quick guide to deploy your Face Detection app using Railway (backend) and Vercel (frontend).

## Prerequisites

- GitHub account
- Railway account (free at [railway.app](https://railway.app))
- Vercel account (free at [vercel.com](https://vercel.com))

## Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/face-detct.git
git push -u origin main
```

## Step 2: Deploy Backend to Railway

### Option A: Via Railway Dashboard (Easiest)

1. Go to [railway.app](https://railway.app) and sign in
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your `face-detct` repository
5. Railway will automatically:
   - Detect it's a Python app
   - Install dependencies
   - Deploy your app
6. Click on your project → **Settings** → **Generate Domain**
7. Copy your Railway URL (e.g., `https://your-app.railway.app`)

### Option B: Via Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize
railway init

# Deploy
railway up

# Get your URL
railway domain
```

### Set Environment Variables (Railway Dashboard)

1. Go to your project → **Variables**
2. Add:
   - `FLASK_ENV=production`
   - `PORT=8080` (Railway sets this automatically, but you can override)

## Step 3: Deploy Frontend to Vercel

### Option A: Via Vercel Dashboard (Easiest)

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click **"Add New Project"**
3. Import your GitHub repository
4. Configure:
   - **Framework Preset:** Other
   - **Root Directory:** `./` (root)
   - **Build Command:** (leave empty or `echo "No build needed"`)
   - **Output Directory:** (leave empty)
5. Add Environment Variables:
   - `FLASK_ENV=production`
6. Click **"Deploy"**

### Option B: Via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel

# For production
vercel --prod
```

## Step 4: Update CORS (If Needed)

If you're accessing the Railway backend from Vercel frontend, update `app.py`:

```python
from flask_cors import CORS

# Add after app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://your-frontend.vercel.app", "http://localhost:8080"]}})
```

And add to `requirements.txt`:
```
flask-cors>=3.0.10
```

## Step 5: Test Your Deployment

1. **Backend (Railway):**
   - Visit: `https://your-app.railway.app`
   - Should see the face detection interface

2. **Frontend (Vercel):**
   - Visit: `https://your-app.vercel.app`
   - Should connect to Railway backend

## 🔄 Auto-Deployment

Both Railway and Vercel automatically deploy when you push to GitHub:

```bash
git add .
git commit -m "Update app"
git push origin main
```

Deployments happen automatically! 🎉

## 📝 Important Notes

### Camera Access Limitation

⚠️ **Cloud platforms cannot access physical cameras.**

For Railway/Vercel deployment:
- The app will run, but camera access won't work
- You'll need to:
  - Use WebRTC to stream from browser
  - Deploy on a device with camera access (Raspberry Pi, local server)
  - Use client-side face detection (MediaPipe, TensorFlow.js)

### Alternative: Local Deployment

For actual camera access, deploy locally:

```bash
# Make accessible on local network
python3 app.py
# Access from other devices: http://YOUR_IP:8080
```

Or use Docker with camera passthrough (see DEPLOYMENT.md).

## 🐛 Troubleshooting

### Railway Issues

**Build fails:**
- Check `requirements.txt` has all dependencies
- Verify Python version in `runtime.txt`

**App crashes:**
- Check Railway logs: `railway logs`
- Verify environment variables are set

### Vercel Issues

**Build fails:**
- Check `vercel.json` configuration
- Verify static files are in correct directories

**CORS errors:**
- Add CORS configuration (see Step 4)
- Verify Railway URL is correct

## 📚 Next Steps

- Set up custom domains
- Configure environment variables
- Set up monitoring
- Add authentication (if needed)

For detailed deployment options, see [DEPLOYMENT.md](DEPLOYMENT.md).

