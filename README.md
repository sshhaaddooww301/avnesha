# 🛡️ QDS-SIEM

> **Security Information and Event Management for Quantum Digital Signature Networks**

---

## 📋 Prerequisites

- **Docker & Docker Compose** (recommended) OR
- **Python 3.10+**, **Node.js 18+**, and **PostgreSQL 16**

---

## 🚀 Option A: Docker Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/sshhaaddooww301/avnesha.git
cd hackthon

# Start all services (database, backend, frontend)
docker-compose up --build -d

# Check running services
docker-compose ps
```

### Access Points:
| Service | URL |
|:---|:---|
| **SOC Dashboard** | [http://localhost:3000](http://localhost:3000) |
| **API Docs (Swagger)** | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **PostgreSQL** | `localhost:5436` (User: `postgres` / Pass: `postgres123`) |

---

## 🔧 Option B: Manual Local Setup

### 1. Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 3. Open Dashboard

Visit [http://localhost:3000](http://localhost:3000)

---

## 👥 Team

- **Team AtharvaX 
