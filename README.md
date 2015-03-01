DESCRIPTION
===========

A tiny script to receive push notifications (using Pushbullet), and/or emails
when a news is posted on multiple predefined groups and multiple hosts.

NOTE: A new version of the notifier is available, now as a webapp [here](https://github.com/Dubrzr/NG-Notifier).

REQUIREMENTS
============

This script has been developped in Python 3.4, so you'll need python3.

As this script uses various python packages, I created a requirement file so
that you just have to type:

```
sudo pip install -r requirements.txt
```

This will find and install needed packages

USAGE
=====

```
celery worker -A tasks --loglevel=info --beat --concurrency=1
```

TODO
====

* Create classes for users, hosts, and groups to handle a db server.
* Create a HTML output for news, and give a link to this output to receiver.
