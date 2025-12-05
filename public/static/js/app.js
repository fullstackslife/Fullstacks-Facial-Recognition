// Face Detection Web Interface - Client-Side Camera
class FaceDetectionApp {
    constructor() {
        this.isRunning = false;
        this.videoElement = null;
        this.canvas = null;
        this.ctx = null;
        this.processedCanvas = null;
        this.processedCtx = null;
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.cameraSelect = document.getElementById('cameraSelect');
        this.faceCountEl = document.getElementById('faceCount');
        this.uniqueFacesEl = document.getElementById('uniqueFaces');
        this.maxFacesEl = document.getElementById('maxFaces');
        this.totalDetectionsEl = document.getElementById('totalDetections');
        this.sessionDurationEl = document.getElementById('sessionDuration');
        this.avgFacesPerSecEl = document.getElementById('avgFacesPerSec');
        this.statusText = document.getElementById('statusText');
        this.statusDot = document.querySelector('.status-dot');
        this.connectionStatus = document.getElementById('connectionStatus');
        this.resetStatsBtn = document.getElementById('resetStatsBtn');
        this.dualCameraMode = document.getElementById('dualCameraMode');
        this.camera2Select = document.getElementById('camera2Select');
        this.crossReferencePanel = document.getElementById('crossReferencePanel');
        this.validationStatus = document.getElementById('validationStatus');
        this.validationConfidence = document.getElementById('validationConfidence');
        
        // API base URL - use Railway backend if available, otherwise use current origin
        this.apiBaseUrl = window.API_BASE_URL || '';
        
        this.selectedCameraId = null;
        this.selectedCamera2Id = null;
        this.availableCameras = [];
        this.stream = null;
        this.stream2 = null;
        this.sessionId = 'session_' + Date.now();
        this.sessionId2 = 'session2_' + Date.now();
        this.statsInterval = null;
        this.frameInterval = null;
        this.crossRefInterval = null;
        
        this.init();
    }

    async init() {
        // Create video element and canvas for display
        this.setupVideoElements();
        
        // Load available cameras
        await this.loadCameras();
        
        // Set up event listeners
        this.startBtn.addEventListener('click', () => this.start());
        this.stopBtn.addEventListener('click', () => this.stop());
        this.cameraSelect.addEventListener('change', (e) => {
            this.selectedCameraId = e.target.value;
            if (this.isRunning) {
                this.stop();
                setTimeout(() => this.start(), 500);
            }
        });
        
        // Set up reset stats button
        this.resetStatsBtn.addEventListener('click', () => this.resetStatistics());
        
        // Set up dual camera mode
        this.dualCameraMode.addEventListener('change', (e) => {
            this.camera2Select.disabled = !e.target.checked;
            if (!e.target.checked) {
                this.selectedCamera2Id = null;
                this.crossReferencePanel.style.display = 'none';
                this.stopCrossReference();
                if (this.stream2) {
                    this.stream2.getTracks().forEach(track => track.stop());
                    this.stream2 = null;
                }
            } else {
                this.populateCamera2Select();
            }
        });
        
        this.camera2Select.addEventListener('change', (e) => {
            this.selectedCamera2Id = e.target.value;
        });
        
        // Initial status
        this.updateStatus('Ready', false);
    }
    
