import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function login(email, password) {
  const form = new URLSearchParams();
  form.append('username', email);
  form.append('password', password);
  return api.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
}

export function register(name, email, password) {
  return api.post('/auth/register', { name, email, password });
}

export function getMovies() {
  return api.get('/movies');
}

export function getSeatLayout(showtimeId) {
  return api.get(`/showtimes/${showtimeId}/seats`);
}

export function lockSeats(showtimeId, seatIds) {
  return api.post('/bookings/lock-seats', { showtime_id: showtimeId, seat_ids: seatIds });
}

export function confirmBooking(showtimeId, seatIds) {
  return api.post('/bookings/confirm', { showtime_id: showtimeId, seat_ids: seatIds });
}

export function getMyBookings() {
  return api.get('/bookings/my');
}

export function cancelBooking(bookingId) {
  return api.post(`/bookings/${bookingId}/cancel`);
}

export default api;