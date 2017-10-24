import re
import sys
import hashlib
from time import sleep
import random
from functools import wraps

import datetime
import requests
import browser_cookie3
from stem import Signal
from stem.control import Controller
from consts import INSTAGRAM_ACCOUNTS, PROXIES
from exceptions import DropConnectionExc


def renew_connection():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate(password='vtyn1gfyr')
        controller.signal(Signal.NEWNYM)


def retry(ExceptionToCheck, tries=4, delay=300, backoff=1, logger=None):
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


def change_ip(f):
    def f_change_ip(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        except DropConnectionExc as e:
            # renew_connection()
            other_accounts = [acc for acc in INSTAGRAM_ACCOUNTS if acc != (self.username, self.password)]
            random_account = random.choice(other_accounts)
            username = random_account[0]
            password = random_account[1]

            other_proxies = [p for p in PROXIES if p != self.s.proxies.get('http')]
            random_proxy = random.choice(other_proxies)
            proxies = {
                'http': random_proxy,
                'https': random_proxy
            }

            m = hashlib.md5()
            m.update(username.encode('utf-8') + password.encode('utf-8'))
            self.device_id = self.generateDeviceId(m.hexdigest())
            self.setUser(username, password)
            self.isLoggedIn = False
            self.LastResponse = None
            self.login(proxies=proxies)
            print('Смена позльзователя\nlogin: %s\nip: %s' % (username, self.s.get('http://ifconfig.me/ip').text))

        except Exception as e:
            self.write_result_html()
            sys.exit(-1)

        return f(self, *args, **kwargs)
    return f_change_ip


@retry(Exception, tries=999999999, delay=300)
def get_browser_followers(username):
    # cookies = browser_cookie3.chrome(cookie_file='~/.config/chromium/Default/Cookies')
    cookies = browser_cookie3.firefox()
    response = requests.get('https://www.instagram.com/%s/' % username, cookies=cookies)
    response_text = response.text
    reg_expr = r'(\d+(?:[.,]\d*)?)[k]* Followers'

    if '<h2>Sorry, this page isn&#39;t available.</h2>' in response_text:
        followers_count = -1
    else:
        followers_count = re.findall(reg_expr, response_text)[0].replace(',', '.')

        if '.' in followers_count:
            if followers_count[-1] == 'k':
                followers_count = followers_count[:-1]
            followers_count = float(followers_count) * 1000

    print('User: %s  Followers: %s' % (username, followers_count))
    return int(followers_count)


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()

        return instance, True


def utc_now():
    return datetime.datetime.now(tz=datetime.timezone.utc)
