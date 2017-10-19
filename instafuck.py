import sys
from time import sleep
from functools import wraps

# import imageio
# imageio.plugins.ffmpeg.download()

from InstagramAPI import InstagramAPI


def retry(ExceptionToCheck, tries=4, delay=300, backoff=2, logger=None):
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    msg = "%s, Ублюдки отправили в таймаут, ждем %s секунд...\n" % (str(e), mdelay)
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


class InstaFuck(InstagramAPI):
    def __init__(self, username, password, tag):
        super().__init__(username, password)
        self.tag = tag
        self.users = []
        self.login()

        publications = self.get_publications(self.tag)
        for pub in publications:
            user = pub['user']
            if user['pk'] not in [u['pk'] for u in self.users]:
                user['followers_count'] = self.get_followers(user['pk'])
                self.users.append(user)

        self.write_result_html()

    @retry(Exception, tries=999999999)
    def get_publications(self, tag):
        publications = []
        next_max_id = True
        while next_max_id:
            if next_max_id == True:
                next_max_id = ''

            _ = self.getHashtagFeed(tag, maxid=next_max_id)
            publications.extend(self.LastJson.get('items', []))
            next_max_id = self.LastJson.get('next_max_id', '')
        return publications

    @retry(Exception, tries=999999999)
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
    login = sys.argv[1]
    password = sys.argv[2]
    tags = sys.argv[3:]

    for tag in tags:
        InstaFuck('LOGIN', 'PASS', tag)
