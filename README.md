Autonomous Lab Teaching Assistant
📋 Project Overview
Autonomous Lab Teaching Assistant (ALTA) is an intelligent web-based platform that provides automated code debugging and manual solution comparison for programming education. It helps students debug their code with AI-powered hints while allowing instructors to upload and compare against reference solutions.
✨ Key Features
🧠 Intelligent Debugging: AI-powered hints based on error types and code analysis
📝 Manual Solution Comparison: Compare student code with reference implementations
📤 User Upload System: Instructors can upload custom manual solutions
🌐 Multi-language Support: Python, JavaScript, and Java execution
📊 Real-time Analytics: Track common errors and success rates
🎨 Modern UI: Responsive design with visual feedback and notifications
📦 Prerequisites
Python 3.8 or higher
Node.js (for JavaScript execution)
Modern web browser (Chrome, Firefox, Safari)
2-Minute Setup
Step 1: Create Project Structure
Create project folder
mkdir alta-project
cd alta-project
Create directories
mkdir backend frontend

Step 2: Set Up Backend
cd backend
Create main.py with the provided Python code
(Paste the FastAPI code into main.py)
Create virtual environment
python -m venv venv
Activate virtual environment
On Windows: venv\Scripts\activate
On Mac/Linux: source venv/bin/activate
Install dependencies
pip install fastapi uvicorn pydantic numpy
Start the backend server
python main.py
Expected Output:
text
🚀 Autonomous Lab TA Backend with Manual Upload
📊 Database initialized with sample data
📝 Manual upload and comparison enabled
📤 User manuals storage ready
🌐 API ready at http://localhost:8000
📚 Documentation: http://localhost:8000/docs
Step 3: Set Up Frontend
bash
cd ../frontend
Create index.html with the provided HTML code
(Paste the HTML code into index.html)
Open in browser
Option 1: Double-click index.html
Option 2: Use Python HTTP server:
python -m http.server 3000

🌐 Access the Application
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs
Health Check: http://localhost:8000/health
Frontend UI: http://localhost:3000
Or open index.html directly in browser
