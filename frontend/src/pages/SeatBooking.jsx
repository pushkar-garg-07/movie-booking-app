import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AlertCircle, CheckCircle2, Loader2, Timer } from 'lucide-react';
import { confirmBooking, getSeatLayout, lockSeats } from '../api/client';
import { useAuth } from '../context/AuthContext';

function seatLabel(seat) {
  return `${seat.row_label}${seat.seat_number}`;
}

function parseUtcTimestamp(dateStr) {
  if (!dateStr) return 0;
  // If no timezone offset exists, append 'Z' to force UTC parsing
  const formatted = dateStr.endsWith('Z') || dateStr.includes('+') ? dateStr : `${dateStr}Z`;
  return new Date(formatted).getTime();
}

function getSeatStyle(seat, selectedIds, lockedByMe) {
  if (!seat) return 'invisible';

  const isSelected = selectedIds.includes(seat.seat_id);
  const isMine = lockedByMe.includes(seat.seat_id);

  if (isSelected || isMine) {
    return 'bg-green-500 text-white ring-2 ring-green-400 cursor-default';
  }
  if (seat.status === 'BOOKED') {
    return 'bg-red-600 text-red-200 cursor-not-allowed opacity-80';
  }
  if (seat.status === 'LOCKED') {
    return 'bg-yellow-500 text-yellow-950 cursor-not-allowed opacity-90';
  }
  return 'bg-zinc-600 text-zinc-200 hover:bg-zinc-500 hover:ring-2 hover:ring-zinc-400 cursor-pointer';
}

function isSeatClickable(seat, selectedIds, lockedByMe, isLocked) {
  if (!seat || isLocked) return false;
  if (seat.status === 'BOOKED') return false;
  if (seat.status === 'LOCKED' && !lockedByMe.includes(seat.seat_id)) return false;
  return true;
}

function formatCountdown(ms) {
  const totalSec = Math.max(0, Math.floor(ms / 1000));
  const min = Math.floor(totalSec / 60);
  const sec = totalSec % 60;
  return `${min}:${sec.toString().padStart(2, '0')}`;
}

