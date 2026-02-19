
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import logging

class EmailService:
    def __init__(self, sender_email=None, password=None):
        self.sender_email = sender_email
        self.password = password
        self.logger = logging.getLogger('EmailService')

    def send_email(self, to_email, subject, body, attachment_path=None, cc_email=None):
        if not self.sender_email or not self.password:
            self.logger.warning(f"Email credentials not provided. Skipping email to {to_email}.")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = subject

            if cc_email:
                msg['Cc'] = cc_email
                recipients = [to_email, cc_email]
            else:
                recipients = [to_email]

            msg.attach(MIMEText(body, 'plain'))

            if attachment_path:
                with open(attachment_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name="resume.txt")
                part['Content-Disposition'] = f'attachment; filename="resume.txt"'
                msg.attach(part)

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.sender_email, self.password)
            server.sendmail(self.sender_email, recipients, msg.as_string())
            server.quit()

            self.logger.info(f"Email sent successfully to {to_email} (CC: {cc_email})")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send email to {to_email}: {e}")
            return False
