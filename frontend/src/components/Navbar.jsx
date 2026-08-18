import { Link } from 'react-router-dom';
import { Film, LogOut, Ticket, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Navbar({ onLoginClick }) {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <nav className="sticky top-0 z-50 border-b border-zinc-800 bg-zinc-950/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
        <Link to="/" className="flex items-center gap-2 text-lg font-bold tracking-tight text-white">
          <Film className="h-6 w-6 text-red-500" />
          <span>CineBook</span>
        </Link>

        <div className="flex items-center gap-3 sm:gap-5">
          {isAuthenticated ? (
            <>
              <div className="hidden items-center gap-2 text-sm text-zinc-400 sm:flex">
                <User className="h-4 w-4" />
                <span>{user?.name ?? user?.email}</span>
              </div>

              <Link
                to="/my-bookings"
                className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium text-zinc-300 transition hover:bg-zinc-800 hover:text-white"
              >
                <Ticket className="h-4 w-4" />
                <span className="hidden sm:inline">My Bookings</span>
              </Link>

              <button
                type="button"
                onClick={logout}
                className="flex items-center gap-1.5 rounded-lg bg-zinc-800 px-3 py-1.5 text-sm font-medium text-zinc-200 transition hover:bg-red-600 hover:text-white"
              >
                <LogOut className="h-4 w-4" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={onLoginClick}
              className="rounded-lg bg-red-600 px-4 py-1.5 text-sm font-semibold text-white transition hover:bg-red-500"
            >
              Login / Register
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}
