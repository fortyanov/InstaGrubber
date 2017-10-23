import operator
from utils import get_browser_followers

FILENAME = '10k_группы_m_division_instagram_00.01_21.10.2017.txt'

with open(FILENAME) as f:
    users = {}
    usernames = f.readlines()
    for username in usernames:
        username = username.rstrip()
        followers = get_browser_followers(username)
        users[username] = followers

    sorted(users.items(), key=operator.itemgetter(1))
    result = ''
    for user in users:
        result += '<a target=_blank href=https://www.instagram.com/%s>%s</a>&#9;%s&#9;<br>\n' % (
            user, user, users[user])

    with open('%s.html' % FILENAME, 'w+') as f:
        f.write(result)
