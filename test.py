import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.backends import default_backend
import base64

# Generate a ChaCha20 key (256 bits, 32 bytes)
encryption_key = os.urandom(32)

def encrypt_api_key(api_key, encryption_key):
    nonce = os.urandom(12)

    cipher = ChaCha20Poly1305(encryption_key)

    api_key_bytes = api_key.encode()

    ciphertext = cipher.encrypt(nonce, api_key_bytes, None)

    encrypted_data = nonce + ciphertext

    encoded_encrypted_api_key = base64.urlsafe_b64encode(encrypted_data).decode()
    
    return encoded_encrypted_api_key

def decrypt_api_key(encoded_encrypted_api_key, encryption_key):

    encrypted_data = base64.urlsafe_b64decode(encoded_encrypted_api_key.encode())


    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]

    cipher = ChaCha20Poly1305(encryption_key)

    decrypted_api_key = cipher.decrypt(nonce, ciphertext, None).decode()

    return decrypted_api_key

# Example usage
api_key = "29"

# Encrypt the API key
encrypted_key = encrypt_api_key(api_key, encryption_key)
print(f"Encrypted API Key: {encrypted_key}")
print(f"Length of Encrypted API Key: {len(encrypted_key)}")

# Decrypt the API key
decrypted_key = decrypt_api_key(encrypted_key, encryption_key)
print(f"Decrypted API Key: {int(decrypted_key)}")