    setupVideoElements() {
        // Get or create video element
        const videoContainer = document.querySelector('.video-wrapper');
        if (!videoContainer) return;
        
        // Remove old video feed if exists
        const oldVideo = document.getElementById('videoFeed');
        if (oldVideo) oldVideo.remove();
        
        // Create video element for camera stream
        this.videoElement = document.createElement('video');
        this.videoElement.id = 'videoFeed';
        this.videoElement.autoplay = true;
        this.videoElement.playsInline = true;
        this.videoElement.style.width = '100%';
        this.videoElement.style.height = '100%';
        this.videoElement.style.objectFit = 'cover';
        
        // Create canvas for processed frames
        this.canvas = document.createElement('canvas');
        this.canvas.style.display = 'none';
        this.processedCanvas = document.createElement('canvas');
        this.processedCanvas.id = 'processedCanvas';
        this.processedCanvas.style.width = '100%';
        this.processedCanvas.style.height = '100%';
        this.processedCanvas.style.position = 'absolute';
        this.processedCanvas.style.top = '0';
        this.processedCanvas.style.left = '0';
        this.processedCanvas.style.pointerEvents = 'none';
        
        this.ctx = this.canvas.getContext('2d');
        this.processedCtx = this.processedCanvas.getContext('2d');
        
        // Add to container
        videoContainer.appendChild(this.videoElement);
        videoContainer.appendChild(this.processedCanvas);
    }
    
    async loadCameras() {
        try {
            // Get available cameras from browser
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(device => device.kind === 'videoinput');
            
            this.availableCameras = videoDevices.map((device, index) => ({
                deviceId: device.deviceId,
                label: device.label || `Camera ${index + 1}`,
                index: index
            }));
            
            this.populateCameraSelect(this.availableCameras);
        } catch (error) {
            console.error('Error loading cameras:', error);
            this.cameraSelect.innerHTML = '<option value="">Error loading cameras</option>';
        }
    }
    
    populateCameraSelect(cameras) {
        this.cameraSelect.innerHTML = '';
        
        if (cameras.length === 0) {
            this.cameraSelect.innerHTML = '<option value="">No cameras found</option>';
            return;
        }
        
        cameras.forEach((cam, index) => {
            const option = document.createElement('option');
            option.value = cam.deviceId;
            option.textContent = `📹 ${cam.label}`;
            if (index === 0) {
                option.selected = true;
                this.selectedCameraId = cam.deviceId;
            }
            this.cameraSelect.appendChild(option);
        });
        
        this.populateCamera2Select();
    }
    
    populateCamera2Select() {
        if (!this.availableCameras || this.availableCameras.length === 0) return;
        
        this.camera2Select.innerHTML = '<option value="">Select 2nd Camera...</option>';
        
        this.availableCameras.forEach(cam => {
            if (cam.deviceId === this.selectedCameraId) return;
            
            const option = document.createElement('option');
            option.value = cam.deviceId;
            option.textContent = `📹 ${cam.label}`;
            this.camera2Select.appendChild(option);
        });
    }

    async start() {
        if (this.isRunning) return;
        
        if (!this.selectedCameraId) {
            alert('Please select a camera first');
            return;
        }
        
        try {
            // Request camera access
            const constraints = {
                video: {
                    deviceId: { exact: this.selectedCameraId },
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            };
            
            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.videoElement.srcObject = this.stream;
            
            // Wait for video to be ready
            await new Promise((resolve) => {
                this.videoElement.onloadedmetadata = () => {
                    this.canvas.width = this.videoElement.videoWidth;
                    this.canvas.height = this.videoElement.videoHeight;
                    this.processedCanvas.width = this.videoElement.videoWidth;
                    this.processedCanvas.height = this.videoElement.videoHeight;
                    resolve();
                };
            });
            
            // Start dual camera if enabled
            if (this.dualCameraMode.checked && this.selectedCamera2Id) {
                await this.startSecondCamera();
            }
            
            this.isRunning = true;
            this.startBtn.disabled = true;
            this.stopBtn.disabled = false;
            this.cameraSelect.disabled = true;
            
            this.updateStatus('Detecting...', true);
            this.connectionStatus.textContent = 'Active';
            
            // Start processing frames
            this.startFrameProcessing();
            
            // Start statistics polling
            this.startStatisticsPolling();
            
            if (this.dualCameraMode.checked) {
                this.startCrossReference();
            }
            
        } catch (error) {
            console.error('Error starting camera:', error);
            alert('Error accessing camera: ' + error.message);
            this.updateStatus('Camera Error', false);
        }
    }
    
    async startSecondCamera() {
        try {
            const constraints2 = {
                video: {
                    deviceId: { exact: this.selectedCamera2Id },
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            };
            
            this.stream2 = await navigator.mediaDevices.getUserMedia(constraints2);
            // You can add a second video element if needed
        } catch (error) {
            console.error('Error starting second camera:', error);
        }
    }
    
    startFrameProcessing() {
        // Process frames at ~30 FPS
        this.frameInterval = setInterval(() => {
            this.processFrame();
        }, 33); // ~30 FPS
    }
    
    async processFrame() {
        if (!this.videoElement || !this.isRunning) return;
        
        try {
            // Draw current frame to canvas
            this.ctx.drawImage(this.videoElement, 0, 0);
            
            // Convert canvas to base64
            const frameBase64 = this.canvas.toDataURL('image/jpeg', 0.8);
            
            // Send to backend for processing
            const apiUrl = this.apiBaseUrl ? `${this.apiBaseUrl}/api/process_frame` : '/api/process_frame';
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    frame: frameBase64,
                    session_id: this.sessionId
                })
            });
            
