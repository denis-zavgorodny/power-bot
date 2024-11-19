from sqlalchemy import create_engine, Column, Integer, String, update
from sqlalchemy.orm import declarative_base, sessionmaker

from logger import get_logger

engine = create_engine('sqlite:///instance/conf.db')
Base = declarative_base()
logger = get_logger()


class Configuration(Base):
    __tablename__ = 'configuration'

    key = Column(String, unique=False, primary_key=True, nullable=False)
    value = Column(String, unique=False, nullable=False)


# Create all tables in the engine. This is equivalent to "Create Table" statements in raw SQL.
Base.metadata.create_all(engine)

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a Session
session = Session()
print('DB created: configuration')


def get(key) -> str | None:
    value = session.query(Configuration).filter_by(key=key).first()

    if value is None:
        return None

    return session.query(Configuration).filter_by(key=key).first().value


def set_configuration(key, value):
    if get("maintenance_mode") is not None:
        logger.error(f"Updating---------:")
        session.query(Configuration).where(Configuration.key == key).update({"value": value})
    else:
        logger.error(f"Creating---------:")
        new_configuration = Configuration(key=key, value=value)

        session.add(new_configuration)

    session.commit()


def is_maintenance_mode() -> bool:
    value = get("maintenance_mode")

    if value is None:
        return False

    if value in ["true", "True", "TRUE"]:
        return True

    if value in ["false", "False", "FALSE"]:
        return False

    return True


def enable_maintenance_mode():
    set_configuration("maintenance_mode", "True")


def disable_maintenance_mode():
    set_configuration("maintenance_mode", "False")
