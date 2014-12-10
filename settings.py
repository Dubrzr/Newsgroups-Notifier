# Hosts

hosts = {
      'epita':
        {
            'host': 'news.epita.fr',
            'port': 119,
            'user': None,
            'pass': None,
            'ssl' : False,
            'timeout': 10,
            'groups': ['epita.assistants', 'epita.cours.c-unix.42sh',
                       'epita.adm.a1', 'iit.adm', 'epita.adm.adm',
                       'epita.delegues', 'iit.assos.gconfs',
                       'epita.cours.c++.atelier', 'epita.cours.c++',
                       'epita.cours.asm', 'epita.cours.compile']
        }
}

# Users

users = {
    'you':
        {
            'mail': 'your@mail.com',
            'notifs': {
                'push': True,
                'mail': True
            },
            'pushbullet_api_key': 'your_pushbullet_api_key',
            'subscriptions': [
                'epita'
            ]
        },
   }



# Tag to be added to the message object
BOT_TAG = '[BOT]'

# Message to be displayed at the end of the news.
BOT_NAME = '*BOT*'
BOT_MSG = '\nThis message has been sent automatically by the ' + BOT_NAME + '.'

# Time delta between two checks
SECONDS_DELTA = 30

# Notifications
PUSH = True
MAIL = True


# TODO: Delete personal config
# SEND MAIL Configuration
SEND_FROM_POSTER = False # Send the mail from the address of the news poster
mail = {
    'address': 'sender@mail.com',
    #'toaddrs': ['contact@juliendubiel.net', 'c.tresarrieu@gmail.com'],
    'host': 'my.host.com',
    'port':  465,
    'user': 'my_username or email',
    'pass': 'my_password',
    'ssl': True
}
