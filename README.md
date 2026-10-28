# Game Logic Debugging Test

A local-network quiz website for 30 beginner-friendly game logic debugging challenges. It includes an attendee view, organizer dashboard, editable question descriptions and images, answer submissions with CSV export, a 120-minute default timer, organizer start/pause controls, and fullscreen activity reporting.

## Run on Windows

1. Install Python 3.
2. Change `admin_password` in `config.json` before the event.
3. Double-click `start_test.bat`.
4. On the host laptop, open `http://localhost:8000/admin` (username `admin`; use the password in `config.json`).
5. Attendees on the same Wi-Fi open `http://HOST-IP:8000`; find the host IPv4 address with `ipconfig`.
6. Start the test from the admin dashboard when everyone is ready. The test is closed by default.

The app runs on the host laptop; GitHub Pages cannot run its Python server. Fullscreen exit and tab visibility reporting depend on browser support. Browser-level F11 fullscreen may not be verifiable, and browsers allow attendees to exit fullscreen.
