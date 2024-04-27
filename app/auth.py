from blacksheep import Application
from app.settings import Settings
from Models.models import Users
from sqlmodel import Session, select
import jwt
import datetime
from database.db import async_engine, AsyncSession
import bcrypt
import smtplib
from email.message import EmailMessage
from decouple import config


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
    return token
def generate_refresh_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30),
        "iat": datetime.datetime.utcnow(),
        "type": "refresh"
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token
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



def encrypt_password(password: str) -> str:
    
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def check_password(plain_password: str, hashed_password: str) -> bool:
    
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

reset_token_secret_key = config('RESET_TOKEN_SECRET_KEY')
def encrypt_password_reset_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() +datetime.timedelta(hours=1),
        "iat": datetime.datetime.utcnow()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
def decrypt_password_reset_token(token):
    try:
        payload = jwt.decode(token, reset_token_secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return "Token has expired"
    except jwt.InvalidTokenError:
        return "Invalid token"

def send_password_reset_email(receiver: str ,link:str):
    msg = EmailMessage()
    msg.set_content(f"this is you password reset link please click on it and reset your password: {link}")
    msg['Subject'] = 'RESET Password'
    msg['From'] = config('E-MAIL_USERNAME')
    msg['To'] = receiver

    smtp_host = config('E-MAIL_HOST')
    smtp_port = config('E-MAIL_PORT')
    username = config('E-MAIL_USERNAME')
    password = config('E-MAIL_PASSWORD')
    print(password)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email. Error: {e}")


def configure_authentication(app: Application, settings: Settings):
    """
    Configure authentication as desired. For reference:
    https://www.neoteroi.dev/blacksheep/authentication/
    """


