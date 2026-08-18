import { useState } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/Navbar';
import AuthModal from './pages/AuthModal';
import MovieCatalog from './pages/MovieCatalog';
import SeatBooking from './pages/SeatBooking';
import MyBookings from './pages/MyBookings';

export default function App() {
  const [authOpen, setAuthOpen] = useState(false);

  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-zinc-950 text-zinc-100">
          <Navbar onLoginClick={() => setAuthOpen(true)} />
          <main>
            <Routes>
              <Route path="/" element={<MovieCatalog />} />
              <Route
                path="/book/:showtimeId"
                element={<SeatBooking onLoginClick={() => setAuthOpen(true)} />}
              />
              <Route
                path="/my-bookings"
                element={<MyBookings onLoginClick={() => setAuthOpen(true)} />}
              />
            </Routes>
          </main>
          <AuthModal open={authOpen} onClose={() => setAuthOpen(false)} />
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}
