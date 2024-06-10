import random
import string
import time

def generate_custom_id():
    timestamp = str(int(time.time()))
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    return f"{timestamp}-{random_chars}"

custom_id = generate_custom_id()

print(custom_id)