from fastapi import APIRouter, Request, HTTPException
from starlette.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/auth", tags=["auth"])

oauth = OAuth()

# Check if credentials are set, otherwise warn (or fail gracefully in dev)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    print("WARNING: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set. OAuth will fail.")

oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@router.get("/login")
async def login(request: Request):
    # Dynamic Redirect URI construction
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    
    # MOCK AUTH FOR DEVELOPMENT (If no creds set)
    if not GOOGLE_CLIENT_ID or GOOGLE_CLIENT_ID == "your_client_id_here":
        # Simulate successful login
        request.session['user'] = {
            "name": "Dev User", 
            "email": "dev@localhost", 
            "picture": "https://ui-avatars.com/api/?name=Dev+User"
        }
        return RedirectResponse(url="/")

    # Ensure no trailing slash for clean concatenation
    base_url = base_url.rstrip("/")
    redirect_uri = f"{base_url}/auth/google"
    
    return await oauth.google.authorize_redirect(request, redirect_uri, prompt='select_account')

@router.get("/google")
async def auth_google(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        # Handle cases where session might be missing or token exchange fails
        raise HTTPException(status_code=400, detail=f"OAuth Error: {str(e)}")

    user = token.get('userinfo')
    if user:
        # Store user info in session
        request.session['user'] = user
        # Redirect to main dashboard
        return RedirectResponse(url="/")
    
    raise HTTPException(status_code=401, detail="Authentication failed")

@router.get("/logout")
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url="/login")
