# 🎬 CINE-RESERVE — Full-Stack Movie Ticket & Seat Booking System

A high-concurrency movie reservation platform built with **FastAPI**, **SQLAlchemy (Async)**, **React**, **Vite**, and **Tailwind CSS**. Designed with ACID compliance and pessimistic locking to handle high-demand flash ticketing without double-booking anomalies.

---

## 🚀 Key Features

- **Pessimistic Seat Locking**: Implements short-lived dynamic reservations (10-minute hold) to avoid race conditions during concurrent checkouts.
- **Async Database Architecture**: Fully asynchronous database queries using SQLAlchemy Async Engine + SQLite/PostgreSQL.
- **JWT-Based Authentication**: Secure authentication flow with Bearer token storage, route protection, and auth state persistence.
- **Automated Concurrency Testing**: Integration test suite built with `pytest` and `httpx` validating atomic lock conflicts and state transitions.
- **Dynamic Seat Layout**: Multi-screen seat rendering with interactive status states (`AVAILABLE`, `LOCKED`, `BOOKED`).

---

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **Backend** | FastAPI, Python 3.14+, SQLAlchemy (AsyncIO), Pydantic v2, Passlib (Bcrypt), PyJWT |
| **Frontend** | React 18, Vite, Tailwind CSS, Axios, Lucide Icons |
| **Testing** | Pytest, Pytest-AsyncIO, HTTPX |
| **Containerization** | Docker, Docker Compose |

---

## 🏗️ Architecture & Locking Workflow

```text
[User Request] 
      │
      ▼
[FastAPI Route: /bookings/lock-seats]
      │
      ├─► Acquire DB Row Lock (SELECT ... FOR UPDATE)
      ├─► Verify Seat Status != 'BOOKED' & Lock Not Active
      ├─► Set Seat Status = 'LOCKED', Assign Lock Expiry (now + 10m)
      └─► Commit Transaction (Release Lock)
            │
            ├─► [Succeeds] ──► 200 OK (Proceed to Payment/Confirm)
            └─► [Conflict] ──► 409 Conflict (Seats Unavailable)
```

---

## 🚦 Getting Started (Local Development)

### 1. Backend Setup

```bash
cd backend
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Install Dependencies
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic passlib bcrypt python-jose pyjwt pytest pytest-asyncio httpx

# Seed Database
python seed.py

# Run Server
uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd ../frontend
npm install
npm run dev
```

---

## 🧪 Running Concurrency Tests

To run the automated suite that simulates two simultaneous users attempting to lock the same seat:

```bash
cd backend
python -m pytest test_concurrency.py -v
```

---

## 🐳 Docker Deployment

Run both the frontend and backend using Docker Compose:

```bash
docker-compose up --build
```

- **Frontend:** `http://localhost:5173`
- **Backend API Docs:** `http://localhost:8000/docs
