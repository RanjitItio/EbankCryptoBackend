from cryptography.fernet import Fernet
import base64
from decouple import config
import json
import zlib


secret_key = config('SECRET_KEY_MERCHANT')
# secret_key = Fernet.generate_key()

cipher_suite = Fernet(secret_key)
hash_map = {}


def encrypt_and_encode(model_id):
    model_id_bytes = str(model_id).encode()

    encrypted_model_id = cipher_suite.encrypt(model_id_bytes)

    compressed_data = zlib.compress(encrypted_model_id)

    encoded_data = base64.urlsafe_b64encode(compressed_data).decode()

    short_hash = encoded_data[:20] 

    hash_map[short_hash] = encoded_data

    print(short_hash)

    return short_hash


def decrypt_and_decode(short_hash):
    encoded_data = hash_map.get(short_hash, None)

    if not encoded_data:
        raise ValueError("Invalid hash or hash not found")

    compressed_data = base64.urlsafe_b64decode(encoded_data.encode())

    encrypted_data = zlib.decompress(compressed_data)

    decrypted_model_id = cipher_suite.decrypt(encrypted_data).decode()

    print(decrypted_model_id)
    return int(decrypted_model_id)





