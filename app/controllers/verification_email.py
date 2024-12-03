from blacksheep import json, Request, get
from app.auth import send_welcome_email
import random





# Send verification email to user while signing up
@get('/api/v1/send/user/email/')
async def SendVerificationMailToUser(email: str):
    """
        Send a verification email to the user's email address.<br/>
        Args:<br/>
            email (str): The user's email address.<br/><br/>

        Returns:<br/>
        - JSON response with success status and OTP if email is sent successfully.<br/>
        - JSON response with error status and error message if email sending fails.<br/><br/>

        Raises:<br/>
          - JSON response with error status and error message if email sending fails.<br/>
    """
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

