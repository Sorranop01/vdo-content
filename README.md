# VDO Content - AI Content Pipeline

🎬 เครื่องมือสร้าง Content ที่เสียงพากย์และวีดีโอสอดคล้องกัน

## ✨ Features

- ✅ Gen บทพากย์ภาษาไทยด้วย DeepSeek AI
- ✅ แบ่งฉากอัตโนมัติ (≤8 วินาที/ฉาก ตาม Veo 3)
- ✅ Gen Veo 3 Prompt ภาษาอังกฤษที่ตรงกับบทพากย์
- ✅ Streamlit Dashboard สำหรับจัดการ
- ✅ Copy Prompt พร้อมใช้งาน

---

## 📁 Project Structure (NEW - Restructured)

```
vdo-content/
├── src/                          # Main source code
│   ├── frontend/                 # Streamlit UI
│   │   ├── app.py                # Main entry point
│   │   ├── pages/                # Page modules (TODO)
│   │   ├── components/           # Reusable UI components
│   │   ├── styles/               # CSS & styling
│   │   └── utils/                # Frontend utilities
│   │
│   ├── backend/                  # FastAPI backend
│   │   ├── api/                  # API (moved from /api)
│   │   ├── routers/              # API routes (TODO)
│   │   └── services/             # Business logic (TODO)
│   │
│   ├── core/                     # Core business logic
│   │   └── ... (existing modules)
│   │
│   ├── config/                   # Configuration
│   │   ├── settings.py           # App settings
│   │   └── constants.py          # Constants
│   │
│   ├── shared/                   # Shared utilities
│   │   ├── database.py           # Database operations
│   │   └── models.py             # Shared models
│   │
│   └── tests/                    # All tests
│       ├── unit/                 # Unit tests
│       └── integration/          # Integration tests
│
├── scripts/                      # Utility scripts
│   ├── check_api.py
│   ├── debug_whisper.py
│   └── convert_ui.py
│
├── data/                         # Data storage
├── app.py                        # Symlink to src/frontend/app.py
├── app_legacy.py                 # Old monolithic app (2,610 lines)
├── .env                          # Environment variables
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy and edit .env file
cp .env.example .env
nano .env  # Add your DEEPSEEK_API_KEY
```

### 3. Run Application

```bash
# Using Make (Recommended)
make dev      # Run Streamlit dev server (http://localhost:8501)
make api      # Run FastAPI backend (http://localhost:8000)
make run      # Run both servers
make test     # Run tests
make clean    # Clean up temporary files

# Or using npm-style commands
npm run dev   # Run Streamlit
npm run api   # Run FastAPI
npm run test  # Run tests

# Or direct commands
streamlit run app.py
uvicorn src.backend.api.main:app --reload --port 8000
```

---

## 🔄 Migration Status

> **⚠️ Project restructuring in progress**

### ✅ Completed
- Configuration management (`src/config/`)
- Frontend utilities (`src/frontend/utils/`)
- Styles (`src/frontend/styles/`)
- Components (`src/frontend/components/`)
- Test organization (`src/tests/unit/`, `src/tests/integration/`)
- Core modules moved to `src/core/`

### 🚧 In Progress
- Page extraction from `app_legacy.py` → `src/frontend/pages/`
- Backend service layer (`src/backend/services/`)
- Import path updates throughout codebase

### 📋 Temporary Notes
- **Current Usage**: For full functionality, use `streamlit run app_legacy.py`
- **New Entry Point**: `streamlit run app.py` (shows restructuring progress)
- **Reference**: Old monolithic code in `app_legacy.py`

---

## 📚 Usage

1. **Create Content** - ใส่หัวข้อ → AI gen บทภาษาไทย
2. **Scene Editor** - ดู/แก้ไขแต่ละฉาก
3. **Export Prompts** - Copy Veo 3 prompts (English) ไปใช้

---

## 🔧 Development

### Run Tests

```bash
# All tests
pytest

# Unit tests only
pytest src/tests/unit/ -v

# Integration tests only
pytest src/tests/integration/ -v

# Specific test file
pytest src/tests/unit/test_models.py -v
```

### Code Structure

- **Frontend**: Streamlit pages and components
- **Backend**: FastAPI REST API
- **Core**: Business logic (AI generation, scene splitting, etc.)
- **Config**: Centralized configuration using Pydantic
- **Shared**: Database operations and shared models

---

## 🌐 API

- **Script Generation**: DeepSeek API (Thai narration)
- **Video Prompts**: Auto-generated in English for Veo 3
- **Backend API**: http://localhost:8000 (FastAPI)

---

## 📝 License

Private project - All rights reserved

---

## 🚧 Version History

- **v2.2.0** (Current) - Major restructuring for scalability
- **v2.1.x** - Added PostgreSQL, dark mode, mobile responsive
- **v2.0.x** - Multi-page dashboard with project management
- **v1.x** - Initial prototype

---

For detailed documentation, see `/docs` folder.
