import sys
import random
import requests
import json

# import imageio
# imageio.plugins.ffmpeg.download()

from InstagramAPI import InstagramAPI
from consts import INSTAGRAM_ACCOUNTS
from utils import get_browser_followers


class InstaFuck(InstagramAPI):
    def __init__(self, username, password, tag, location_filter=None):
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
                # user['followers_count'] = self.get_followers(user['pk'])
                user['followers_count'] = get_browser_followers(user['username'])
                print('user: %s    followers_count: %s\n' % (user['username'], user['followers_count']))
                self.users.append(user)

        self.write_result_html()

    def login(self, force=False, proxies=None):
        if (not self.isLoggedIn or force):
            self.s = requests.Session()
            if proxies:
                self.s.proxies = proxies

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

    for tag in ['zingerclub']:
        print('tag: %s' % tag)

        account = random.choice(INSTAGRAM_ACCOUNTS)
        print('account: %s %s' % account)
        InstaFuck(account[0], account[1], tag)
