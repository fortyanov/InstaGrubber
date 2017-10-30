from models import Session, User, Publication, Tag


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
    session = Session()

    # Получаем всех пользователей у которых были посты по интересующим нас тегам и возвращаем
    # их в порядке убывания подписчиков
    suitable_users = session.query(User).join(User.publications).join(Publication.tags).filter(
        Tag.name.in_(tags)).order_by(User.followers.desc()).all()

    result = ''
    for user in suitable_users:
        result += '<a target=_blank href=https://www.instagram.com/%s>%s</a>&#9;%s&#9;<br>\n' % (
            user.username, user.username, user.followers)

    with open('%s.html' % '_'.join(tags), 'w+') as f:
        f.write(result)
