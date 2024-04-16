import os
from sqlmodel import create_engine, SQLModel, Session
# from FinanceAPI.Models import models


password = 'postgres123'
DATABASE_URL = f"postgresql+psycopg2://postgres:{password}@localhost/Finance Application"
# DATABASE_URL = os.environ.get('DATABASE_URL')


engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    create_db_and_tables()


def get_session():
    with Session(engine) as session:
        yield session


