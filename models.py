from sqlalchemy import DateTime
from sqlalchemy import (create_engine, Column, Date, Integer, String, Float, Table, MetaData, ForeignKey)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from utils import utc_now

engine = create_engine("sqlite:///instafuck.db", echo=True)
Base = declarative_base()

Session = sessionmaker(bind=engine)


association_table = Table(
    'association', Base.metadata,
    Column('publications_id', Integer, ForeignKey('publications.id')),
    Column('tags_id', Integer, ForeignKey('tags.id'))
)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, autoincrement=True, primary_key=True)
    instagram_pk = Column(Integer, unique=True, nullable=False)
    username = Column(String(255))
    full_name = Column(String(255))
    followers = Column(Integer)
    last_modified = Column(DateTime, onupdate=utc_now())

    def __repr__(self):
        return '%s: %s' % (self.username, self.followers)


class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String(255))


class Publication(Base):
    __tablename__ = 'publications'

    id = Column(Integer, autoincrement=True, primary_key=True)
    instagram_pk = Column(Integer, unique=True, nullable=False)
    user = Column(Integer, ForeignKey('users.id'))
    tag = relationship("Tag", secondary=association_table, backref="publications")


# В случае отсутствия важной таблицы, считаем что файл с БД отсутствует
# и потому создаем базу из моделей
if not engine.dialect.has_table(engine, 'users'):
    Base.metadata.create_all(engine)
