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

