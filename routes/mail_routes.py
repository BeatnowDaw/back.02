import bcrypt
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from config.mail import send_email
from config.security import get_current_user, get_user_id
from dotenv import load_dotenv
from model.user_shemas import NewUser, User
import random
from config.db import mail_code_collection, password_reset_collection
from model.shemas import Mail_Code, PasswordResetRequest

load_dotenv()

router = APIRouter()

def generate_six_digit_number():
    number = random.randrange(0, 999999)
    return str(number).zfill(6)


async def create_and_save_confirmation_code(user: User):
    confirmation_code = generate_six_digit_number()
    # Hash the password before saving it
    code_hash = bcrypt.hashpw(confirmation_code.encode('utf-8'), bcrypt.gensalt())
    user_id=await get_user_id(user.username)
    mail_code=Mail_Code(user_id=user_id,code=code_hash)
    await mail_code_collection.delete_many({"user_id": user_id})
    result = await mail_code_collection.insert_one(mail_code.dict())
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Failed to save code")
    return confirmation_code

@router.post("/send-confirmation/")
async def send_confirmation(background_tasks: BackgroundTasks,user: NewUser = Depends(get_current_user)):
    try:
        confirmation_code = await create_and_save_confirmation_code(user)
        subject = "Confirmación de Registro"
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Email Verification</title>
        </head>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5;">
            <div class="container" style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div class="header">
                    <img src="http://172.203.251.28/res/logo.png" alt="BeatNow Logo">
                    <h1>Verify your email address</h1>
                </div>
                <div class="body">
                    <p>Hola {user.username},</p>
                    <p>You need to verify your email address to continue using your Twilio account. Enter the following code to verify your email address:</p>
                    <h2 style="text-align: center;">{confirmation_code}</h2>
                    <p>In case you were not trying to access your Twilio Account & are seeing this email, please follow the instructions below:</p>
                    <ul>
                        <li>Reset your BeatNow password.</li>
                        <li>Check if any changes were made to your account & user settings. If yes, revert them immediately.</li>
                    </ul>
                    <p>Thank You!</p>
                    <p>BeatNow Team</p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 BeatNow. All Rights Reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """


        send_email(user.email, subject, html_content)
        return {"message": "Correo de confirmación enviado"}
    except Exception as e:
        print(f"Error: {e}")  # Print the error message
    return {"error": str(e)}

def generate_reset_token():
    token = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=32))
    return token

async def create_and_save_reset_request(user: User):
    reset_token = generate_reset_token()
    user_id = await get_user_id(user.username)
    reset_request = PasswordResetRequest(user_id=user_id, reset_token=reset_token)
    result = await password_reset_collection.insert_one(reset_request.dict())
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Failed to save reset request")
    return reset_token

@router.post("/send-password-reset/")
async def send_password_reset(background_tasks: BackgroundTasks, user: User = Depends(get_current_user)):
    try:
        reset_token = await create_and_save_reset_request(user)
        subject = "Password Reset"
        reset_link = f"https://example.com/reset-password?token={reset_token}"  # Replace with your actual reset link
        html_content = f"""
        <html>
        <body>
            <h1>Password Reset</h1>
            <p>Hello {user.username},</p>
            <p>We received a request to reset your password. If this was you, please click the following link to reset your password:</p>
            <a href="{reset_link}">Reset Password</a>
            <p>If you didn't request a password reset, you can safely ignore this email.</p>
            <p>Thank you!</p>
        </body>
        </html>
        """
        send_email(user.email, subject, html_content)
        return {"message": "Password reset email sent"}
    except Exception as e:
        print(f"Error: {e}")  # Print the error message
        raise HTTPException(status_code=500, detail="Failed to send password reset email")
        