import smtplib, ssl
import logging
import re

class ErrorMailer(object):

    def __init__(self, MY_ADDRESS, PASSWORD):

        self.smtp_server = "smtp.gmail.com"
        self.port = 587  # For starttls
        self.sender_email = MY_ADDRESS
        self.password = PASSWORD

    def send_error_log(self, receiver):
        # Create a secure SSL context
        context = ssl.create_default_context()

        # Try to log in to server and send email
        try:
            server = smtplib.SMTP(self.smtp_server, self.port)
            server.ehlo()  # Can be omitted
            server.starttls(context=context)  # Secure the connection
            server.ehlo()  # Can be omitted
            server.login(self.sender_email, self.password)
            message = self._get_log_text()
            server.sendmail(self.sender_email, receiver, message)
        except Exception as e:
            # Print any error messages to stdout
            logging.error(e)
        finally:
            server.quit()

    def _get_log_text(self):

        return_text = "Its time again for some microtop measurements!"
        return return_text

if __name__ == "__main__":
    Mailer = ErrorMailer("pythonscripterrorlog@gmail.com", "RCNNlogger")
    Mailer.send_error_log("darklefknight@googlemail.com")