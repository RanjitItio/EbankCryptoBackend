import os
from sqlmodel import create_engine, SQLModel, Session
from app.settings import DATABASE_URL



DATABASE_URL = DATABASE_URL


engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    create_db_and_tables()


def get_session():
    with Session(engine) as session:
        yield session


