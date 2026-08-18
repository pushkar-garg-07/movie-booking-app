from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from auth import get_current_user
from database import get_db
from models import (
    Booking,
    BookingItem,
    BookingStatus,
    SeatStatus,
    Showtime,
    ShowtimeSeat,
    User,
)
from routers.movie_routes import clear_expired_locks
from schemas import (
    BookingResponse,
    BookingSeatDetail,
    ConfirmBookingRequest,
    LockSeatsRequest,
    LockSeatsResponse,
)

router = APIRouter(prefix="/bookings", tags=["bookings"])

LOCK_DURATION_MINUTES = 5


def seat_is_lockable(sts: ShowtimeSeat, now: datetime) -> bool:
    if sts.status == SeatStatus.AVAILABLE:
        return True
    if sts.status == SeatStatus.LOCKED and sts.locked_until and sts.locked_until < now:
        return True
    return False


@router.post("/lock-seats", response_model=LockSeatsResponse)
async def lock_seats(
    payload: LockSeatsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LockSeatsResponse:
    now = datetime.utcnow()
    locked_until = now + timedelta(minutes=LOCK_DURATION_MINUTES)

    try:
        await clear_expired_locks(db, payload.showtime_id)

        showtime_result = await db.execute(
            select(Showtime).where(Showtime.id == payload.showtime_id)
        )
        showtime = showtime_result.scalar_one_or_none()
        if showtime is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Showtime not found")

        result = await db.execute(
            select(ShowtimeSeat)
            .where(
                ShowtimeSeat.showtime_id == payload.showtime_id,
                ShowtimeSeat.seat_id.in_(payload.seat_ids),
            )
            .with_for_update()
        )
        showtime_seats = list(result.scalars().all())

        if len(showtime_seats) != len(set(payload.seat_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more seats not found for this showtime",
            )

        unavailable = [
            sts.seat_id for sts in showtime_seats if not seat_is_lockable(sts, now)
        ]
        if unavailable:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": "Some seats are unavailable", "seat_ids": unavailable},
            )

        for sts in showtime_seats:
            sts.status = SeatStatus.LOCKED
            sts.locked_until = locked_until

        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise

    return LockSeatsResponse(
        showtime_id=payload.showtime_id,
        locked_seat_ids=payload.seat_ids,
        locked_until=locked_until,
        message=f"Seats locked until {locked_until.isoformat()} UTC",
    )


@router.post("/confirm", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def confirm_booking(
    payload: ConfirmBookingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BookingResponse:
    now = datetime.utcnow()

    try:
        await clear_expired_locks(db, payload.showtime_id)

        showtime_result = await db.execute(
            select(Showtime)
            .options(selectinload(Showtime.movie))
            .where(Showtime.id == payload.showtime_id)
        )
        showtime = showtime_result.scalar_one_or_none()
        if showtime is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Showtime not found")

        result = await db.execute(
            select(ShowtimeSeat)
            .options(selectinload(ShowtimeSeat.seat))
            .where(
                ShowtimeSeat.showtime_id == payload.showtime_id,
                ShowtimeSeat.seat_id.in_(payload.seat_ids),
            )
            .with_for_update()
        )
        showtime_seats = list(result.scalars().all())

        if len(showtime_seats) != len(set(payload.seat_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more seats not found for this showtime",
            )

        invalid = [
            sts.seat_id
            for sts in showtime_seats
            if sts.status != SeatStatus.LOCKED
            or sts.locked_until is None
            or sts.locked_until <= now
        ]
        if invalid:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": "Seats are not locked or lock expired", "seat_ids": invalid},
            )

        total_amount = Decimal(str(showtime.base_price)) * len(showtime_seats)
        booking = Booking(
            user_id=current_user.id,
            showtime_id=showtime.id,
            total_amount=total_amount,
            status=BookingStatus.CONFIRMED,
        )
        db.add(booking)
        await db.flush()

        seat_details: list[BookingSeatDetail] = []
        for sts in showtime_seats:
            sts.status = SeatStatus.BOOKED
            sts.locked_until = None
            db.add(
                BookingItem(
                    booking_id=booking.id,
                    showtime_seat_id=sts.id,
                )
            )
            seat = sts.seat
            seat_details.append(
                BookingSeatDetail(
                    row_label=seat.row_label,
                    seat_number=seat.seat_number,
                    seat_type=seat.seat_type,
                )
            )

        await db.commit()
        await db.refresh(booking)
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise

    return BookingResponse(
        id=booking.id,
        showtime_id=booking.showtime_id,
        total_amount=booking.total_amount,
        status=booking.status.value,
        created_at=booking.created_at,
        movie_title=showtime.movie.title,
        showtime_start=showtime.start_time,
        seats=seat_details,
    )


@router.get("/my", response_model=list[BookingResponse])
async def get_my_bookings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BookingResponse]:
    result = await db.execute(
        select(Booking)
        .options(
            selectinload(Booking.showtime).selectinload(Showtime.movie),
            selectinload(Booking.items)
            .selectinload(BookingItem.showtime_seat)
            .selectinload(ShowtimeSeat.seat),
        )
        .where(Booking.user_id == current_user.id)
        .order_by(Booking.created_at.desc())
    )
    bookings = list(result.scalars().unique().all())

    responses: list[BookingResponse] = []
    for booking in bookings:
        seats = [
            BookingSeatDetail(
                row_label=item.showtime_seat.seat.row_label,
                seat_number=item.showtime_seat.seat.seat_number,
                seat_type=item.showtime_seat.seat.seat_type,
            )
            for item in booking.items
        ]
        responses.append(
            BookingResponse(
                id=booking.id,
                showtime_id=booking.showtime_id,
                total_amount=booking.total_amount,
                status=booking.status.value,
                created_at=booking.created_at,
                movie_title=booking.showtime.movie.title,
                showtime_start=booking.showtime.start_time,
                seats=seats,
            )
        )
    return responses


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BookingResponse:
    try:
        result = await db.execute(
            select(Booking)
            .options(
                selectinload(Booking.showtime).selectinload(Showtime.movie),
                selectinload(Booking.items)
                .selectinload(BookingItem.showtime_seat)
                .selectinload(ShowtimeSeat.seat),
            )
            .where(Booking.id == booking_id, Booking.user_id == current_user.id)
            .with_for_update()
        )
        booking = result.scalar_one_or_none()
        if booking is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
        if booking.status == BookingStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking is already cancelled",
            )

        booking.status = BookingStatus.CANCELLED
        for item in booking.items:
            sts = item.showtime_seat
            sts.status = SeatStatus.AVAILABLE
            sts.locked_until = None

        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise

    seats = [
        BookingSeatDetail(
            row_label=item.showtime_seat.seat.row_label,
            seat_number=item.showtime_seat.seat.seat_number,
            seat_type=item.showtime_seat.seat.seat_type,
        )
        for item in booking.items
    ]
    return BookingResponse(
        id=booking.id,
        showtime_id=booking.showtime_id,
        total_amount=booking.total_amount,
        status=booking.status.value,
        created_at=booking.created_at,
        movie_title=booking.showtime.movie.title,
        showtime_start=booking.showtime.start_time,
        seats=seats,
    )
