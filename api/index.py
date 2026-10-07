import os
import sys
import urllib.parse

# Ensure root directory is on the Python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.server import app as fastapi_app

class VercelPathMiddleware:
    def __init__(self, inner_app):
        self.inner_app = inner_app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            query_string = scope.get("query_string", b"").decode("utf-8")
            params = urllib.parse.parse_qs(query_string)
            if "__vercel_path" in params and params["__vercel_path"]:
                path = params["__vercel_path"][0]
                if not path.startswith("/"):
                    path = "/" + path
                scope["path"] = path
                scope["raw_path"] = path.encode("utf-8")
            elif scope.get("path") in ("/api/index.py", "/api/index"):
                scope["path"] = "/"
                scope["raw_path"] = b"/"
        await self.inner_app(scope, receive, send)

app = VercelPathMiddleware(fastapi_app)
