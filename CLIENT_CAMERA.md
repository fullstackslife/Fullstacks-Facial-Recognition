# Client-Side Camera Implementation

This document explains the client-side camera implementation that allows the application to work in cloud environments (Railway, Vercel) by using the browser's camera instead of server-side camera access.

## Architecture Changes

### Before (Server-Side Camera)
- Flask backend accessed camera directly via OpenCV
- Video streamed from server to browser
- Required physical camera access on server
- Not suitable for cloud deployment

### After (Client-Side Camera)
- Browser accesses user's camera via MediaDevices API
- Frames sent from browser to Flask backend
- Backend processes frames and returns results
- Works in any cloud environment

## How It Works

### 1. Browser Camera Access
```javascript
// Request camera access
const stream = await navigator.mediaDevices.getUserMedia({
    video: { deviceId: selectedCameraId }
});
```

### 2. Frame Capture & Transmission
```javascript
// Capture frame from video element
ctx.drawImage(videoElement, 0, 0);
const frameBase64 = canvas.toDataURL('image/jpeg');

// Send to backend
fetch('/api/process_frame', {
    method: 'POST',
    body: JSON.stringify({ frame: frameBase64, session_id: sessionId })
});
```

### 3. Backend Processing
```python
# Receive frame
frame = base64_to_image(request.json['frame'])

# Process with OpenCV
analysis = analyzer.analyze_faces(frame)
processed_frame = draw_enhanced_detections(frame, analysis)

# Return processed frame and analysis
return jsonify({
    'processed_frame': image_to_base64(processed_frame),
    'analysis': analysis
})
```

### 4. Display Results
```javascript
// Display processed frame with overlays
const img = new Image();
img.src = 'data:image/jpeg;base64,' + data.processed_frame;
processedCanvas.drawImage(img, 0, 0);
```

## Key Features

### ✅ Cloud-Ready
- Works on Railway, Vercel, Heroku, etc.
- No server-side camera required
- Uses user's device camera

### ✅ Privacy-Friendly
- Camera access requires user permission
- Processing happens on backend (optional)
- No video stored permanently

### ✅ Multi-Camera Support
- Select from available cameras
- Dual camera mode supported
- Cross-reference validation

### ✅ Real-Time Processing
- ~30 FPS frame processing
- Low latency (<100ms)
- Smooth video display

## API Endpoints

### POST `/api/process_frame`
Process a single frame from the client.

**Request:**
```json
{
    "frame": "data:image/jpeg;base64,...",
    "session_id": "session_123"
}
```

**Response:**
```json
{
    "status": "success",
    "processed_frame": "base64_encoded_image",
    "analysis": { ... }
}
```

### GET `/api/facial_features?session_id=xxx`
Get detailed facial analysis for a session.

**Response:**
```json
{
    "status": "success",
    "faces": [...],
    "count": 1,
    "unique_faces": 1,
    ...
}
```

### POST `/api/reset_stats`
Reset session statistics.

**Request:**
```json
{
    "session_id": "session_123"
}
```

## Browser Compatibility

### Required APIs
- **MediaDevices API** - Camera access
- **Canvas API** - Frame capture
- **Fetch API** - Backend communication

### Supported Browsers
- ✅ Chrome/Edge (Chromium) 60+
- ✅ Firefox 55+
- ✅ Safari 11+
- ✅ Opera 47+

### HTTPS Requirement
Camera access requires HTTPS (or localhost) in most browsers.

## Performance Considerations

### Frame Rate
- Default: ~30 FPS
- Adjustable via `frameInterval` in JavaScript
- Higher FPS = more backend load

### Image Quality
- JPEG quality: 80% (adjustable)
- Resolution: 1280x720 (ideal)
- Compression reduces bandwidth

### Backend Load
- Each frame = 1 API call
- ~30 requests/second per user
- Consider rate limiting for production

## Security Considerations

### CORS
CORS enabled for all origins. For production, restrict to your domain:
```python
CORS(app, resources={r"/*": {"origins": ["https://yourdomain.com"]}})
```

### Rate Limiting
Consider adding rate limiting:
```python
from flask_limiter import Limiter
limiter = Limiter(app, key_func=get_remote_address)

@app.route('/api/process_frame', methods=['POST'])
@limiter.limit("30 per second")
def process_frame():
    ...
```

### Input Validation
- Validate base64 image data
- Check image size limits
- Sanitize session IDs

## Deployment

### Railway (Backend)
1. Deploy Flask app to Railway
2. Set environment variables
3. Backend ready to process frames

### Vercel (Frontend)
1. Deploy static files to Vercel
2. Configure API URL to Railway backend
3. Set CORS in backend

### Local Development
```bash
# Backend
python3 app.py

# Frontend (if separated)
# Serve static files or use Vercel dev
```

## Troubleshooting

### Camera Not Accessing
- Check browser permissions
- Ensure HTTPS (or localhost)
- Verify camera not in use by another app

### Frames Not Processing
- Check browser console for errors
- Verify backend is running
- Check network tab for API calls

### Poor Performance
- Reduce frame rate
- Lower image quality
- Optimize backend processing
- Use Web Workers for frame capture

## Future Enhancements

### WebRTC Streaming
- Stream video directly to backend
- Lower latency
- Better quality

### WebAssembly
- Client-side face detection
- Reduce backend load
- Faster processing

### Web Workers
- Offload frame capture
- Better UI responsiveness
- Parallel processing

## Migration Notes

### From Server-Side to Client-Side

1. **Remove server camera code:**
   - `get_camera()` function
   - `generate_frames()` function
   - `/video_feed` endpoint (optional)

2. **Add client-side code:**
   - MediaDevices API access
   - Frame capture and transmission
   - Processed frame display

3. **Update endpoints:**
   - `/api/process_frame` - New endpoint
   - `/api/facial_features` - Updated for sessions
   - `/api/reset_stats` - Updated for sessions

4. **Update frontend:**
   - Replace `<img>` with `<video>` and `<canvas>`
   - Add frame processing loop
   - Update camera selection

## Testing

### Local Testing
```bash
# Start backend
python3 app.py

# Open browser
http://localhost:8080

# Grant camera permission
# Start detection
```

### Cloud Testing
1. Deploy to Railway/Vercel
2. Access deployed URL
3. Test camera access
4. Verify frame processing

## Support

For issues or questions:
- Check browser console for errors
- Review backend logs
- Verify API endpoints
- Test with different browsers

