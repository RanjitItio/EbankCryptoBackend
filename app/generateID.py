from database.db import AsyncSession, async_engine
from sqlmodel import select
from Models.models3 import MerchantPaymentButton
from Models.crypto import CryptoSwap, CryptoExchange
import uuid
import time
import json
import base64
import hashlib
import random
import string


# Generate unique ID
def generate_unique_id():
    unique_uuid = uuid.uuid4().hex
    current_time_ms = int(time.time() * 1000)
    current_time_hex = hex(current_time_ms)[2:] 
    unique_id = unique_uuid + current_time_hex[:8] 
    return unique_id[:35]


# Encode base64
def generate_base64_encode(data):
    json_payload = json.dumps(data)
    encoded_data = base64.b64encode(json_payload.encode('utf-8'))
    encoded_str  = encoded_data.decode('utf-8')
    return encoded_str


# Decode base64
def base64_decode(encoded_data):
    decoded_data = base64.b64decode(encoded_data)
    decoded_str  = decoded_data.decode('utf-8')
    # decoded_value = json.loads(decoded_str)
    return decoded_str


def calculate_sha256_string(data):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(data.encode('utf-8'))
    return sha256_hash.hexdigest()


# Generate new unique Button ID 
async def generate_new_button_id():
    while True:
        unique_id = str(uuid.uuid4())[:30]
        async with AsyncSession(async_engine) as session:
                unique_button_id_obj = await session.execute(select(MerchantPaymentButton).where(
                    MerchantPaymentButton.button_id == unique_id
                ))
                unique_button_id = unique_button_id_obj.scalar()

                if not unique_button_id:
                    return f"button_{unique_id}"



### Generate new transaction ID for CryptoSwap Transaction
async def generate_new_swap_transaction_id():
    while True:
        unique_id = str(uuid.uuid4())[:30]

        async with AsyncSession(async_engine) as session:
                unique_transaction_id_obj = await session.execute(select(CryptoSwap).where(
                    CryptoSwap.transaction_id == unique_id
                ))
                unique_transaction_id = unique_transaction_id_obj.scalar()

                if not unique_transaction_id:
                    return unique_id
    


### Generate new transaction ID for CryptoExchange Transaction
async def generate_new_crypto_exchange_transaction_id():
    while True:
        unique_id = str(uuid.uuid4())[:30]

        async with AsyncSession(async_engine) as session:
                unique_transaction_id_obj = await session.execute(select(CryptoExchange).where(
                    CryptoExchange.transaction_id == unique_id
                ))
                unique_transaction_id = unique_transaction_id_obj.scalar()

                if not unique_transaction_id:
                    return unique_id




def generate_random_capital_word():
    letters = list(string.ascii_uppercase)

    random.shuffle(letters)
    word = letters.copy()

    while len(word) < 30:
        word.append(random.choice(string.ascii_uppercase))

    random.shuffle(word)

    return ''.join(word)


def generate_random_word(length=30):

    upper = string.ascii_uppercase
    lower = string.ascii_lowercase
    digits = string.digits
    special = string.punctuation

    characters = [random.choice(upper), random.choice(lower), random.choice(digits), random.choice(special)]

    all_characters = upper + lower + digits + special
    characters += random.choices(all_characters, k=length - len(characters))

    random.shuffle(characters)

    return ''.join(characters)

