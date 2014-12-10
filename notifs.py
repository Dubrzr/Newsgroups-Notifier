import smtplib
from settings import mail
from pushbullet import PushBullet
from email.mime.text import MIMEText


class Notif:

    def send_email(self, msg, subject, from_addr, to_addrs):
        return True
        msg = MIMEText(msg)
        msg['Subject'] = subject
        msg['From'] = from_addr
        msg['To'] = to_addrs
        try:
            if mail['ssl']:
                server = smtplib.SMTP_SSL(mail['host'],mail['port'], timeout=10)
            else:
                server = smtplib.SMTP(mail['host'], mail['port'], timeout=10)
        except Exception as err:
            print('Can\'t connect to the email server.')
            print("Error: {}".format(err))
            return False

        try:
            server.login(mail['user'], mail['pass'])
            server.send_message(msg)
            server.quit()
        except Exception as err:
            print("Can't send email...")
            print("Error: {}".format(err))
            return False
        return True

    def send_pushbullet(self, api_key, devices, subject, msg):
        print(api_key)
        pb = PushBullet(api_key)
        if not pb:
            return False
        print(pb.devices)
        for device in pb.devices:
            success, push = device.push_note(subject, msg)
            #print(success)
            #print(push)
        return True