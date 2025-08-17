
import io
from typing import Literal, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from starlette.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import segno
from segno import helpers

app = FastAPI(title="QR Code Generator API", version="1.0.0")

# CORS (open by default; tighten if deploying behind a frontend on another domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QRRequest(BaseModel):
    type: Literal["text", "url", "tel", "sms", "email", "wifi", "mecard"] = Field(..., description="Kind of QR to create")
    data: Dict[str, Any] = Field(..., description="Payload for the selected type")
    error: Literal["L", "M", "Q", "H"] = Field("M", description="Error correction level")
    scale: int = Field(8, ge=1, le=50, description="Pixel size multiplier for raster formats")
    border: int = Field(4, ge=0, le=20, description="Quiet zone size in modules")
    format: Literal["png", "svg"] = Field("png", description="Output image format")
    dark: Optional[str] = Field("#000000", description="Dark color (hex or named)")
    light: Optional[str] = Field("#FFFFFF", description="Light color (hex or named)")

def make_qr(req: QRRequest):
    qrobj = None
    t = req.type
    d = req.data or {}

    # Normalize a few fields
    def require(*keys):
        missing = [k for k in keys if not d.get(k)]
        if missing:
            raise HTTPException(status_code=422, detail=f"Missing fields for {t}: {', '.join(missing)}")

    if t == "text":
        require("text")
        qrobj = segno.make(str(d["text"]), error=req.error)

    elif t == "url":
        require("url")
        url = str(d["url"])
        # Add scheme if missing
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url
        qrobj = segno.make(url, error=req.error)

    elif t == "tel":
        require("number")
        content = f"tel:{d['number']}"
        qrobj = segno.make(content, error=req.error)

    elif t == "sms":
        require("number")
        # Commonly supported formats: SMSTO:number:message  OR  sms:number?body=message
        msg = d.get("message", "")
        if msg:
            content = f"SMSTO:{d['number']}:{msg}"
        else:
            content = f"SMSTO:{d['number']}:"
        qrobj = segno.make(content, error=req.error)

    elif t == "email":
        require("to")
        from urllib.parse import urlencode, quote
        to = d["to"]
        subject = d.get("subject", "")
        body = d.get("body", "")
        params = {}
        if subject:
            params["subject"] = subject
        if body:
            params["body"] = body
        qs = ("?" + urlencode(params)) if params else ""
        content = f"mailto:{quote(to)}{qs}"
        qrobj = segno.make(content, error=req.error)

    elif t == "wifi":
        # security: 'WEP', 'WPA', or 'nopass'
        require("ssid")
        security = (d.get("security") or "WPA").upper()
        password = d.get("password", "") if security != "NOPASS" else None
        hidden = bool(d.get("hidden", False))
        qrobj = helpers.make_wifi(ssid=d["ssid"], password=password, security=security if security != "NOPASS" else None, hidden=hidden, error=req.error)

    elif t == "mecard":
        # Minimal digital contact card; widely supported by scanners
        if not (d.get("name") or (d.get("first_name") or d.get("last_name"))):
            raise HTTPException(status_code=422, detail="Provide 'name' or both 'first_name' and 'last_name' for mecard")
        name = d.get("name") or (str(d.get("last_name","")).strip() + "," + str(d.get("first_name","")).strip()).strip(",")
        phone = d.get("phone")
        email = d.get("email")
        url = d.get("url")
        note = d.get("note")
        org = d.get("org")
        adr = d.get("address")
        qrobj = helpers.make_mecard(name=name, phone=phone, email=email, url=url, org=org, adr=adr, note=note, error=req.error)

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported type: {t}")

    return qrobj

@app.post("/api/qr")
def create_qr(req: QRRequest):
    qr = make_qr(req)
    buf = io.BytesIO()
    if req.format == "png":
        qr.save(buf, kind="png", scale=req.scale, border=req.border, dark=req.dark, light=req.light)
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png", headers={"Content-Disposition": "inline; filename=qr.png"})
    elif req.format == "svg":
        qr.save(buf, kind="svg", xmldecl=False, unit="mm", border=req.border, dark=req.dark, light=req.light)
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/svg+xml", headers={"Content-Disposition": "inline; filename=qr.svg"})
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")

@app.get("/api/health")
def health():
    return {"status": "ok"}

# Serve the frontend
app.mount("/assets", StaticFiles(directory="frontend"), name="assets")

@app.get("/")
def root():
    return FileResponse("frontend/index.html")
