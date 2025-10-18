import os, re, html
from urllib.parse import urlparse
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
import httpx
from readability import Document
import bleach
from datetime import datetime, timezone

app = FastAPI(title="Eggcracker Text-Only Reader (Open Sources Only)")

# Env config
ALLOWLIST = set(filter(None, os.getenv("ALLOWLIST", "").split(",")))
MAX_CHARS = int(os.getenv("MAX_CHARS", "2500"))
TIMEOUT = float(os.getenv("TIMEOUT", "15.0"))

CSP = "default-src 'self'; img-src 'none'; media-src 'none'; object-src 'none'; frame-src 'none'; style-src 'unsafe-inline' 'self';"

TEXT_ONLY_TAGS = [
    'a','p','div','span','section','article','header','footer','h1','h2','h3','h4','h5','h6',
    'ul','ol','li','blockquote','pre','code','strong','em','small','time','br','hr'
]
TEXT_ONLY_ATTRS = {
    'a': ['href', 'title', 'rel'],
    '*': ['class']
}

def is_allowed(url: str) -> bool:
    if not ALLOWLIST:
        return True
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        return False
    # Strip 'www.' for comparison
    host = host.lower()
    if host.startswith("www."):
        host = host[4:]
    return any(host == d or host.endswith("." + d) for d in ALLOWLIST)

def strip_media(html_in: str) -> str:
    html_in = re.sub(r"(?is)<(img|picture|video|audio|iframe|svg|canvas|figure).*?>.*?</\1>", "", html_in)
    html_in = re.sub(r"(?is)<(img|picture|video|audio|iframe|svg|canvas|figure)[^>]*>", "", html_in)
    html_in = re.sub(r"(?i)background-image:\s*url\([^)]*\);?", "", html_in)
    return html_in

def sanitize(html_in: str) -> str:
    return bleach.clean(html_in, tags=TEXT_ONLY_TAGS, attributes=TEXT_ONLY_ATTRS, strip=True)

def excerpt(text: str, limit: int) -> str:
    import re as _re
    t = _re.sub(r"\s+", " ", text).strip()
    return (t[:limit] + "…") if len(t) > limit else t

TEMPLATE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Inter,Arial,sans-serif;line-height:1.6;max-width:880px;margin:2rem auto;padding:1rem;color:#111;background:#fff}
h1{font-size:1.5rem;margin:.25rem 0 .75rem}
.meta{color:#666;font-size:.95rem;margin-bottom:1rem}
a{color:#0a58ca;text-decoration:none}
a:hover{text-decoration:underline}
hr{border:0;border-top:1px solid #ddd;margin:1rem 0}
img,video,picture,iframe,canvas,svg,figure{display:none!important}
</style>
</head><body>
<header>
  <h1>{title}</h1>
  <p class="meta">Text-only preview • Source: <a href="{orig}">{host}</a> • Fetched: {fetched}</p>
</header>
<main>
  {content}
  <p style="margin-top:1rem"><a href="{orig}">Read the full article on {host}</a></p>
</main>
<footer class="meta" style="margin-top:2rem;border-top:1px solid #ddd;padding-top:.75rem">
  © Eggcracker — text-only preview. Media blocked by design.
</footer>
</body></html>"""

@app.get("/healthz")
def healthz():
    return PlainTextResponse("ok")

@app.get("/read", response_class=HTMLResponse)
async def read(url: str = Query(..., description="Article URL to preview")):
    if not url.startswith(("http://","https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
    if not is_allowed(url):
        raise HTTPException(status_code=403, detail="Domain not allowed")

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=TIMEOUT, headers={"User-Agent":"EggcrackerTextOnly/1.0"}) as client:
            r = await client.get(url)
            r.raise_for_status()
            html_src = r.text
    except Exception:
        raise HTTPException(status_code=502, detail="Failed to fetch source URL")

    try:
        doc = Document(html_src)
        title = doc.short_title() or "Article"
        content = doc.summary(html_partial=True)
    except Exception:
        title, content = "Article", ""

    content = strip_media(content)
    content = sanitize(content)

    # Plain-text excerpt to stay within fair use
    text_only = bleach.clean(content, tags=[], strip=True)
    text_only = excerpt(text_only, MAX_CHARS)
    para = "<p>" + html.escape(text_only).replace("\n", "</p><p>") + "</p>"

    host = urlparse(url).hostname or "source"
    host_disp = host.lower().replace("www.","")
    fetched = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    html_out = TEMPLATE.format(title=html.escape(title), orig=html.escape(url), host=html.escape(host_disp), content=para, fetched=fetched)

    return HTMLResponse(content=html_out, headers={"Content-Security-Policy": CSP})
