# noinspection PyUnresolvedReferences
from sqlalchemy import create_engine, ForeignKey, Column, Integer, String, DateTime, Boolean, CHAR, Float, JSON
# noinspection PyUnresolvedReferences
from sqlalchemy.orm import relationship, backref, sessionmaker, declarative_base, declarative_mixin, scoped_session, load_only
# noinspection PyUnresolvedReferences
from sqlalchemy.ext.orderinglist import ordering_list
# noinspection PyUnresolvedReferences
from sqlalchemy.exc import PendingRollbackError
# noinspection PyUnresolvedReferences
from sqlalchemy.orm.exc import ObjectDeletedError

Base = declarative_base()

def get_base_metadata():
    # import all files with database tables - this is needed for alembic
    # noinspection PyUnresolvedReferences
    import classes.data_classes as data_classes
    # noinspection PyUnresolvedReferences
    import classes.video_class as video_class

    return Base.metadata

def connect_to_db(first_time=False):
    """
    Connects to the database
    """
    engine = create_engine(f'sqlite:///./db/database.db', echo=False)

    if first_time:
        Base.metadata.create_all(bind=engine)

    session = sessionmaker(bind=engine, autoflush=False)
    return session()