export default function SeatBooking({ onLoginClick }) {
  const { showtimeId } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const [layout, setLayout] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedIds, setSelectedIds] = useState([]);
  const [lockedByMe, setLockedByMe] = useState([]);
  const [lockExpiry, setLockExpiry] = useState(null);
  const [countdown, setCountdown] = useState(0);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const expiredHandled = useRef(false);

  const isLocked = lockedByMe.length > 0 && lockExpiry !== null && countdown > 0;

  const fetchLayout = useCallback(async () => {
    try {
      const { data } = await getSeatLayout(showtimeId);
      setLayout(data);
      setError('');
    } catch {
      setError('Failed to load seat layout.');
    } finally {
      setLoading(false);
    }
  }, [showtimeId]);

  useEffect(() => {
    fetchLayout();
    const interval = setInterval(fetchLayout, 10000);
    return () => clearInterval(interval);
  }, [fetchLayout]);

  useEffect(() => {
    if (!lockExpiry) return undefined;

    const expiryMs = parseUtcTimestamp(lockExpiry);

    const tick = () => {
      const remaining = expiryMs - Date.now();
      setCountdown(Math.max(0, remaining));

      if (remaining <= 0 && !expiredHandled.current) {
        expiredHandled.current = true;
        setLockedByMe([]);
        setLockExpiry(null);
        setSelectedIds([]);
        setActionError('Lock expired. Seats have been released.');
        fetchLayout();
        setTimeout(() => navigate('/'), 2500);
      }
    };

    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [lockExpiry, fetchLayout, navigate]);

  const toggleSeat = (seat) => {
    if (!isAuthenticated) {
      onLoginClick?.();
      return;
    }
    if (!isSeatClickable(seat, selectedIds, lockedByMe, isLocked)) return;

    setSelectedIds((prev) =>
      prev.includes(seat.seat_id)
        ? prev.filter((id) => id !== seat.seat_id)
        : [...prev, seat.seat_id],
    );
    setActionError('');
  };

  const handleLockSeats = async () => {
    if (!selectedIds.length) {
      setActionError('Select at least one seat.');
      return;
    }
    setActionLoading(true);
    setActionError('');
    try {
      const { data } = await lockSeats(Number(showtimeId), selectedIds);
      expiredHandled.current = false;
      setLockedByMe(data.locked_seat_ids);
      setLockExpiry(data.locked_until);
      await fetchLayout();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setActionError(typeof detail === 'string' ? detail : detail?.message ?? 'Failed to lock seats.');
      await fetchLayout();
    } finally {
      setActionLoading(false);
    }
  };

  const handleConfirm = async () => {
    setActionLoading(true);
    setActionError('');
    try {
      await confirmBooking(Number(showtimeId), lockedByMe);
      setSuccessMsg('Booking confirmed! Redirecting to your bookings…');
      setTimeout(() => navigate('/my-bookings'), 1500);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setActionError(typeof detail === 'string' ? detail : detail?.message ?? 'Failed to confirm booking.');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-red-500" />
      </div>
    );
  }

  if (error || !layout) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center">
        <p className="text-red-400">{error || 'Showtime not found.'}</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
      <div className="mb-6 text-center">
        <h1 className="text-2xl font-bold text-white">Select Your Seats</h1>
        <p className="mt-1 text-sm text-zinc-400">{layout.screen_name}</p>
      </div>

      {/* Screen */}
      <div className="mb-8">
        <div className="mx-auto max-w-md rounded-t-full border-t-4 border-zinc-600 bg-gradient-to-b from-zinc-700/40 to-transparent py-3 text-center text-xs font-semibold uppercase tracking-[0.3em] text-zinc-500">
          Screen
        </div>
      </div>

      {/* Seat grid */}
      <div className="overflow-x-auto">
        <div className="mx-auto inline-block min-w-full">
          {/* Column numbers */}
          <div className="mb-2 flex justify-center gap-1.5 pl-8">
            {Array.from({ length: layout.total_cols }, (_, i) => (
              <span key={i} className="flex h-8 w-8 items-center justify-center text-xs text-zinc-500">
                {i + 1}
              </span>
            ))}
          </div>

          {layout.grid.map((row, rowIdx) => (
            <div key={rowIdx} className="mb-1.5 flex items-center justify-center gap-1.5">
              <span className="flex h-8 w-6 items-center justify-center text-xs font-bold text-zinc-400">
                {String.fromCharCode(65 + rowIdx)}
              </span>
              {row.map((seat, colIdx) => (
                <button
                  key={colIdx}
                  type="button"
                  disabled={!seat || !isSeatClickable(seat, selectedIds, lockedByMe, isLocked)}
                  onClick={() => toggleSeat(seat)}
                  title={seat ? seatLabel(seat) : ''}
                  className={`flex h-8 w-8 items-center justify-center rounded-md text-[10px] font-semibold transition ${getSeatStyle(
                    seat,
                    selectedIds,
                    lockedByMe,
                  )}`}
                >
                  {seat ? seat.seat_number : ''}
                </button>
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="mt-8 flex flex-wrap justify-center gap-4 text-xs text-zinc-400">
        <span className="flex items-center gap-1.5">
          <span className="h-4 w-4 rounded bg-zinc-600" /> Available
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-4 w-4 rounded bg-green-500" /> Selected
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-4 w-4 rounded bg-yellow-500" /> Locked
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-4 w-4 rounded bg-red-600" /> Booked
        </span>
      </div>

      {/* Timer */}
      {isLocked && (
        <div className="mt-6 flex items-center justify-center gap-2 rounded-xl border border-yellow-500/30 bg-yellow-500/10 px-4 py-3 text-yellow-400">
          <Timer className="h-5 w-5" />
          <span className="font-mono text-lg font-bold">{formatCountdown(countdown)}</span>
          <span className="text-sm">remaining to confirm</span>
        </div>
      )}

      {/* Messages */}
      {actionError && (
        <div className="mt-4 flex items-center gap-2 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {actionError}
        </div>
      )}
      {successMsg && (
        <div className="mt-4 flex items-center gap-2 rounded-lg border border-green-500/30 bg-green-500/10 px-4 py-3 text-sm text-green-400">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          {successMsg}
        </div>
      )}

      {/* Actions */}
      <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
        {!isLocked ? (
          <button
            type="button"
            onClick={handleLockSeats}
            disabled={actionLoading || !selectedIds.length}
            className="rounded-xl bg-red-600 px-8 py-3 text-sm font-semibold text-white transition hover:bg-red-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {actionLoading ? 'Locking…' : `Lock Seats (${selectedIds.length})`}
          </button>
        ) : (
          <button
            type="button"
            onClick={handleConfirm}
            disabled={actionLoading}
            className="rounded-xl bg-green-600 px-8 py-3 text-sm font-semibold text-white transition hover:bg-green-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {actionLoading ? 'Confirming…' : 'Confirm Booking'}
          </button>
        )}
      </div>

      {!isAuthenticated && (
        <p className="mt-4 text-center text-sm text-zinc-500">
          You must be logged in to select and lock seats.
        </p>
      )}
    </div>
  );
}