
# QR Code Generator — Full‑Stack (FastAPI + Vanilla JS)

A tiny full‑stack app that generates QR codes for:
- Text
- URL / Weblink
- Phone (`tel:`)
- SMS
- Email (`mailto:`)
- Wi‑Fi (WPA/WEP/nopass)
- MeCard (contact)

Back‑end: **Python FastAPI** using **segno** (no Pillow needed).  
Front‑end: Minimal HTML/JS form with live preview + download.

---

## 1) Run locally

```bash
# From project root
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r backend/requirements.txt
uvicorn backend.app:app --reload
```

Open http://127.0.0.1:8000/ in your browser.

---

## 2) Project structure

```
qr-fullstack/
├─ backend/
│  ├─ app.py
│  └─ requirements.txt
├─ frontend/
│  └─ index.html
└─ Dockerfile
```

> The backend serves the static frontend at `/` and the API at `/api/qr`.

---

## 3) API quick reference

`POST /api/qr` — Body:
```json
{
  "type": "wifi",
  "data": { "ssid": "CafeWifi", "security": "WPA", "password": "secret", "hidden": false },
  "error": "M",
  "scale": 10,
  "border": 4,
  "format": "png",
  "dark": "#000000",
  "light": "#FFFFFF"
}
```

Types and fields:

- `text`: `{ "text": "hello" }`
- `url`: `{ "url": "example.com" }` (scheme auto‑added)
- `tel`: `{ "number": "+911234567890" }`
- `sms`: `{ "number": "+911234567890", "message": "Hi" }`
- `email`: `{ "to": "user@example.com", "subject": "...", "body": "..." }`
- `wifi`: `{ "ssid": "...", "security": "WPA|WEP|nopass", "password": "..."?, "hidden": false }`
- `mecard`: `{ "name": "Aman Ranjan", "phone": "...", "email": "...", "url": "...", "org": "...", "address": "...", "note": "..." }`

Returns: `image/png` or `image/svg+xml`.

---

## 4) Deploy options

### Option A — Docker anywhere (Render, Railway, Fly, your VPS)

1. Push this repo to GitHub.
2. The included `Dockerfile` exposes port `8000`.
3. In your platform:
   - **Render**: Create *Web Service* → From repo → Runtime: Docker → Expose port `8000`.
   - **Railway**: New Project → Deploy from Repo → Auto‑detect Dockerfile → Set `PORT=8000` if needed.
   - **Fly.io** / **VPS**: `docker build -t qr-app . && docker run -p 8000:8000 qr-app`
4. Open the service URL; the UI is served at `/`.

### Option B — Without Docker (Proc‑style)

Set the start command to:
```
uvicorn backend.app:app --host 0.0.0.0 --port 8000
```
Ensure Python 3.11+ and install `backend/requirements.txt`.

---

## 5) Publish with Git

```bash
git init
git add .
git commit -m "QR full-stack app"
git branch -M main
git remote add origin https://github.com/<your-username>/qr-fullstack.git
git push -u origin main
```

Then connect your GitHub repo to your chosen host (Render/Railway/etc.) and deploy.

---

## 6) Notes

- SVG output is perfect for print and design workflows.
- For different colorways, set `dark` and `light` (ensure contrast).
- If you only need a *static* site (no Python), you could generate QR client‑side with a JS library and host on GitHub Pages — but this project demonstrates a Python full‑stack service.
