import os
from fastapi_users.authentication import CookieTransport, JWTStrategy, AuthenticationBackend
from httpx_oauth.clients.google import GoogleOAuth2
from dotenv import load_dotenv

load_dotenv()

SECRET = os.environ.get("SECRET_KEY") or os.getenv("SECRET_KEY", "super-secret-default-key-keep-private")

cookie_transport = CookieTransport(
    cookie_name="app_token",
    cookie_max_age=3600 * 24 * 7, # 7 days
    cookie_secure=True,
    cookie_httponly=True,
    cookie_samesite="lax",
)

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600 * 24 * 7)

auth_backend = AuthenticationBackend(
    name="jwt_cookie",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

google_oauth_client = GoogleOAuth2(
    os.getenv("AUTH_GOOGLE_ID", ""),
    os.getenv("AUTH_GOOGLE_SECRET", "")
)
