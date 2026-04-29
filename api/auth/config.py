import os
from fastapi_users.authentication import CookieTransport, JWTStrategy, AuthenticationBackend
from httpx_oauth.clients.google import GoogleOAuth2
from dotenv import load_dotenv

load_dotenv()

_IS_PRODUCTION = os.getenv("APP_ENV") == "production"

if _IS_PRODUCTION:
    SECRET = os.environ["SECRET_KEY"]
else:
    SECRET = os.getenv("SECRET_KEY", "super-secret-default-key-keep-private")

_cookie_secure = os.getenv("COOKIE_SECURE", "true").lower() != "false"
_cookie_domain = os.getenv("COOKIE_DOMAIN") or None

cookie_transport = CookieTransport(
    cookie_name="app_token",
    cookie_max_age=3600 * 24 * 7, # 7 days
    cookie_secure=_cookie_secure,
    cookie_httponly=True,
    cookie_samesite="lax",
    cookie_domain=_cookie_domain,
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
