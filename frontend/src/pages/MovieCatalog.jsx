import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Clock, Film, Loader2 } from 'lucide-react';
import { getMovies } from '../api/client';

function formatShowtime(iso) {
  return new Date(iso).toLocaleString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatDuration(mins) {
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return h ? `${h}h ${m}m` : `${m}m`;
}

const POSTER_GRADIENTS = [
  'from-indigo-600 via-purple-600 to-pink-600',
  'from-amber-600 via-orange-600 to-red-600',
  'from-emerald-600 via-teal-600 to-cyan-600',
];

export default function MovieCatalog() {
  const [movies, setMovies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getMovies()
      .then(({ data }) => setMovies(data))
      .catch(() => setError('Failed to load movies. Is the backend running?'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-red-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center">
        <p className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-red-400">{error}</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Now Showing</h1>
        <p className="mt-1 text-zinc-400">Pick a movie and choose your showtime</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {movies.map((movie, idx) => (
          <article
            key={movie.id}
            className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/60 shadow-xl transition hover:border-zinc-700"
          >
            <div className="flex flex-col sm:flex-row">
              <div
                className={`flex h-48 shrink-0 items-center justify-center bg-gradient-to-br sm:h-auto sm:w-40 ${
                  POSTER_GRADIENTS[idx % POSTER_GRADIENTS.length]
                }`}
              >
                {movie.poster_url ? (
                  <img
                    src={movie.poster_url}
                    alt={movie.title}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <Film className="h-16 w-16 text-white/40" />
                )}
              </div>

              <div className="flex flex-1 flex-col p-5">
                <h2 className="text-xl font-bold text-white">{movie.title}</h2>

                <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-zinc-400">
                  <span className="rounded-full bg-zinc-800 px-2.5 py-0.5 text-zinc-300">
                    {movie.genre}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    {formatDuration(movie.duration_mins)}
                  </span>
                </div>

                <div className="mt-4">
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    Showtimes
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {movie.showtimes?.length ? (
                      movie.showtimes.map((st) => (
                        <Link
                          key={st.id}
                          to={`/book/${st.id}`}
                          className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-1.5 text-sm font-medium text-zinc-200 transition hover:border-red-500 hover:bg-red-600/20 hover:text-white"
                        >
                          {formatShowtime(st.start_time)}
                          <span className="ml-1.5 text-zinc-500">₹{st.base_price}</span>
                        </Link>
                      ))
                    ) : (
                      <span className="text-sm text-zinc-500">No showtimes available</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
