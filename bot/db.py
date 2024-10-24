from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine('sqlite:///instance/bot.db')
Base = declarative_base()


class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, unique=True, nullable=False)
    user_name = Column(String, unique=False, nullable=True)

# Create all tables in the engine. This is equivalent to "Create Table" statements in raw SQL.
Base.metadata.create_all(engine)

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a Session
session = Session()
print('DB created: subscriptions')


# CRUD operations
def subscribe(chat_id, user_name):
    if user_name is None:
        new_user = Subscription(chat_id=chat_id, user_name=f"unknown_{chat_id}")
    else:
        new_user = Subscription(chat_id=chat_id, user_name=user_name)

    session.add(new_user)
    session.commit()


def get_all_subscribers():
    return session.query(Subscription).all()


def get_subscriber(chat_id):
    return session.query(Subscription).filter_by(chat_id=chat_id).first()


def unsubscribe(chat_id):
    user = session.query(Subscription).filter_by(chat_id=chat_id).first()
    if user:
        session.delete(user)
        session.commit()
        return True
    return False
