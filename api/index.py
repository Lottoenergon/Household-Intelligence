import os
import sys

# Ensure root directory is on the Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import Request
from fastapi.responses import JSONResponse
from backend.server import app

# Diagnostic 404 handler to see exact path passed by Vercel
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    routes = [getattr(r, "path", str(r)) for r in app.routes]
    return JSONResponse(
        status_code=404,
        content={
            "detail": f"Path not found: '{request.url.path}'",
            "method": request.method,
            "routes_sample": routes[:10]
        }
    )
