import sys
import random
import datetime

import requests
import json

# import imageio
# imageio.plugins.ffmpeg.download()

from InstagramAPI import InstagramAPI
from utils import get_browser_followers
from db_utils import get_or_create, write_to_html
from consts import INSTAGRAM_ACCOUNTS, TAGS
from models import Session, User, Tag, Publication


class InstaGrubber(InstagramAPI):
    def __init__(self, username, password, tag, location_filter=None):
        super().__init__(username, password)
        self.location_filter = location_filter
        self.tag = tag
        self.login()
        self.db_session = Session()
        self.today = datetime.date.today()

        publications = self.get_publications()

        for publication in publications:
            self.write_to_db(user=publication['user'], tag=self.tag, publication=publication)

    def login(self, force=False, proxies=None):
        if not self.isLoggedIn or force:
            self.s = requests.Session()
            if proxies:
                self.s.proxies = proxies

            if self.SendRequest('si/fetch_headers/?challenge_type=signup&guid=' + self.generateUUID(False), None, True):
                data = {
                    'phone_id': self.generateUUID(True),
                    '_csrftoken': self.LastResponse.cookies['csrftoken'],
                    'username': self.username,
                    'guid': self.uuid,
                    'device_id': self.device_id,
                    'password': self.password,
                    'login_attempt_count': '0'
                }

                if self.SendRequest('accounts/login/', self.generateSignature(json.dumps(data)), True):
                    self.isLoggedIn = True
                    self.username_id = self.LastJson["logged_in_user"]["pk"]
                    self.rank_token = "%s_%s" % (self.username_id, self.uuid)
                    self.token = self.LastResponse.cookies["csrftoken"]

                    self.syncFeatures()
                    self.autoCompleteUserList()
                    self.timelineFeed()
                    self.getv2Inbox()
                    self.getRecentActivity()
                    print("Login success!\n")
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

    def write_to_db(self, user, tag, publication, actual_days_range=100):
        db_user, db_user_created = get_or_create(self.db_session, User, instagram_pk=user['pk'])
        if db_user_created or db_user.last_modified==None \
                or (self.today - db_user.last_modified.date() > datetime.timedelta(days=actual_days_range)):
            db_user.username = user['username']
            db_user.full_name = user['full_name']
            db_user.followers = get_browser_followers(user['username'])
            print('Создание/Обновление пользователя: %s %s %s\n' % (db_user.username, db_user.full_name, db_user.followers))

        db_publication, db_publication_created = get_or_create(self.db_session, Publication, instagram_pk=publication['pk'])
        if db_publication_created:
            db_publication.user_id = db_user.id

        if db_publication.last_modified==None \
                or (self.today - db_publication.last_modified.date() > datetime.timedelta(days=actual_days_range)):
            db_publication.like_count = publication['like_count']
            db_publication.link_code = publication['code']
            db_publication.device_timestamp = datetime.datetime.fromtimestamp(
                int(str(publication['device_timestamp'])[:10])
            )
            print('Создание/Обновление публикации: %s %s %s\n' % (db_publication.link_code, db_user.full_name, db_publication.like_count))

        db_tag, db_tag_created = get_or_create(self.db_session, Tag, name=tag)
        if db_tag_created:
            db_tag.publications.append(db_publication)
            print('Создание тега: %s' % tag)

        self.db_session.commit()

    def __exit__(self):
        self.db_session.close()


if __name__ == '__main__':
    for tag in TAGS:
        print('tag: %s' % tag)

        account = random.choice(INSTAGRAM_ACCOUNTS)
        print('account: %s %s' % account)

        InstaGrubber(account[0], account[1], tag)

    write_to_html(TAGS)

