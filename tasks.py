from celery import Celery
from datetime import timedelta
from datetime import datetime
import nntplib
import smtplib
import hashlib
from email.mime.text import MIMEText

def parse_nntp_date(str):
    # Parsing the date of the post
    try:
        return datetime.strptime(str, '%a, %d %b %Y %H:%M:%S %z (%Z)')
    except:
        try:
            return datetime.strptime(str, '%a, %d %b %Y %H:%M:%S %z')
        except:
            return None

def get_encoded(str):
    try:
        str = str.encode('utf-8')
    except:
        try:
            str = str.encode('iso-8859-15', 'surrogateescape')
        except Exception as err:
            print('Error occured during encoding process.')
            print('Error: {}'.format(err))
            return None
    return str

def get_decoded(str):
    try:
        str = str.decode('utf-8')
    except:
        try:
            str = str.decode('iso-8859-15', 'surrogateescape')
        except Exception as err:
            print('Error occured during decoding process.')
            print('Error: {}'.format(err))
            return None
    return str

def hash_plz(over):
    try:
        str = over['subject'] + over['xref'] + over['message-id']
    except Exception as err:
        print('Error occured during getting keys of over dictionary.')
        print('Error: {}'.format(err))
        return None

    str = get_encoded(str)
    if str is None:
        return None

    return hashlib.sha1(str).hexdigest()

app_end_msg = "\nThis message has been sent automatically by the *BOT*."

time_delta = timedelta(seconds=60)
nb_last = 50

hosts = [
    {
        'host': 'news.epita.fr',
        'port': 119,
        'user': None,
        'pass': None,
        'ssl' : False,
        #'groups': ['iit.test'],
        'groups': ['epita.assistants', 'epita.cours.c-unix.42sh', 'epita.adm.a1', 'iit.adm', 'epita.adm.adm', 'epita.delegues', 'iit.assos.gconfs', 'epita.cours.c++.atelier',
		   'epita.cours.c++']
    }
]

mail = {
    'fromaddr': 'your_send@email.com',
    'toaddrs': ['your@email.com'],
    'host': 'host.com',
    'port':  465,
    'user': 'your@email.com',
    'pass': 'your_password',
    'ssl': True
}

class Notifier():
    def __init__(self, hosts):
        self.host = hosts[0]['host']
        self.port = hosts[0]['port']
        self.ssl = hosts[0]['ssl']
        self.user = hosts[0]['user']
        self.password = hosts[0]['pass']
        self.groups = hosts[0]['groups']
        self.last_update = datetime.utcnow() # Use UTC+0000
        self.known_ids = None

    def send_email(self, group, header, msg):

        msg = MIMEText(msg + app_end_msg)# msg_bottom)
        msg['Subject'] = header['subject'] + ' [BOT]'
        msg['From'] = header['from']# mail['fromaddr']
        msg['To'] = ", ".join(mail['toaddrs'])
#        print(header)
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


    def get_last(self, time_delta):
        try:
            # Connecting to the server...
            if self.ssl:
                co = nntplib.NNTP_SSL(self.host, self.port, self.user,
                                   self.password, timeout=10)
            else:
                co = nntplib.NNTP(self.host, self.port, self.user,
                                  self.password, timeout=10)
        except Exception as err:
            print("Can't connect to the host {}.".format(self.host))
            print("Error: {}".format(err))
            return 0

        i = 0
        if self.known_ids is None:
            self.known_ids = []
            for group in self.groups:
                print("Adding '{}' group...".format(group))
                _, _, first, last, _ = co.group(group)
                _, overviews = co.over((first, last))
                for id, over in overviews:
                    self.known_ids.append(hash_plz(over))
        else:
            for group in self.groups:
                print("Checking '{}' group...".format(group))

                # Getting infos & data from the given group
                _, _, first, last, _ = co.group(group)

                # Sending a OVER command to get last_nb posts
                resp, overviews = co.over((first, last))

                # For each post in all post...

                for id, over in overviews:
                    over_hash = hash_plz(over)
                    if over_hash is None:
                        continue

                    # If the post is not new we continue to the next post...
                    if over_hash in self.known_ids:
                        continue
                    self.known_ids.append(over_hash)

                    # Parsing the date of the post
                    post_date = parse_nntp_date(over['date'])
                    if post_date is None:
                        self.known_ids.remove(over_hash)
                        continue
                    print("Post Date = {}".format(post_date))

                    _, info = co.body(over['message-id'])
                    result = ''
                    for line in info[2]:
                        result += get_decoded(line) + '\n'
                    print(result)
                    if (self.send_email(group, over, result)):
                        self.last_update = datetime.utcnow()
                        i += 1
        co.quit()
        return i



celery = Celery('tasks')

celery.config_from_object('celeryconfig')

celery.conf.update(
    # Broker settings.
    BROKER_URL = 'sqla+sqlite:///celerydb.sqlite',

    CELERY_RESULT_BACKEND = 'db+sqlite:///results.db',

    CELERY_ANNOTATIONS = {'tasks.add': {'rate_limit': '1/s'}},

    CELERY_TASK_SERIALIZER='json',
    CELERY_ACCEPT_CONTENT=['json'],
    CELERY_RESULT_SERIALIZER='json',
    CELERY_TIMEZONE='Europe/Paris',
    CELERY_ENABLE_UTC=True,

    CELERYBEAT_SCHEDULE = {
        'every-minute': {
            'task': 'tasks.update',
            'schedule': time_delta,
        },
    }
)


news_updater = Notifier(hosts)

@celery.task
def update():
    print("Sent {} email updates.".format(news_updater.get_last(time_delta)))
