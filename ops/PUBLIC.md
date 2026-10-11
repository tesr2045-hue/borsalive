# Public URL

- **Live:** see `ops/public_url.txt` (currently an ngrok free HTTPS endpoint).
- Local app remains `http://127.0.0.1:8765`.
- Keepalive: `/workspace/ngrok-keepalive.sh` (dynamic URL; set `FORCE_NGROK_URL` only if the reserved domain is on *this* ngrok account).
- Refresh file: `ops/refresh_public_url.sh` (reads local ngrok agent API `:4040`).
- Old reserved domain `preppy-strenuous-smooth.ngrok-free.dev` belongs to a **different** ngrok account (ERR_NGROK_320) — not usable with the current authtoken.
