# Deployment Guide

This guide covers various ways to deploy the Face Detection & Analysis System as a web application.

## ⚠️ Important Note

**Camera access requires local hardware access.** Most cloud hosting services cannot access physical cameras. These deployment options are best for:
- Local network deployment
- Docker containers with camera passthrough
- Development/testing environments
- Remote access to a machine with cameras

For production web deployment without local cameras, you would need to:
- Stream video from client browsers (WebRTC)
- Use cloud camera services
- Implement client-side face detection

## 🚂 Railway + Vercel Deployment (Recommended)

This setup uses Railway for the Flask backend and Vercel for the frontend (optional).

### Railway Backend Setup

1. **Install Railway CLI:**
```bash
npm i -g @railway/cli
```

2. **Login to Railway:**
```bash
railway login
```

3. **Initialize Railway project:**
```bash
railway init
```

4. **Link to existing project (if you have one):**
```bash
railway link
```

5. **Set environment variables:**
```bash
railway variables set FLASK_ENV=production
railway variables set PORT=8080
```

6. **Deploy:**
```bash
railway up
```

7. **Get your Railway URL:**
```bash
railway domain
```

Your backend will be available at: `https://your-app.railway.app`

### Vercel Frontend Setup (Optional)

**Option 1: Deploy Flask app to Vercel (Full Stack)**

1. **Install Vercel CLI:**
```bash
npm i -g vercel
```

2. **Login:**
```bash
vercel login
```

3. **Deploy:**
```bash
vercel
```

4. **For production:**
```bash
vercel --prod
```

**Option 2: Separate Frontend (If splitting frontend/backend)**

1. **Create frontend directory:**
```bash
mkdir vercel-frontend
# Copy static files and templates
```

2. **Deploy to Vercel:**
```bash
cd vercel-frontend
vercel
```

3. **Update API URL in frontend:**
Set `REACT_APP_API_URL` to your Railway backend URL

### GitHub Integration

1. **Connect Railway to GitHub:**
   - Go to Railway dashboard
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will auto-deploy on push to main branch

2. **Connect Vercel to GitHub:**
   - Go to Vercel dashboard
   - Click "Add New Project"
   - Import your GitHub repository
   - Configure build settings
   - Deploy

3. **Auto-deploy on push:**
   - Both platforms support auto-deployment
   - Push to `main` branch triggers deployment
   - Use GitHub Actions for custom workflows (see `.github/workflows/`)

### Configuration

**Railway Environment Variables:**
```bash
FLASK_ENV=production
PORT=8080
HOST=0.0.0.0
```

**Vercel Environment Variables:**
```bash
FLASK_ENV=production
# If using separate frontend:
REACT_APP_API_URL=https://your-app.railway.app
```

### CORS Configuration (If separating frontend/backend)

If deploying frontend separately, update `app.py` to allow CORS:

```python
from flask_cors import CORS
CORS(app, resources={r"/*": {"origins": ["https://your-frontend.vercel.app"]}})
```

Add to `requirements.txt`:
```
flask-cors>=3.0.10
```

## 🐳 Docker Deployment

### Prerequisites
- Docker installed
- Docker Compose (optional)

### Build and Run

```bash
# Build the image
docker build -t face-detection .

# Run with camera access (Linux)
docker run -d \
  --name face-detection \
  --device=/dev/video0 \
  -p 8080:8080 \
  face-detection

# Run with camera access (macOS/Windows - may need different approach)
docker run -d \
  --name face-detection \
  --privileged \
  -p 8080:8080 \
  face-detection
```

### Using Docker Compose

```bash
docker-compose up -d
```

Access at: `http://localhost:8080`

## ☁️ Heroku Deployment

### Prerequisites
- Heroku CLI installed
- Heroku account

### Deploy Steps

1. **Login to Heroku:**
```bash
heroku login
```

2. **Create a new app:**
```bash
heroku create your-app-name
```

3. **Set environment variables:**
```bash
heroku config:set FLASK_ENV=production
```

4. **Deploy:**
```bash
git push heroku main
```

5. **Open the app:**
```bash
heroku open
```

**Note:** Heroku free tier doesn't support camera access. This would require a paid dyno with camera support or alternative architecture.

## 🚀 Railway Deployment

1. **Install Railway CLI:**
```bash
npm i -g @railway/cli
```

2. **Login:**
```bash
railway login
```

3. **Initialize and deploy:**
```bash
railway init
railway up
```

## 🌐 Render Deployment

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python3 app.py`
   - **Environment:** Python 3
5. Deploy

## 🖥️ Local Network Deployment

### Make it accessible on your local network

Modify `app.py`:

```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
```

Then access from other devices on your network:
```
http://YOUR_IP_ADDRESS:8080
```

Find your IP:
- **macOS/Linux:** `ifconfig | grep "inet "`
- **Windows:** `ipconfig`

## 🔒 Production Configuration

### Security Considerations

1. **Disable debug mode:**
```python
app.run(host='0.0.0.0', port=8080, debug=False)
```

2. **Use environment variables:**
```python
import os
port = int(os.environ.get('PORT', 8080))
debug = os.environ.get('FLASK_ENV') != 'production'
```

3. **Add authentication** (if exposing publicly):
```python
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    return username == 'admin' and password == 'your-secure-password'

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')
```

4. **Use HTTPS** (for production):
- Use a reverse proxy (nginx, Apache)
- Or use a service like Cloudflare Tunnel

## 📦 Standalone Executable (PyInstaller)

Create a standalone executable:

1. **Install PyInstaller:**
```bash
pip install pyinstaller
```

2. **Create spec file:**
```bash
pyinstaller --name face-detection app.py
```

3. **Build executable:**
```bash
pyinstaller face-detection.spec
```

**Note:** Camera access still requires proper permissions on the host system.

## 🌍 Cloud Deployment Options

### Option 1: Client-Side Detection
Modify the app to use browser-based face detection (MediaPipe, TensorFlow.js) instead of server-side OpenCV.

### Option 2: WebRTC Streaming
Stream video from client browser to server for processing.

### Option 3: Edge Computing
Deploy on edge devices (Raspberry Pi, Jetson Nano) with camera access.

## 📝 Environment Variables

Create a `.env` file (not committed to git):

```env
FLASK_ENV=production
PORT=8080
DEBUG=False
```

Load in `app.py`:
```python
from dotenv import load_dotenv
load_dotenv()
```

## 🔧 Troubleshooting Deployment

### Camera Not Accessible
- Check camera permissions
- Verify camera device path
- Test locally first

### Port Already in Use
- Change port in `app.py`
- Use environment variable: `PORT=3000 python3 app.py`

### Dependencies Issues
- Ensure all packages in `requirements.txt`
- Check Python version compatibility
- Use virtual environment

## 📚 Additional Resources

- [Flask Deployment Guide](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [Docker Documentation](https://docs.docker.com/)
- [Heroku Python Guide](https://devcenter.heroku.com/articles/getting-started-with-python)


