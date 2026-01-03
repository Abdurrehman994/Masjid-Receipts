# Masjid Receipts API
Before you begin, ensure you have the following installed:

- Python 3.10+ (Python 3.13 recommended)
- PostgreSQL 15+
- Git (for cloning the repository)
- pip (Python package manager)

---

## Installation

### 1. Clone the Repository
git clone https://github.com/Abdurrehman994/masjid-receipts-api.git
### 2. Create Virtual Environment

python -m venv venv
.\venv\Scripts\Activate.ps1

### 3. Install Dependencies
pip install -r requirements.txt

## Configuration

### 1. Create Environment File
Create a `.env` file in the project root:
Edit `.env` with your settings:
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/masjid_receipts
SECRET_KEY=your-secret-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE=5242880

**Generate a secure SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Database Setup
# 1 Create database
CREATE DATABASE masjid_receipts;

### 2. Run Migrations
```bash
# Windows
.\venv\Scripts\alembic.exe upgrade head

# Linux/Mac
alembic upgrade head
```

##  Running the Application

### Start the Server
```bash
uvicorn app.main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- Interactive Docs (Swagger): http://localhost:8000/docs
