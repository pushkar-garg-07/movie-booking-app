from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ShowtimeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    movie_id: int
    screen_id: int
    start_time: datetime
    base_price: Decimal


class MovieResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    genre: str
    duration_mins: int
    poster_url: str | None
    showtimes: list[ShowtimeResponse] = []


class SeatGridItem(BaseModel):
    showtime_seat_id: int
    seat_id: int
    row_label: str
    seat_number: int
    seat_type: str
    status: str
    locked_until: datetime | None = None


class SeatLayoutResponse(BaseModel):
    showtime_id: int
    screen_name: str
    total_rows: int
    total_cols: int
    grid: list[list[SeatGridItem | None]]


class LockSeatsRequest(BaseModel):
    showtime_id: int
    seat_ids: list[int] = Field(min_length=1)


class LockSeatsResponse(BaseModel):
    showtime_id: int
    locked_seat_ids: list[int]
    locked_until: datetime
    message: str


class ConfirmBookingRequest(BaseModel):
    showtime_id: int
    seat_ids: list[int] = Field(min_length=1)


class BookingSeatDetail(BaseModel):
    row_label: str
    seat_number: int
    seat_type: str


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    showtime_id: int
    total_amount: Decimal
    status: str
    created_at: datetime
    movie_title: str
    showtime_start: datetime
    seats: list[BookingSeatDetail]
