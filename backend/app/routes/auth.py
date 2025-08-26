from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from dotenv import load_dotenv
import os
import httpx

load_dotenv()

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URI = "https://www.googleapis.com/oauth2/v2/userinfo"

@router.get("/signup")
@router.get("/signin")
def google_login():
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "access_type": "offline",
        "prompt": "consent"
    }
    url = httpx.URL(GOOGLE_AUTH_URI).copy_merge_params(params)
    return RedirectResponse(str(url))

@router.get("/callback")
async def auth_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(GOOGLE_TOKEN_URI, data=data)
        token_json = token_resp.json()
        access_token = token_json.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        userinfo_resp = await client.get(GOOGLE_USERINFO_URI, headers={"Authorization": f"Bearer {access_token}"})
        userinfo = userinfo_resp.json()
    # Here, implement user creation or lookup logic
    return JSONResponse(userinfo)
