from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models import Movie, SeatStatus, Showtime, ShowtimeSeat
from schemas import MovieResponse, SeatGridItem, SeatLayoutResponse

router = APIRouter(tags=["movies"])


async def clear_expired_locks(db: AsyncSession, showtime_id: int | None = None) -> None:
    now = datetime.utcnow()
    stmt = (
        update(ShowtimeSeat)
        .where(
            ShowtimeSeat.status == SeatStatus.LOCKED,
            ShowtimeSeat.locked_until.is_not(None),
            ShowtimeSeat.locked_until < now,
        )
        .values(status=SeatStatus.AVAILABLE, locked_until=None)
    )
    if showtime_id is not None:
        stmt = stmt.where(ShowtimeSeat.showtime_id == showtime_id)
    await db.execute(stmt)


@router.get("/movies", response_model=list[MovieResponse])
async def list_movies(db: AsyncSession = Depends(get_db)) -> list[Movie]:
    result = await db.execute(
        select(Movie).options(selectinload(Movie.showtimes)).order_by(Movie.title)
    )
    return list(result.scalars().unique().all())


@router.get("/showtimes/{showtime_id}/seats", response_model=SeatLayoutResponse)
async def get_showtime_seats(
    showtime_id: int,
    db: AsyncSession = Depends(get_db),
) -> SeatLayoutResponse:
    showtime_result = await db.execute(
        select(Showtime)
        .options(
            selectinload(Showtime.screen),
            selectinload(Showtime.showtime_seats).selectinload(ShowtimeSeat.seat),
        )
        .where(Showtime.id == showtime_id)
    )
    showtime = showtime_result.scalar_one_or_none()
    if showtime is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Showtime not found")

    await clear_expired_locks(db, showtime_id)
    await db.commit()

    result = await db.execute(
        select(ShowtimeSeat)
        .options(selectinload(ShowtimeSeat.seat))
        .where(ShowtimeSeat.showtime_id == showtime_id)
    )
    showtime_seats = list(result.scalars().all())

    screen = showtime.screen
    grid: list[list[SeatGridItem | None]] = [
        [None for _ in range(screen.total_cols)] for _ in range(screen.total_rows)
    ]

    row_index = {label: idx for idx, label in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")}

    for sts in showtime_seats:
        seat = sts.seat
        row_idx = row_index.get(seat.row_label)
        if row_idx is None or row_idx >= screen.total_rows:
            continue
        col_idx = seat.seat_number - 1
        if col_idx < 0 or col_idx >= screen.total_cols:
            continue
        grid[row_idx][col_idx] = SeatGridItem(
            showtime_seat_id=sts.id,
            seat_id=seat.id,
            row_label=seat.row_label,
            seat_number=seat.seat_number,
            seat_type=seat.seat_type,
            status=sts.status.value,
            locked_until=sts.locked_until,
        )

    return SeatLayoutResponse(
        showtime_id=showtime.id,
        screen_name=screen.name,
        total_rows=screen.total_rows,
        total_cols=screen.total_cols,
        grid=grid,
    )
