import uuid
import time
import json
import base64
import hashlib


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

