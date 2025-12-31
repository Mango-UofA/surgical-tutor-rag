from motor.motor_asyncio import AsyncIOMotorClient
from .config import MONGODB_URI

client: AsyncIOMotorClient | None = None

def get_client():
    global client
    if client is None:
        client = AsyncIOMotorClient(MONGODB_URI)
    return client


def get_db(name: str = "surgical_tutor"):
    return get_client()[name]
