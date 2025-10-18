# Eggcracker Reader Proxy — Hardened v2
- Pins Python (runtime.txt) and dependency versions.
- Use Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`.
- If a deploy fails, check Logs → Build/Service and use Manual Deploy → Clear build cache & deploy.
