import os
import sys
import traceback

# Ensure root directory is on the Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from backend.server import app
except Exception as e:
    from fastapi import FastAPI
    from fastapi.responses import PlainTextResponse
    app = FastAPI(title="Error Diagnostic Fallback")
    tb = traceback.format_exc()
    print("FATAL ERROR DURING VERCEL STARTUP:\n", tb)
    
    @app.api_route("/{full_path:path}", methods=["GET", "POST", "HEAD", "OPTIONS"])
    def catch_all(full_path: str = ""):
        dir_content = "\n".join(os.listdir(BASE_DIR) if os.path.exists(BASE_DIR) else ["BASE_DIR not found"])
        return PlainTextResponse(
            f"Vercel Serverless Function Startup Error:\n\n{tb}\n\nFiles in BASE_DIR ({BASE_DIR}):\n{dir_content}",
            status_code=500
        )
