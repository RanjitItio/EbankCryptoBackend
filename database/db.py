import os
from sqlmodel import create_engine, SQLModel, Session
# from FinanceAPI.Models import models

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession





# sqlite_file_name = "database.db"
# DATABASE_URL = f"sqlite:///{sqlite_file_name}"
password='root'
# DATABASE_URL = "postgresql+psycopg2://postgres:root@localhost:5433/fin_api"
DATABASE_URL = os.environ.get('DATABASE_URL')


engine = create_engine(DATABASE_URL, echo=True)
async_engine = create_async_engine(DATABASE_URL, echo=True, future=True)



def create_db_and_tables():
    SQLModel.metadata.create_all(async_engine)


if __name__ == "__main__":
    create_db_and_tables()


async def get_async_session():
    async with AsyncSession(async_engine) as session:
        yield session

# def get_session():
#     with Session(engine) as session:
#         yield session


# def get_session():
#     with Session(engine) as session:
#         yield session


