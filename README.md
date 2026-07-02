# 🌱 GreenScape AI — 2D-to-3D Generative AI Pipeline

GreenScape AI is an automated generative AI pipeline that transforms 2D images of abandoned or empty lots into fully fleshed-out 3D Permaculture designs with a focus on zero waste and low-cost execution.

## 🏗️ Architecture & Tech Stack

This project utilizes a modern decoupled architecture:
- **Backend Orchestrator**: FastAPI (Python)
- **AI Reasoning**: Google Gemini 3 Flash Preview (Metadata & Blueprint extraction)
- **Vision Engine**: Grounding DINO (Target localization & Spatial boundaries)
- **Depth Engine**: Depth-Anything-V2 (Monocular depth estimation & 3D Spatial coordinates)
- **3D Generative AI**: SD-XL 1.0 + Stable Fast 3D (SF3D) deployed on Serverless GPUs (Modal.com)
- **Database & Storage**: Supabase (PostgreSQL for metadata, Object Storage for raw images & .glb models)
- **Frontend**: React + Vite + React-Three-Fiber (3D model rendering)

## 🛠️ Prerequisites

Before you begin, ensure you have:
1. **Python 3.10+** installed
2. **Node.js 18+** installed
3. A [Supabase](https://supabase.com/) account (Project URL and Anon Key)
4. A [Google AI Studio](https://aistudio.google.com/) account (Gemini API Key)
5. A [Modal.com](https://modal.com/) account (for running SD-XL and SF3D serverless)
6. A [HuggingFace](https://huggingface.co/) account with an API token (for downloading SF3D weights)

## ⚙️ Environment Setup

Create a `.env` file in the `backend/` directory with the following variables:

```env
# Google Gemini API
GEMINI_API_KEY="your_google_gemini_api_key_here"

# Supabase Configurations
SUPABASE_URL="https://your-project-id.supabase.co"
SUPABASE_KEY="your_supabase_anon_key_here"
SUPABASE_BUCKET_RAW="raw_images"
SUPABASE_BUCKET_GLB="glb_models"

# HuggingFace Token (For Modal to download models)
HF_API_TOKEN="your_huggingface_read_token_here"
```

## 🚀 Installation & Running

### 1. Setup Backend (FastAPI + Modal)

Navigate to the `backend/` directory and set up a virtual environment:

```bash
cd backend
python -m venv green_venv
# Activate virtual environment
# Windows:
.\green_venv\Scripts\activate
# macOS/Linux:
source green_venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

**Deploy AI Models to Modal:**
To use the 3D generation pipeline, you must deploy the functions to your Modal account. First, authenticate with Modal:
```bash
modal setup
```
Then deploy the two apps (SD-XL and SF3D):
```bash
modal deploy services/modal_sd_xl.py
modal deploy services/modal_sf3d.py
```

**Run the Backend Server:**
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
*(Note: Avoid using `--reload` in production to prevent event-loop deadlocks caused by heavy CUDA models).*

### 2. Setup Frontend (React)

Open a new terminal, navigate to the `frontend/` directory:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`. Upload an image of an empty lot or room to watch the pipeline transform it into a 3D model!

## 🧪 End-to-End Testing (Dry Run)

If you wish to test the orchestration pipeline without expending Modal serverless credits, you can run a dry run test. This utilizes a set of stock `.glb` files.

Ensure your backend server is running, then execute:
```bash
cd backend
python test_e2e.py
```
This script uploads a dummy image, polls the task status every 3 seconds, and retrieves the final processed JSON output.

---
*Built for the ORCA Green Innovation Hackathon.*