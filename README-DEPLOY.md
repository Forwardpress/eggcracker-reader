# Eggcracker Reader Proxy — Open Sources Only
A FastAPI service that fetches article URLs, extracts the main text, **removes images/iframes/media**, and serves a **short excerpt** with a link to the source — restricted to **open/public news sites**.

## What’s included
- `app.py` — text-only reader endpoint at `/read?url=...`
- `render.yaml` — Render Web Service config (Free plan) with a pre-filled ALLOWLIST of open sources
- `requirements.txt` — dependencies
- `.gitignore`
- This README

## Deploy in minutes (GitHub → Render)
1) Create a GitHub repo (e.g., `eggcracker-reader`) and upload these files (drag the *contents* of the ZIP, not the ZIP itself).

2) On Render.com → **+ New → Web Service** → select your repo.

3) Render will read `render.yaml` automatically:

   - Build: `pip install -r requirements.txt`

   - Start: `uvicorn app:app --host 0.0.0.0 --port $PORT`

   - Plan: **Free**

4) After deploy, test:

   `https://<yoursvc>.onrender.com/read?url=https%3A%2F%2Fwww.reuters.com%2Fworld%2Fus%2F...`


## (Optional) Add a custom domain

- In Render → your service → **Settings → Custom Domains** → add `reader.eggcracker.com`.

- GoDaddy → `eggcracker.com` → **DNS** → add CNAME:

  - Name: `reader`

  - Type: `CNAME`

  - Value/Target: (Render CNAME target)

- Save; after ~15–60 minutes, `https://reader.eggcracker.com` will work.


## Using it from Eggcracker (your static site)
Add a **Preview (text-only)** link next to each headline:
```
<a href="https://reader.eggcracker.com/read?url=<ENCODED_URL>">Preview (text-only)</a>
```
You can have your GitHub Action generate these automatically.


## Env vars (already set in render.yaml)
- `MAX_CHARS` — excerpt length (default 2500)
- `ALLOWLIST` — CSV of allowed hostnames (**pre-filled** with open sources)
- `TIMEOUT` — fetch timeout (seconds)


## Notes
- This service only shows a **short excerpt** and always links to the original source to stay within fair use.
- You can edit the allowed list by changing `ALLOWLIST` in `render.yaml` or in Render → **Environment**.
