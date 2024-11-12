from blacksheep import json, Request, get
from app.auth import send_welcome_email
import random





# Send verification email to user while signing up
@get('/api/v1/send/user/email/')
async def SendVerificationMailToUser(email: str):
    try:
        random_number   = random.randint(1000, 9999)
        receipient_mail = email

        body = f"""
                <html>
                <body>
                    <b>Your One-Time Password (OTP) is:</b><span>{random_number}</span>

                    <p>Please enter the above OTP in signup page to complete the email verification process.</p>
                    
                    <p><b>Best Regards,</b><br>
                    <b>Itio Innovex Pvt. Ltd.</b></p>
                </body>
                </html>
                """
        send_welcome_email(receipient_mail, "Verify Email Address", body)

        return json({
            'success': True,
            'otp': random_number
        }, 200)
    
    except Exception as e:
        return json({
            'success': False,
            'error': 'Mail send error',
            'message': f'{str(e)}'
        }, 400)

