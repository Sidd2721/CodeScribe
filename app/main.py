from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from app.routes import auth, upload
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="CodeScribe AI", description="Deterministic Code Analysis & Documentation Generator")

# Add SessionMiddleware for OAuth
# WARNING: Replace 'your-secret-key' with a strong random string in production
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "your-secret-key"))

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

app.include_router(auth.router)
app.include_router(upload.router)

@app.get("/login")
async def login_page(request: Request):
    # If already logged in, redirect to dashboard
    if request.session.get('user'):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/")
async def root(request: Request):
    # Protect dashboard: redirect to login if not authenticated
    if not request.session.get('user'):
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse("index.html", {"request": request, "message": "CodeScribe AI: Deterministic Code Analysis"})

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

