import smtplib
import ssl
from email.message import EmailMessage

# Define email sender and receiver
EMAIL_SENDER = 'beatnowinfo@gmail.com'
EMAIL_PASSWORD = 'qowkdxcphexfjjyr'


def send_email(email_receiver: str, subject: str, body: str):
    try:
        em = EmailMessage()
        em['From'] = EMAIL_SENDER
        em['To'] = email_receiver
        em['Subject'] = subject
        em.add_alternative(body, subtype='html')  # Use add_alternative method and specify subtype as 'html'
        # Add SSL (layer of security)
        context = ssl.create_default_context()

        # Log in and send the email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(em)  # Use send_message method instead of sendmail
            print("Correo enviado exitosamente.")  # Print statement for verification
    except Exception as e:
        print(f"Error in send_email: {e}")  # Print the error message