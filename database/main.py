from sqlalchemy import create_engine, ForeignKey, Column, Integer, String, DateTime, Boolean, CHAR, Float, JSON
from sqlalchemy.orm import relationship, backref, sessionmaker, declarative_base, declarative_mixin
from sqlalchemy.ext.orderinglist import ordering_list

Base = declarative_base()

def connect_to_db():
    """
    Connects to the database
    """
    engine = create_engine('sqlite:///db/database.db', echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()
