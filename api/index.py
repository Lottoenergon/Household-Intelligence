import os
import sys

# Ensure root directory is on the Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import Request
from fastapi.responses import JSONResponse
from backend.server import app

@app.middleware("http")
async def vercel_path_corrector(request: Request, call_next):
    if "debug" in request.query_params:
        return JSONResponse({
            "scope_path": request.scope.get("path"),
            "headers": dict(request.headers)
        })
    
    # Check headers sent by Vercel to get original requested path
    original_uri = request.headers.get("x-invoke-path") or request.headers.get("x-forwarded-uri") or request.headers.get("x-matched-path")
    if original_uri and original_uri not in ("/api/index.py", "/api/index"):
        request.scope["path"] = original_uri.split("?")[0]
    elif request.scope["path"] in ("/api/index.py", "/api/index"):
        request.scope["path"] = "/"
        
    return await call_next(request)

# Diagnostic 404 handler to see exact path passed by Vercel
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    routes = [getattr(r, "path", str(r)) for r in app.routes]
    return JSONResponse(
        status_code=404,
        content={
            "detail": f"Path not found: '{request.url.path}'",
            "scope_path": request.scope.get("path"),
            "headers": {k: v for k, v in request.headers.items() if "path" in k or "uri" in k or "url" in k}
        }
    )
