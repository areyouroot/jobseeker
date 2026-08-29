
import smtplib
from email.mime.text import MIMEText
import logging
import os
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('EmailValidation')

def load_credentials():
    sender_email = None
    sender_password = None

    if os.path.exists("email_credentials.txt"):
        with open("email_credentials.txt", "r") as f:
            for line in f:
                if line.startswith("SENDER_EMAIL="):
                    sender_email = line.strip().split("=", 1)[1]
                elif line.startswith("SENDER_PASSWORD="):
                    sender_password = line.strip().split("=", 1)[1]
    return sender_email, sender_password

def validate_email():
    logger.info("Starting Email Validation Check...")

    sender_email, sender_password = load_credentials()

    if not sender_email or not sender_password:
        logger.error("❌ Credentials NOT found in 'email_credentials.txt'.")
        return False

    if sender_email == "your_email@gmail.com":
        logger.error("❌ Placeholder credentials detected. Please update 'email_credentials.txt' with real values.")
        return False

    logger.info(f"Using credentials for: {sender_email}")

    try:
        # Test Connection to Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()

        # Test Login
        logger.info("Attempting to login...")
        server.login(sender_email, sender_password)
        logger.info("✅ Login successful!")

        # Test Sending
        test_recipient = "abdulfaheemasd@gmail.com"
        msg = MIMEText("This is a test email to verify job application setup.")
        msg['Subject'] = "Email Setup Validation - Job Seeker"
        msg['From'] = sender_email
        msg['To'] = test_recipient

        server.sendmail(sender_email, [test_recipient], msg.as_string())
        logger.info(f"✅ Test email sent successfully to {test_recipient}")

        server.quit()
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("❌ Authentication Failed: Please check your App Password.")
        logger.info("Ensure you are using an App Password, not your regular Google password.")
        return False
    except Exception as e:
        logger.error(f"❌ Error during email validation: {e}")
        return False

if __name__ == "__main__":
    success = validate_email()
    if not success:
        sys.exit(1)
