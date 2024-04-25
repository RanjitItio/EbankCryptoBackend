# from block_io import BlockIo


# dogecoin = BlockIo('09d7-7b5c-a11d-a233','AEB8E42FA8E59592')
# litcoin = BlockIo('ee6a-5cb6-4f85-3247','AEB8E42FA8E59592')
# bitcoin = BlockIo('0d25-0de7-1052-e04a','AEB8E42FA8E59592')
# address="2MscM7HNHeedb42DVgn8b98zeynUAD6EsZv"

# transactions = dogecoin.prepare_transaction(amounts='5',from_addresses='2N5kLFSD5EJPtegdnfYFFN7BTouAbLRL3km',to_addresses=address ,priority='high')


import smtplib
from email.message import EmailMessage
from decouple import config



def send_password_reset_email(receiver: str):
    msg = EmailMessage()
    msg.set_content('This is a test!')
    msg['Subject'] = 'Test'
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
            server.login(username, 'Cywar@exe248#')
            server.send_message(msg)
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email. Error: {e}")
        
        


# Example usage:
send_password_reset_email('rishus@itio.in')
