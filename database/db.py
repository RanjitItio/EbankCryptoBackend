from sqlmodel import create_engine, SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from decouple import config




password='root'

DATABASE_URL = config('DATABASE_URL')

# engine = create_engine(DATABASE_URL)

async_engine = create_async_engine(DATABASE_URL, future=True)



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


