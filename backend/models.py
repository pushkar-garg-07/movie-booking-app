import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class SeatStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    LOCKED = "LOCKED"
    BOOKED = "BOOKED"


class BookingStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    genre: Mapped[str] = mapped_column(String(100), nullable=False)
    duration_mins: Mapped[int] = mapped_column(Integer, nullable=False)
    poster_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    showtimes: Mapped[list["Showtime"]] = relationship(back_populates="movie")


class Screen(Base):
    __tablename__ = "screens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    total_cols: Mapped[int] = mapped_column(Integer, nullable=False)

    seats: Mapped[list["Seat"]] = relationship(back_populates="screen")
    showtimes: Mapped[list["Showtime"]] = relationship(back_populates="screen")


class Seat(Base):
    __tablename__ = "seats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    screen_id: Mapped[int] = mapped_column(ForeignKey("screens.id"), nullable=False)
    row_label: Mapped[str] = mapped_column(String(5), nullable=False)
    seat_number: Mapped[int] = mapped_column(Integer, nullable=False)
    seat_type: Mapped[str] = mapped_column(String(50), default="STANDARD", nullable=False)

    screen: Mapped["Screen"] = relationship(back_populates="seats")
    showtime_seats: Mapped[list["ShowtimeSeat"]] = relationship(back_populates="seat")

    __table_args__ = (UniqueConstraint("screen_id", "row_label", "seat_number", name="uq_screen_seat"),)


class Showtime(Base):
    __tablename__ = "showtimes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id"), nullable=False)
    screen_id: Mapped[int] = mapped_column(ForeignKey("screens.id"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    base_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    movie: Mapped["Movie"] = relationship(back_populates="showtimes")
    screen: Mapped["Screen"] = relationship(back_populates="showtimes")
    showtime_seats: Mapped[list["ShowtimeSeat"]] = relationship(back_populates="showtime")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="showtime")


class ShowtimeSeat(Base):
    __tablename__ = "showtime_seats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    showtime_id: Mapped[int] = mapped_column(ForeignKey("showtimes.id"), nullable=False)
    seat_id: Mapped[int] = mapped_column(ForeignKey("seats.id"), nullable=False)
    status: Mapped[SeatStatus] = mapped_column(
        Enum(SeatStatus), default=SeatStatus.AVAILABLE, nullable=False
    )
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    showtime: Mapped["Showtime"] = relationship(back_populates="showtime_seats")
    seat: Mapped["Seat"] = relationship(back_populates="showtime_seats")
    booking_items: Mapped[list["BookingItem"]] = relationship(back_populates="showtime_seat")

    __table_args__ = (UniqueConstraint("showtime_id", "seat_id", name="uq_showtime_seat"),)


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    showtime_id: Mapped[int] = mapped_column(ForeignKey("showtimes.id"), nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus), default=BookingStatus.CONFIRMED, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="bookings")
    showtime: Mapped["Showtime"] = relationship(back_populates="bookings")
    items: Mapped[list["BookingItem"]] = relationship(back_populates="booking")


class BookingItem(Base):
    __tablename__ = "booking_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    showtime_seat_id: Mapped[int] = mapped_column(ForeignKey("showtime_seats.id"), nullable=False)

    booking: Mapped["Booking"] = relationship(back_populates="items")
    showtime_seat: Mapped["ShowtimeSeat"] = relationship(back_populates="booking_items")
