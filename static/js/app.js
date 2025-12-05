// Real-time Face Detection & Analysis - Frontend Application

let webcamStream = null;
let isProcessing = false;
let animationFrameId = null;
let fpsInterval = 1000 / 10; // Process at 10 FPS
let lastFrameTime = Date.now();
let frameCount = 0;
let fpsStartTime = Date.now();
let currentFPS = 0;

// DOM Elements
const webcamElement = document.getElementById('webcam');
const overlayCanvas = document.getElementById('overlay');
const overlayContext = overlayCanvas.getContext('2d');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const captureBtn = document.getElementById('captureBtn');
const faceCountElement = document.getElementById('faceCount');
const fpsElement = document.getElementById('fps');
const statusElement = document.getElementById('status');
const faceDetailsElement = document.getElementById('faceDetails');

// Button event listeners
startBtn.addEventListener('click', startCamera);
stopBtn.addEventListener('click', stopCamera);
captureBtn.addEventListener('click', captureFrame);

/**
 * Start the webcam and begin processing
 */
async function startCamera() {
    try {
        statusElement.textContent = 'Starting camera...';
        
        // Request camera access
        const constraints = {
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'user'
            },
            audio: false
        };
        
        webcamStream = await navigator.mediaDevices.getUserMedia(constraints);
        webcamElement.srcObject = webcamStream;
        
        // Wait for video to be ready
        await new Promise((resolve) => {
            webcamElement.onloadedmetadata = () => {
                webcamElement.play();
                resolve();
            };
        });
        
        // Set canvas size to match video
        overlayCanvas.width = webcamElement.videoWidth;
        overlayCanvas.height = webcamElement.videoHeight;
        
        // Update UI
        startBtn.disabled = true;
        stopBtn.disabled = false;
        captureBtn.disabled = false;
        statusElement.textContent = 'Camera active';
        
        // Start processing frames
        isProcessing = true;
        fpsStartTime = Date.now();
        processFrame();
        
        console.log('Camera started successfully');
    } catch (error) {
        console.error('Error starting camera:', error);
        statusElement.textContent = 'Camera access denied';
        alert('Could not access camera. Please ensure you have granted camera permissions.');
    }
}

/**
 * Stop the webcam and processing
 */
function stopCamera() {
    isProcessing = false;
    
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
    }
    
    if (webcamStream) {
        webcamStream.getTracks().forEach(track => track.stop());
        webcamStream = null;
    }
    
    webcamElement.srcObject = null;
    
    // Update UI
    startBtn.disabled = false;
    stopBtn.disabled = true;
    captureBtn.disabled = true;
    statusElement.textContent = 'Camera stopped';
    faceCountElement.textContent = '0';
    fpsElement.textContent = '0';
    faceDetailsElement.innerHTML = '<p class="no-faces">Camera stopped. Click "Start Camera" to begin again.</p>';
    
    console.log('Camera stopped');
}

/**
 * Process video frames and send to backend for analysis
 */
async function processFrame() {
    if (!isProcessing) {
        return;
    }
    
    const now = Date.now();
    const elapsed = now - lastFrameTime;
    
    // Throttle frame processing
    if (elapsed > fpsInterval) {
        lastFrameTime = now - (elapsed % fpsInterval);
        
        try {
            // Capture frame from video
            const canvas = document.createElement('canvas');
            canvas.width = webcamElement.videoWidth;
            canvas.height = webcamElement.videoHeight;
            const context = canvas.getContext('2d');
            context.drawImage(webcamElement, 0, 0, canvas.width, canvas.height);
            
            // Convert to base64
            const imageData = canvas.toDataURL('image/jpeg', 0.8);
            
            // Send to backend for analysis
            const response = await fetch('/analyze_frame', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ image: imageData })
            });
            
            if (response.ok) {
                const result = await response.json();
                
                if (result.success) {
                    // Update UI with analysis results
                    updateFaceData(result.face_data);
                    
                    // Calculate FPS
                    frameCount++;
                    const fpsElapsed = now - fpsStartTime;
                    if (fpsElapsed > 1000) {
                        currentFPS = Math.round((frameCount * 1000) / fpsElapsed);
                        fpsElement.textContent = currentFPS;
                        frameCount = 0;
                        fpsStartTime = now;
                    }
                }
            }
        } catch (error) {
            console.error('Error processing frame:', error);
        }
    }
    
    // Continue processing
    animationFrameId = requestAnimationFrame(processFrame);
}

/**
 * Update face analysis data in UI
 */
function updateFaceData(faceData) {
    faceCountElement.textContent = faceData.length;
    
    if (faceData.length === 0) {
        faceDetailsElement.innerHTML = '<p class="no-faces">No faces detected in frame.</p>';
        return;
    }
    
    let html = '';
    
    faceData.forEach((face, index) => {
        const blinkIndicator = face.blink_count > 0 ? 
            `<span class="blink-alert">👁️ Blinked!</span>` : '';
        
        html += `
            <div class="face-card">
                <h4>Face ${face.face_id} ${blinkIndicator}</h4>
                <div class="face-detail">
                    <span class="face-detail-label">Expression:</span>
                    <span class="face-detail-value">${face.expression}</span>
                </div>
                <div class="face-detail">
                    <span class="face-detail-label">Blink Count:</span>
                    <span class="face-detail-value">${face.blink_count}</span>
                </div>
                <div class="face-detail">
                    <span class="face-detail-label">Head Yaw:</span>
                    <span class="face-detail-value">${face.head_pose.yaw.toFixed(1)}°</span>
                </div>
                <div class="face-detail">
                    <span class="face-detail-label">Head Pitch:</span>
                    <span class="face-detail-value">${face.head_pose.pitch.toFixed(1)}°</span>
                </div>
                <div class="face-detail">
                    <span class="face-detail-label">Head Roll:</span>
                    <span class="face-detail-value">${face.head_pose.roll.toFixed(1)}°</span>
                </div>
                <div class="face-detail">
                    <span class="face-detail-label">Position:</span>
                    <span class="face-detail-value">
                        (${face.bounding_box.x_min}, ${face.bounding_box.y_min})
                    </span>
                </div>
            </div>
        `;
    });
    
    faceDetailsElement.innerHTML = html;
}

/**
 * Capture current frame as image
 */
function captureFrame() {
    const canvas = document.createElement('canvas');
    canvas.width = webcamElement.videoWidth;
    canvas.height = webcamElement.videoHeight;
    const context = canvas.getContext('2d');
    context.drawImage(webcamElement, 0, 0, canvas.width, canvas.height);
    
    // Download image
    const link = document.createElement('a');
    link.download = `face-capture-${Date.now()}.jpg`;
    link.href = canvas.toDataURL('image/jpeg');
    link.click();
    
    // Visual feedback
    const originalStatus = statusElement.textContent;
    statusElement.textContent = 'Frame captured! 📸';
    setTimeout(() => {
        statusElement.textContent = originalStatus;
    }, 2000);
}

// Initialize - check for camera support
if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    statusElement.textContent = 'Camera not supported';
    startBtn.disabled = true;
    alert('Your browser does not support camera access. Please use a modern browser like Chrome, Firefox, or Safari.');
} else {
    console.log('Camera API supported');
    statusElement.textContent = 'Ready - Click "Start Camera"';
}

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (webcamStream) {
        stopCamera();
    }
});
