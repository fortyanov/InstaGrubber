from models import Session, User


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()

        return instance, True


def write_to_html(tags):
    # self.users.sort(key=lambda x: x['followers_count'], reverse=True)
    # result = ''
    # for user in self.users:
    #     result += '<a target=_blank href=https://www.instagram.com/%s>%s</a>&#9;%s&#9;<br>\n' % (
    #         user['username'], user['username'], user['followers_count'])
    #
    # with open('%s.html' % self.tag, 'w+') as f:
    #     f.write(result)

    session = Session()
    # session.query(Tag).first().publications
    # session.query(Publication).first().tags
    # session.query(User).first().publications
    pass