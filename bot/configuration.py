from sqlalchemy import create_engine, Column, Integer, String, update
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine('sqlite:///instance/conf.db')
Base = declarative_base()


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


def get(key) -> str:
    return session.query(Configuration).filter_by(key=key).first().value


def set_configuration(key, value):
    if get("maintenance_mode") is not None:
        session.execute(update(Configuration).where(Configuration.key == key).values(value=value))
    else:
        new_configuration = Configuration(key=key, value=value)

        session.add(new_configuration)

    session.commit()


def is_maintenance_mode() -> bool:
    if get("maintenance_mode") in ["true", "True", "TRUE"]:
        return True

    return False


def enable_maintenance_mode():
    set_configuration("maintenance_mode", "True")


def disable_maintenance_mode():
    set_configuration("maintenance_mode", "False")
