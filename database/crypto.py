import base64
from Crypto.Cipher import AES
from config.settings import ENCRYPTION_KEY

# Ensure your key matches exactly 32 bytes for AES-256 algorithms
SECRET_CIPHER_KEY = ENCRYPTION_KEY.encode('utf-8')[:32].ljust(32, b'\x00')

def encrypt_password(plain_text: str) -> str:
    """Transforms a plain text string into an AES-256-GCM encrypted base64 payload."""
    if not plain_text:
        return ""
    
    # Initialize cryptographic cipher engine
    cipher = AES.new(SECRET_CIPHER_KEY, AES.MODE_GCM)
    
    # Encrypt raw data frames
    ciphertext, tag = cipher.encrypt_and_digest(plain_text.encode('utf-8'))
    
    # Package Nonce, Authentication Tag, and Ciphertext together into a single transfer string
    encoded_payload = base64.b64encode(cipher.nonce + tag + ciphertext).decode('utf-8')
    return encoded_payload

def decrypt_password(cipher_text_payload: str) -> str:
    """Reverses the AES-256-GCM operation to return the plain password for automated login."""
    if not cipher_text_payload:
        return ""
    
    try:
        # Decode base64 package back into component byte structures
        raw_data = base64.b64decode(cipher_text_payload.encode('utf-8'))
        
        # GCM expects: Nonce (16 bytes), Tag (16 bytes), followed by Ciphertext payload
        nonce = raw_data[:16]
        tag = raw_data[16:32]
        ciphertext = raw_data[32:]
        
        # Re-initialize engine with extracted parameters
        cipher = AES.new(SECRET_CIPHER_KEY, AES.MODE_GCM, nonce=nonce)
        
        # Decrypt data frame and check mathematical integrity tag
        decrypted_bytes = cipher.decrypt_and_verify(ciphertext, tag)
        return decrypted_bytes.decode('utf-8')
    except Exception as error:
        # If decryption keys fail or data is manipulated, raise an error
        raise ValueError("Cryptographic core verification failure or corrupted storage token.") from error