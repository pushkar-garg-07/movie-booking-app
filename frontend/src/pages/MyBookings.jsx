import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, Loader2, Ticket, XCircle } from 'lucide-react';
import { cancelBooking, getMyBookings } from '../api/client';
import { useAuth } from '../context/AuthContext';

function formatDate(iso) {
  return new Date(iso).toLocaleString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatSeats(seats) {
  return seats.map((s) => `${s.row_label}${s.seat_number}`).join(', ');
}

function StatusBadge({ status }) {
  const isConfirmed = status === 'CONFIRMED';
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
        isConfirmed
          ? 'bg-green-500/15 text-green-400 ring-1 ring-green-500/30'
          : 'bg-zinc-700 text-zinc-400 ring-1 ring-zinc-600'
      }`}
    >
      {status}
    </span>
  );
}

export default function MyBookings({ onLoginClick }) {
  const { isAuthenticated } = useAuth();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [cancellingId, setCancellingId] = useState(null);

  const fetchBookings = () => {
    setLoading(true);
    getMyBookings()
      .then(({ data }) => setBookings(data))
      .catch(() => setError('Failed to load bookings.'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }
    fetchBookings();
  }, [isAuthenticated]);

  const handleCancel = async (bookingId) => {
    setCancellingId(bookingId);
    try {
      const { data } = await cancelBooking(bookingId);
      setBookings((prev) => prev.map((b) => (b.id === bookingId ? data : b)));
    } catch {
      setError('Failed to cancel booking.');
    } finally {
      setCancellingId(null);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center">
        <Ticket className="mx-auto mb-4 h-12 w-12 text-zinc-600" />
        <h2 className="text-xl font-bold text-white">Sign in to view bookings</h2>
        <p className="mt-2 text-zinc-400">Your ticket history appears here after you log in.</p>
        <button
          type="button"
          onClick={onLoginClick}
          className="mt-6 rounded-lg bg-red-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-red-500"
        >
          Login / Register
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-red-500" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">My Bookings</h1>
        <p className="mt-1 text-zinc-400">Manage your movie tickets</p>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {!bookings.length ? (
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 py-16 text-center">
          <Ticket className="mx-auto mb-4 h-12 w-12 text-zinc-600" />
          <p className="text-zinc-400">No bookings yet.</p>
          <Link
            to="/"
            className="mt-4 inline-block text-sm font-medium text-red-400 hover:text-red-300"
          >
            Browse movies →
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {bookings.map((booking) => (
            <article
              key={booking.id}
              className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5 shadow-lg"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-bold text-white">{booking.movie_title}</h2>
                  <div className="mt-1 flex items-center gap-1.5 text-sm text-zinc-400">
                    <Calendar className="h-3.5 w-3.5" />
                    {formatDate(booking.showtime_start)}
                  </div>
                </div>
                <StatusBadge status={booking.status} />
              </div>

              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Seats</p>
                  <p className="mt-0.5 text-sm text-zinc-200">{formatSeats(booking.seats)}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Total</p>
                  <p className="mt-0.5 text-sm font-semibold text-white">₹{booking.total_amount}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Booked on</p>
                  <p className="mt-0.5 text-sm text-zinc-300">{formatDate(booking.created_at)}</p>
                </div>
              </div>

              {booking.status === 'CONFIRMED' && (
                <button
                  type="button"
                  onClick={() => handleCancel(booking.id)}
                  disabled={cancellingId === booking.id}
                  className="mt-4 flex items-center gap-1.5 rounded-lg border border-red-500/30 px-4 py-2 text-sm font-medium text-red-400 transition hover:bg-red-500/10 disabled:opacity-50"
                >
                  <XCircle className="h-4 w-4" />
                  {cancellingId === booking.id ? 'Cancelling…' : 'Cancel Booking'}
                </button>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
