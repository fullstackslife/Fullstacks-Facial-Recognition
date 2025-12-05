# 🌐 Domain Setup: fullstacks.click

This guide will help you configure `fullstacks.click` for your Face Detection & Analysis System deployment.

## Domain Information

- **Domain**: `fullstacks.click`
- **Status**: Active
- **Expiration**: August 12, 2026
- **Privacy Protection**: ON

## Setup Options

### Option 1: Single Domain Setup (Recommended)

Use `fullstacks.click` for the frontend (Vercel) and keep Railway's default domain for the backend API.

**Frontend (Vercel)**: `https://fullstacks.click`  
**Backend (Railway)**: `https://web-production-7c047.up.railway.app` (or Railway's generated domain)

### Option 2: Subdomain Setup

Use subdomains to separate frontend and backend:

**Frontend (Vercel)**: `https://fullstacks.click`  
**Backend (Railway)**: `https://api.fullstacks.click`

## Step-by-Step Setup

### For Vercel (Frontend) - fullstacks.click

1. **Go to Vercel Dashboard**
   - Navigate to your project: `fullstacks-facial-recognition`
   - Go to **Settings** → **Domains**

2. **Add Domain**
   - Enter: `fullstacks.click`
   - Click **Add**

3. **Configure DNS**
   Vercel will show you DNS records to add. You'll need to add one of these:

   **Option A: Root Domain (fullstacks.click)**
   ```
   Type: A
   Name: @
   Value: 76.76.21.21
   ```

   **Option B: CNAME (if supported by your registrar)**
   ```
   Type: CNAME
   Name: @
   Value: cname.vercel-dns.com
   ```

4. **Add DNS Record**
   - Go to your domain registrar (where you manage fullstacks.click)
   - Add the DNS record shown by Vercel
   - Wait for DNS propagation (5-30 minutes)

5. **Verify**
   - Vercel will automatically verify the domain
   - Once verified, SSL certificate will be issued automatically
   - Your site will be live at `https://fullstacks.click`

### For Railway (Backend) - Optional Subdomain

If you want to use `api.fullstacks.click` for the backend:

1. **Go to Railway Dashboard**
   - Navigate to your project
   - Go to **Settings** → **Domains**

2. **Add Custom Domain**
   - Enter: `api.fullstacks.click`
   - Railway will provide DNS records

3. **Add DNS Record**
   - Go to your domain registrar
   - Add the CNAME record provided by Railway:
   ```
   Type: CNAME
   Name: api
   Value: [Railway-provided-value]
   ```

4. **Update CORS in app.py** (if using subdomain)
   ```python
   CORS(app, resources={r"/*": {"origins": [
       "https://fullstacks.click",
       "https://www.fullstacks.click",
       "http://localhost:8080"
   ]}})
   ```

## DNS Configuration Summary

In your domain registrar, you'll need to add:

### For Vercel (fullstacks.click):
```
Type: A or CNAME
Name: @ (or leave blank for root)
Value: [Vercel-provided-value]
```

### For Railway (api.fullstacks.click) - Optional:
```
Type: CNAME
Name: api
Value: [Railway-provided-value]
```

## Testing

After DNS propagation:

1. **Test Frontend**
   - Visit: `https://fullstacks.click`
   - Should see the face detection interface

2. **Test Backend** (if using subdomain)
   - Visit: `https://api.fullstacks.click`
   - Should see the Flask app response

3. **Test Integration**
   - Start face detection on `fullstacks.click`
   - Verify it connects to the backend API

## Troubleshooting

### DNS Not Propagating
- Wait 24-48 hours for full propagation
- Use `dig fullstacks.click` or `nslookup fullstacks.click` to check
- Clear your DNS cache: `sudo dscacheutil -flushcache` (macOS)

### SSL Certificate Issues
- Vercel and Railway automatically provision SSL certificates
- Wait 5-10 minutes after DNS verification
- Check certificate status in dashboard

### CORS Errors
- Update `app.py` CORS configuration with your new domain
- Ensure both frontend and backend domains are in the allowed origins list

## Current Deployment URLs

- **Vercel Frontend**: https://fullstacks-facial-recognition.vercel.app/
- **Railway Backend**: https://web-production-7c047.up.railway.app/
- **New Domain**: https://fullstacks.click (after setup)

## Next Steps

1. ✅ Add domain to Vercel
2. ✅ Configure DNS records
3. ✅ Wait for DNS propagation
4. ✅ Verify SSL certificate
5. ✅ Test the deployment
6. ✅ (Optional) Set up backend subdomain

Once complete, your face detection app will be live at `https://fullstacks.click`! 🎉

