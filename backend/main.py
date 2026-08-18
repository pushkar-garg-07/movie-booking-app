from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth_routes, booking_routes, movie_routes

app = FastAPI(title="Movie Seat Booking Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(movie_routes.router)
app.include_router(booking_routes.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
