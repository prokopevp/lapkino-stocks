from sqlalchemy import create_engine, exists
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, Session

engine = create_engine(f'sqlite:////root/lapkino-stocks/data.db', echo=True)

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    chat_id: Mapped[str] = mapped_column(primary_key=True)

def start_db():
    Base.metadata.create_all(engine)


def create_user(chat_id):
    with Session(engine) as session:
        new_user = User(chat_id=chat_id)
        session.add(new_user)
        session.commit()


def check_user(chat_id):
    with Session(engine) as session:
        return session.query(exists().where(User.chat_id==chat_id)).scalar()
