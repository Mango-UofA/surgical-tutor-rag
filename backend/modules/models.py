from typing import Any, Dict
from app.db import get_db


def users_collection():
    return get_db()["users"]


def sessions_collection():
    return get_db()["sessions"]


def quizzes_collection():
    return get_db()["quizzes"]


async def create_user(user: Dict[str, Any]):
    col = users_collection()
    res = await col.insert_one(user)
    return res.inserted_id


async def save_session(session: Dict[str, Any]):
    col = sessions_collection()
    res = await col.insert_one(session)
    return res.inserted_id


async def save_quiz_result(result: Dict[str, Any]):
    col = quizzes_collection()
    res = await col.insert_one(result)
    return res.inserted_id