            const data = await response.json();
            
            if (data.status === 'success' && data.processed_frame) {
                // Display processed frame
                const img = new Image();
                img.onload = () => {
                    this.processedCtx.clearRect(0, 0, this.processedCanvas.width, this.processedCanvas.height);
                    this.processedCtx.drawImage(img, 0, 0);
                };
                img.src = 'data:image/jpeg;base64,' + data.processed_frame;
            }
        } catch (error) {
            console.error('Error processing frame:', error);
        }
    }
    
    startStatisticsPolling() {
        this.statsInterval = setInterval(async () => {
            try {
                const apiUrl = this.apiBaseUrl ? `${this.apiBaseUrl}/api/facial_features?session_id=${this.sessionId}` : `/api/facial_features?session_id=${this.sessionId}`;
                const response = await fetch(apiUrl);
                const data = await response.json();
                
                if (data.status === 'success') {
                    this.faceCountEl.textContent = data.count || 0;
                    this.uniqueFacesEl.textContent = data.unique_faces || 0;
                    this.maxFacesEl.textContent = data.max_faces || 0;
                    this.totalDetectionsEl.textContent = data.total_detections || 0;
                    this.sessionDurationEl.textContent = this.formatDuration(data.session_duration || 0);
                    this.avgFacesPerSecEl.textContent = (data.avg_faces_per_sec || 0).toFixed(2);
                    
                    // Update facial features display
                    this.displayFacialFeatures(data.faces || []);
                }
            } catch (error) {
                console.error('Error fetching statistics:', error);
            }
        }, 500); // Update every 500ms
    }
    
    formatDuration(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    displayFacialFeatures(faces) {
        const featuresContainer = document.getElementById('facialFeatures');
        if (!featuresContainer) return;
        
        if (faces.length === 0) {
            featuresContainer.innerHTML = `
                <div class="feature-placeholder-compact">
                    <p>No faces detected</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        faces.forEach((face, index) => {
            const blink = face.blink || {};
            const eyes = face.individual_eyes || {};
            const headPose = face.full_head_pose || face.head_pose || {};
            const quality = face.quality || {};
            
            html += `
                <div class="feature-card-compact">
                    <div class="feature-header-compact">
                        <span>Face ID: ${face.id}</span>
                        <span class="confidence-badge">${(face.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <div class="feature-grid-compact">
                        <div class="feature-item-compact">
                            <span class="feature-label">Age:</span>
                            <span class="feature-value">${face.age || 'N/A'}</span>
                        </div>
                        <div class="feature-item-compact">
                            <span class="feature-label">Gender:</span>
                            <span class="feature-value">${face.gender || 'N/A'}</span>
                        </div>
                        <div class="feature-item-compact">
                            <span class="feature-label">Expression:</span>
                            <span class="feature-value">${face.expression || 'neutral'}</span>
                        </div>
                        <div class="feature-item-compact">
                            <span class="feature-label">Blinks:</span>
                            <span class="feature-value">${blink.count || 0}</span>
                        </div>
                        <div class="feature-item-compact">
                            <span class="feature-label">Head Yaw:</span>
                            <span class="feature-value">${headPose.yaw ? headPose.yaw.toFixed(1) : '0'}°</span>
                        </div>
                        <div class="feature-item-compact">
                            <span class="feature-label">Head Pitch:</span>
                            <span class="feature-value">${headPose.pitch ? headPose.pitch.toFixed(1) : '0'}°</span>
                        </div>
                        <div class="feature-item-compact">
                            <span class="feature-label">Quality:</span>
                            <span class="feature-value">${quality.sharpness ? quality.sharpness.toFixed(2) : 'N/A'}</span>
                        </div>
                        <div class="feature-item-compact">
                            <span class="feature-label">Eyes Open:</span>
                            <span class="feature-value">${eyes.left_eye?.is_open && eyes.right_eye?.is_open ? 'Yes' : 'No'}</span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        featuresContainer.innerHTML = html;
    }

    stop() {
        if (!this.isRunning) return;
        
        this.isRunning = false;
        this.startBtn.disabled = false;
        this.stopBtn.disabled = true;
        this.cameraSelect.disabled = false;
        
        // Stop frame processing
        if (this.frameInterval) {
            clearInterval(this.frameInterval);
            this.frameInterval = null;
        }
        
        // Stop statistics polling
        if (this.statsInterval) {
            clearInterval(this.statsInterval);
            this.statsInterval = null;
        }
        
        // Stop camera streams
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        if (this.stream2) {
            this.stream2.getTracks().forEach(track => track.stop());
            this.stream2 = null;
        }
        
        // Clear video
        if (this.videoElement) {
            this.videoElement.srcObject = null;
        }
        
        if (this.processedCtx) {
            this.processedCtx.clearRect(0, 0, this.processedCanvas.width, this.processedCanvas.height);
        }
        
        this.updateStatus('Stopped', false);
        this.connectionStatus.textContent = 'Inactive';
        
        this.stopCrossReference();
    }
    
    updateStatus(text, isActive) {
        if (this.statusText) this.statusText.textContent = text;
        if (this.statusDot) {
            this.statusDot.className = 'status-dot ' + (isActive ? 'active' : '');
        }
    }
    
    async resetStatistics() {
        try {
            const apiUrl = this.apiBaseUrl ? `${this.apiBaseUrl}/api/reset_stats` : '/api/reset_stats';
            await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: this.sessionId
                })
            });
            
            // Reset UI
            this.faceCountEl.textContent = '0';
            this.uniqueFacesEl.textContent = '0';
            this.maxFacesEl.textContent = '0';
            this.totalDetectionsEl.textContent = '0';
            this.sessionDurationEl.textContent = '0:00';
            this.avgFacesPerSecEl.textContent = '0.00';
        } catch (error) {
            console.error('Error resetting statistics:', error);
        }
    }
    
    startCrossReference() {
        this.crossRefInterval = setInterval(async () => {
            try {
                const apiUrl = this.apiBaseUrl ? `${this.apiBaseUrl}/api/cross_reference` : '/api/cross_reference';
                const response = await fetch(apiUrl);
                const data = await response.json();
                
                if (data.status === 'success' && data.summary) {
                    this.crossReferencePanel.style.display = 'block';
                    this.validationStatus.textContent = data.summary.overall_match ? 'Match' : 'Mismatch';
                    this.validationConfidence.textContent = `${(data.summary.confidence * 100).toFixed(1)}%`;
                }
            } catch (error) {
                console.error('Error fetching cross-reference:', error);
            }
        }, 2000);
    }
    
    stopCrossReference() {
        if (this.crossRefInterval) {
            clearInterval(this.crossRefInterval);
            this.crossRefInterval = null;
        }
        if (this.crossReferencePanel) {
            this.crossReferencePanel.style.display = 'none';
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new FaceDetectionApp();
});
