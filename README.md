# 🎬 CineReserve — Concurrency-Safe Movie Ticket Booking System

A full-stack movie seat reservation platform engineered with FastAPI and React. Designed to handle high-traffic seat selection with pessimistic concurrency control, sub-second reactivity, and transactional integrity.

---

## 📌 Architecture & Concurrency Strategy

* **Pessimistic Seat Locking**: Seats selected by a user enter a `LOCKED` state with a 5-minute auto-expiry window. Other users receive real-time conflict status (`409 Conflict`).
* **ACID Transactions**: Final booking confirmation converts locked seats into `BOOKED` inside an isolated database transaction, rolling back gracefully if expired.
* **Timezone Normalization**: UTC-synchronized lock timestamps prevent client-side device drift from affecting reservation timeouts.

---

## 🛠️ Tech Stack

* **Backend**: FastAPI, Async SQLAlchemy, SQLite / PostgreSQL, Pydantic v2, Python-Jose (JWT), Passlib (Bcrypt).
* **Frontend**: React 18, Vite, Tailwind CSS, Axios, Lucide Icons, React Router v6.
* **Testing & DevOps**: Pytest, Pytest-Asyncio, Docker & Docker Compose.

---

## 🚀 Quick Start (Local Setup)

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python seed.py
uvicorn main:app --reload --port 8000