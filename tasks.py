import nntplib
import hashlib
from celery import Celery
from settings import hosts, users, mail,\
    SECONDS_DELTA, BOT_TAG, BOT_MSG, SEND_FROM_POSTER, PUSH, MAIL
from datetime import timedelta
from datetime import datetime
from notifs import Notif


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


class NewsGetter:
    def __init__(self, hosts, users):
        self.hosts = hosts
        self.users = users
        self.notif_obj = Notif()
        self.known_ids = None

    def connect_to_host(self, ssl, host, port, user, password, tout):
        try:
            if ssl:
                co = nntplib.NNTP_SSL(host, port, user, password, timeout=tout)
            else:
                co = nntplib.NNTP(host, port, user, password, timeout=tout)
        except Exception as err:
            print("Can't connect to the host {}.".format(host))
            print("Error: {}".format(err))
            return None
        return co

    def get_overviews(self, co, group_name):
        try:
            # Getting infos & data from the given group
            _, _, first, last, _ = co.group(group_name)
            # Sending a OVER command to get last_nb posts
            _, overviews = co.over((first, last))
        except Exception as err:
            print("Can't get news from {} group.".format(group_name))
            print("Error: {}".format(err))
            return None
        return overviews

    def send_notifs(self, name, group, header, msg):
        m = 0
        p = 0

        m_msg = msg + ' ' + BOT_MSG
        m_subject = header['subject'] + ' ' + BOT_TAG
        m_from_addr = header['from'] if SEND_FROM_POSTER else mail['address']
        m_to_addrs = ''

        # Mails
        for _, user in self.users.items():
            #print(user)
            if not MAIL or not user['notifs']['mail']:
                pass
            for host_name in user['subscriptions']:
                if host_name == name:
                    m_to_addrs += ', ' if m_to_addrs != '' else ''
                    m_to_addrs += user['mail']
                    m += 1

        # Send email in one time
        if self.notif_obj.send_email(m_msg, m_subject, m_from_addr, m_to_addrs):
            pass
        else:
            m = 0


        for _, user in self.users.items():
            if not PUSH or not user['notifs']['push']:
                pass
            self.notif_obj.send_pushbullet(user['pushbullet_api_key'], None,
                                           m_subject, m_msg)

        return (m, p)

    def add_host(self, name, host):
        co = self.connect_to_host(
            host['ssl'],
            host['host'],
            host['port'],
            host['user'],
            host['pass'],
            host['timeout']
        )
        if not co:
            return 0
        if self.known_ids is None:
            self.known_ids = []
        for group in host['groups']:
            print("Adding '{}' group...".format(group))

            overviews = self.get_overviews(co, group)
            if not overviews:
                pass

            for id, over in overviews:
                self.known_ids.append(hash_plz(over))

    def check_host(self, name, host):
        co = self.connect_to_host(
            host['ssl'],
            host['host'],
            host['port'],
            host['user'],
            host['pass'],
            host['timeout']
        )
        if not co:
            return 0

        m = 0
        p = 0
        for group in host['groups']:
            print("Checking '{}' group...".format(group))

            overviews = self.get_overviews(co, group)
            if not overviews:
                pass

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
                print("==> Found a new message! {}".format(post_date))

                _, info = co.body(over['message-id'])
                result = ''
                for line in info[2]:
                    result += get_decoded(line) + '\n'

                tmp_m, tmp_p = self.send_notifs(name, group, over, result)
                m += tmp_m
                p += tmp_p
        co.quit()
        return (m, p)

    def check_all(self):
        m = 0
        p = 0
        if not self.known_ids:
            for name, host in self.hosts.items():
                print('Adding [{}] host.'.format(name.upper()))
                self.add_host(name, host)
        else:
            for name, host in self.hosts.items():
                print('Checking [{}] host.'.format(name.upper()))
                tmp_m, tmp_p = self.check_host(name, host)
                m += tmp_m
                p += tmp_p
        return (m, p)


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
            'schedule': timedelta(seconds=SECONDS_DELTA),
        },
    }
)


# Launching the app

news_updater = NewsGetter(hosts, users)

@celery.task
def update():
    nb_m, nb_p =  news_updater.check_all()
    print("Sent {} email updates.\nSent {} push updates.".format(nb_m, nb_p))
