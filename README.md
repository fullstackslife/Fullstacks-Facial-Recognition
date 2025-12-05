# Fullstacks-Facial-Recognition 🎭

A real-time face detection and analysis web application built with Flask, OpenCV, and MediaPipe. Features multi-face tracking, expression detection, blink counting, and head pose estimation.

![Python](https://img.shields.io/badge/Python-3.7%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8.1-red)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.7-orange)

## ✨ Features

- **Multi-Face Tracking**: Detect and track up to 5 faces simultaneously
- **Expression Detection**: Identify facial expressions (neutral, smiling, surprised)
- **Blink Detection**: Count and detect eye blinks in real-time
- **Head Pose Estimation**: Calculate yaw, pitch, and roll angles
- **Face Mesh Visualization**: Display detailed facial landmarks
- **Browser Camera**: Direct browser camera access without server-side streaming
- **Real-time Processing**: Process video frames at up to 10 FPS
- **Responsive UI**: Modern, mobile-friendly interface

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Webcam/Camera
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/fullstackslife/Fullstacks-Facial-Recognition.git
   cd Fullstacks-Facial-Recognition
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:5000`

## 🎯 Usage

1. Click the **"Start Camera"** button to access your webcam
2. Allow camera permissions when prompted by your browser
3. Position your face(s) within the camera view
4. Watch real-time analysis appear in the information panel:
   - Face count and detection status
   - Individual face analysis with expressions
   - Blink counting for each detected face
   - Head pose angles (yaw, pitch, roll)
5. Use the **"Capture Frame"** button to save a snapshot
6. Click **"Stop Camera"** when finished

## 🏗️ Architecture

### Backend (Flask + OpenCV + MediaPipe)
- **app.py**: Main Flask application with face analysis endpoints
- **FaceAnalyzer**: Class handling detection logic
  - Eye Aspect Ratio (EAR) calculation for blink detection
  - Head pose estimation using facial landmarks
  - Expression detection based on facial geometry

### Frontend (HTML + CSS + JavaScript)
- **index.html**: Main application interface
- **style.css**: Responsive styling with gradient backgrounds
- **app.js**: Camera handling and real-time frame processing

### API Endpoints

- `GET /`: Main application page
- `POST /analyze_frame`: Analyze a single frame (JSON)
- `GET /health`: Health check endpoint

## 📦 Deployment

### Railway

1. Push your code to GitHub
2. Connect your repository to Railway
3. Railway will automatically detect Python and deploy using `Procfile`

### Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. Run: `vercel`
3. Follow the prompts to deploy

### Environment Variables

No environment variables required for basic operation.

## 🛠️ Technologies

- **Backend**: Flask 2.3.3
- **Computer Vision**: OpenCV 4.8.1
- **Face Analysis**: MediaPipe 0.10.7
- **Numerical Computing**: NumPy 1.24.3
- **Production Server**: Gunicorn 21.2.0

## 📊 Performance

- Processes frames at approximately 10 FPS
- Supports up to 5 simultaneous faces
- Low latency (<100ms) frame analysis
- Optimized for real-time performance

## 🔒 Privacy

- All processing happens locally in your browser and server
- No video data is stored or transmitted to third parties
- Camera access requires explicit user permission
- Frames are processed in memory only

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- [MediaPipe](https://google.github.io/mediapipe/) for facial landmark detection
- [OpenCV](https://opencv.org/) for computer vision capabilities
- [Flask](https://flask.palletsprojects.com/) for the web framework

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

Built with ❤️ by Fullstacks Life