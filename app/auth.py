from blacksheep import Application
from app.settings import Settings
from Models.models import Users
from sqlmodel import Session, select
import jwt
import datetime
from database.db import async_engine, AsyncSession
import bcrypt
import smtplib

from decouple import config
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from blacksheep import json


# from database.db import engine
EMAIL_HOST=config('EMAIL_HOST')
EMAIL_PORT =config('EMAIL_PORT')
EMAIL_USERNAME=config('EMAIL_USERNAME')
EMAIL_PASSWORD=config('EMAIL_PASSWORD')
reset_token_secret_key = config('RESET_TOKEN_SECRET_KEY')


SECRET_KEY = "your_secret_key"  


def generate_access_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=72),
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
    

def generate_access_token_from_refresh_token(refresh_token):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload["user_id"]

        access_token = generate_access_token(user_id)
        return json({'access_token': access_token})

    except jwt.ExpiredSignatureError:
        return "Refresh token has expired"
    except jwt.InvalidTokenError:
        return "Invalid refresh token"



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



def encrypt_password_reset_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() +datetime.timedelta(hours=1),
        "iat": datetime.datetime.utcnow()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def decrypt_password_reset_token(token):
    try:
        payload = jwt.decode(token, reset_token_secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return "Token has expired"
    except jwt.InvalidTokenError:
        return "Invalid token"


def send_password_reset_email( recipient_email, subject, body):
    smtp_server = EMAIL_HOST
    smtp_port = int(EMAIL_PORT)  # For TLS

   
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USERNAME
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  
        server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USERNAME, recipient_email, msg.as_string())


def configure_authentication(app: Application, settings: Settings):
    """
    Configure authentication as desired. For reference:
    https://www.neoteroi.dev/blacksheep/authentication/
    """


