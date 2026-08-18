import asyncio
from datetime import datetime, timedelta

from sqlalchemy import select

from database import AsyncSessionLocal, engine
from models import Base, Movie, Screen, Seat, SeatStatus, Showtime, ShowtimeSeat


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # 1. Create Screens
        screens = [
            Screen(name="Screen 1 (IMAX)", total_rows=4, total_cols=10),
            Screen(name="Screen 2 (Dolby Cinema)", total_rows=4, total_cols=10),
        ]
        for screen in screens:
            db.add(screen)
        await db.flush()

        # 2. Create Seats for each Screen
        screen_seats: dict[int, list[Seat]] = {}
        for screen in screens:
            seats: list[Seat] = []
            for row_label in ("A", "B", "C", "D"):
                for seat_number in range(1, 11):
                    seat_type = "PREMIUM" if row_label in ("A", "B") else "STANDARD"
                    seat = Seat(
                        screen_id=screen.id,
                        row_label=row_label,
                        seat_number=seat_number,
                        seat_type=seat_type,
                    )
                    seats.append(seat)
                    db.add(seat)
            screen_seats[screen.id] = seats
        await db.flush()

        # 3. Create Expanded Movie Catalog
        movies = [
            Movie(
                title="Inception",
                genre="Sci-Fi / Action",
                duration_mins=148,
                poster_url="https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=800&auto=format&fit=crop&q=80",
            ),
            Movie(
                title="The Dark Knight",
                genre="Action / Crime",
                duration_mins=152,
                poster_url="https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=800&auto=format&fit=crop&q=80",
            ),
            Movie(
                title="Interstellar",
                genre="Sci-Fi / Adventure",
                duration_mins=169,
                poster_url="https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&auto=format&fit=crop&q=80",
            ),
            Movie(
                title="Oppenheimer",
                genre="Biography / Drama",
                duration_mins=180,
                poster_url="https://images.unsplash.com/photo-1440404653325-ab127d49abc1?w=800&auto=format&fit=crop&q=80",
            ),
            Movie(
                title="Spider-Man: Across the Spider-Verse",
                genre="Animation / Action",
                duration_mins=140,
                poster_url="https://images.unsplash.com/photo-1635805737707-575885ab0820?w=800&auto=format&fit=crop&q=80",
            ),
            Movie(
                title="Avengers: Endgame",
                genre="Action / Sci-Fi",
                duration_mins=181,
                poster_url="https://images.unsplash.com/photo-1563089145-599997674d42?w=800&auto=format&fit=crop&q=80",
            ),
        ]
        for movie in movies:
            db.add(movie)
        await db.flush()

        # 4. Create Showtimes
        base_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0) + timedelta(hours=2)
        showtimes = [
            # Inception
            Showtime(movie_id=movies[0].id, screen_id=screens[0].id, start_time=base_time, base_price=12.50),
            Showtime(movie_id=movies[0].id, screen_id=screens[1].id, start_time=base_time + timedelta(hours=3), base_price=14.00),
            
            # The Dark Knight
            Showtime(movie_id=movies[1].id, screen_id=screens[0].id, start_time=base_time + timedelta(hours=4), base_price=13.00),
            Showtime(movie_id=movies[1].id, screen_id=screens[1].id, start_time=base_time + timedelta(days=1), base_price=15.00),
            
            # Interstellar
            Showtime(movie_id=movies[2].id, screen_id=screens[0].id, start_time=base_time + timedelta(hours=1), base_price=15.00),
            Showtime(movie_id=movies[2].id, screen_id=screens[1].id, start_time=base_time + timedelta(hours=5), base_price=16.50),
            
            # Oppenheimer
            Showtime(movie_id=movies[3].id, screen_id=screens[0].id, start_time=base_time + timedelta(hours=6), base_price=14.50),
            Showtime(movie_id=movies[3].id, screen_id=screens[1].id, start_time=base_time + timedelta(days=1, hours=2), base_price=16.00),
            
            # Spider-Man
            Showtime(movie_id=movies[4].id, screen_id=screens[0].id, start_time=base_time + timedelta(hours=2), base_price=11.50),
            Showtime(movie_id=movies[4].id, screen_id=screens[1].id, start_time=base_time + timedelta(hours=7), base_price=13.00),
            
            # Avengers: Endgame
            Showtime(movie_id=movies[5].id, screen_id=screens[0].id, start_time=base_time + timedelta(days=1, hours=4), base_price=15.50),
            Showtime(movie_id=movies[5].id, screen_id=screens[1].id, start_time=base_time + timedelta(days=1, hours=8), base_price=16.00),
        ]
        for showtime in showtimes:
            db.add(showtime)
        await db.flush()

        # 5. Populate ShowtimeSeats for all Showtimes
        total_showtime_seats = 0
        for showtime in showtimes:
            for seat in screen_seats[showtime.screen_id]:
                db.add(
                    ShowtimeSeat(
                        showtime_id=showtime.id,
                        seat_id=seat.id,
                        status=SeatStatus.AVAILABLE,
                    )
                )
                total_showtime_seats += 1

        await db.commit()
        print("Database seeded successfully.")
        print(f"  Movies: {len(movies)}")
        print(f"  Screens: {len(screens)}")
        print(f"  Total Showtimes: {len(showtimes)}")
        print(f"  Total Showtime Seats: {total_showtime_seats}")


if __name__ == "__main__":
    asyncio.run(seed())