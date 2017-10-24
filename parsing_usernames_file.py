import operator
from utils import get_browser_followers


FILENAMES = ('asdf.txt', '10k_группы_m_division_instagram_00.01_21.10.2017.txt', '10k_конкуренты_instagram_мин2_23.txt')


def sort_by_users(filename):
    with open(filename) as f:
        users = []
        usernames = f.readlines()
        for username in usernames:
            username = username.rstrip()
            followers = get_browser_followers(username)
            users.append((username, followers))

        users.sort(key=operator.itemgetter(1), reverse=True)
        result = ''
        for user in users:
            result += '<a target=_blank href=https://www.instagram.com/%s>%s</a>    %s<br>\n' % (user[0], user[0], user[1])

        with open('%s.html' % filename, 'w+') as f:
            f.write(result)

if __name__ == '__main__':
    for filename in FILENAMES:
        sort_by_users(filename)
