import sys
from time import sleep
from functools import wraps
import random

import requests
import json
from stem import Signal
from stem.control import Controller

# import imageio
# imageio.plugins.ffmpeg.download()

from InstagramAPI import InstagramAPI

INSTAGRAM_ACCOUNTS = (('mrslapper0_0', 'vtyn1gfyr'), ('vsegdazhivoi@protonmail.com', 'SaprunZhopa12253'), ('mutniyjoe@gmail.com', 'mutniyjoe1!'))


def retry(ExceptionToCheck, tries=4, delay=300, backoff=2, logger=None):
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    msg = "Таймаут, ждем %s секунд...\n" % mdelay
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)
        return f_retry
    return deco_retry


def renew_connection():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password='my_password')
        controller.signal(Signal.NEWNYM)


def change_ip(f):
    def f_change_ip(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        except Exception as e:
            renew_connection()
            other_accounts = [acc for acc in INSTAGRAM_ACCOUNTS if acc != (self.username, self.password)]
            random_account = random.choice(other_accounts)
            self.setUser(self, random_account[0], random_account[1])
            self.login()
            print('Смена позльзователя\nlogin: %s\nip: %s' % (random_account[0], self.s.get('http://ifconfig.me/ip').text))
        return f(self, *args, **kwargs)
    return f_change_ip


class InstaFuck(InstagramAPI):
    def __init__(self, username, password, tag, location_filter=None, tor=False):
        super().__init__(username, password)
        self.location_filter = location_filter
        self.tag = tag
        self.users = []
        self.login()

        publications = self.get_publications()

        for pub in publications:
            print('publication: %s\n' % pub)
            user = pub['user']
            if user['pk'] not in [u['pk'] for u in self.users]:
                user['followers_count'] = self.get_followers(user['pk'])
                print('user: %s    followers_count: %s\n' % (user['username'], user['followers_count']))
                self.users.append(user)

        self.write_result_html()

    def login(self, force=False, tor=False):
        if (not self.isLoggedIn or force):
            self.s = requests.Session()
            if tor:
                self.s.proxies = {
                    'http': 'socks5://127.0.0.1:9050',
                    'https': 'socks5://127.0.0.1:9050'
                }

            # if you need proxy make something like this:
            # self.s.proxies = {"https" : "http://proxyip:proxyport"}
            if (self.SendRequest('si/fetch_headers/?challenge_type=signup&guid=' + self.generateUUID(False), None, True)):

                data = {'phone_id'   : self.generateUUID(True),
                        '_csrftoken' : self.LastResponse.cookies['csrftoken'],
                        'username'   : self.username,
                        'guid'       : self.uuid,
                        'device_id'  : self.device_id,
                        'password'   : self.password,
                        'login_attempt_count' : '0'}

                if (self.SendRequest('accounts/login/', self.generateSignature(json.dumps(data)), True)):
                    self.isLoggedIn = True
                    self.username_id = self.LastJson["logged_in_user"]["pk"]
                    self.rank_token = "%s_%s" % (self.username_id, self.uuid)
                    self.token = self.LastResponse.cookies["csrftoken"]

                    self.syncFeatures()
                    self.autoCompleteUserList()
                    self.timelineFeed()
                    self.getv2Inbox()
                    self.getRecentActivity()
                    print ("Login success!\n")
                    return True

    @retry(Exception, tries=999999999, delay=30)
    @change_ip
    def get_publications(self):
        publications = []
        next_max_id = True
        while next_max_id:
            if next_max_id == True:
                next_max_id = ''

            _ = self.getHashtagFeed(self.tag, maxid=next_max_id)
            publications.extend(self.LastJson.get('items', []))
            next_max_id = self.LastJson.get('next_max_id', '')

        if self.location_filter:
            publications = [pub for pub in publications if
                            self.location_filter.items() in pub.get('location', {})]
        return publications

    @retry(Exception, tries=999999999, delay=30)
    @change_ip
    def get_followers(self, user_pk):
        followers_count = len(self.getTotalFollowers(user_pk))
        return followers_count

    def write_result_html(self):
        self.users.sort(key=lambda x: x['followers_count'], reverse=True)
        result = ''
        for user in self.users:
            result += '<a target=_blank href=https://www.instagram.com/%s>%s</a>&#9;%s&#9;<br>\n' % (
                user['username'], user['username'], user['followers_count'])

        with open('%s.html' % self.tag, 'w+') as f:
            f.write(result)


if __name__ == '__main__':
    # login = sys.argv[1]
    # password = sys.argv[2]
    # tags = sys.argv[3:]

    for tag in ['zingerclub', 'zinger']:
        print('tag: %s' % tag)
        # InstaFuck('mrslapper0_0', 'vtyn1gfyr', tag, location_filter={'city': 'Saint Petersburg, Russia'})
        InstaFuck('mrslapper0_0', 'vtyn1gfyr', tag, tor=True)
