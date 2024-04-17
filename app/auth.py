from blacksheep import Application
from app.settings import Settings
from Models.models import Users
from sqlmodel import Session, select
import jwt
import datetime
from database.db import async_engine, AsyncSession

# from database.db import engine

SECRET_KEY = "your_secret_key"  # You should keep this secret and never expose it

def generate_access_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=15),
        "iat": datetime.datetime.utcnow(),
        "type": "access"
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token.decode("utf-8")

def generate_refresh_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30),
        "iat": datetime.datetime.utcnow(),
        "type": "refresh"
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token.decode("utf-8")

def decode_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return "Token has expired"
    except jwt.InvalidTokenError:
        return "Invalid token"




async def is_authenticated(id):
    async with AsyncSession(async_engine) as session:
        user = await session.exec(select(Users).where(Users.id == id)).first()
        if user is not None:
            return user
        else:
            return False


def configure_authentication(app: Application, settings: Settings):
    """
    Configure authentication as desired. For reference:
    https://www.neoteroi.dev/blacksheep/authentication/
    """


