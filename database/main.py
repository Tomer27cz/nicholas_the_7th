from sqlalchemy import create_engine, ForeignKey, Column, Integer, String, DateTime, Boolean, CHAR, Float, JSON
from sqlalchemy.orm import relationship, backref, sessionmaker, declarative_base, declarative_mixin, scoped_session
from sqlalchemy.ext.orderinglist import ordering_list

Base = declarative_base()

def connect_to_db(parent_dir='', first_time=False):
    """
    Connects to the database
    """
    engine = create_engine(f'sqlite:///{parent_dir}db/database.db', echo=False)

    if first_time:
        Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine, autoflush=False)
    return Session()
