from flask_jwt_extended import get_jwt_identity
from backend.database import db
from backend.models.user import User
from sqlalchemy import select


def get_current_user():
    user_id = int(get_jwt_identity())

    user = db.session.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()

    if not user:
        return None

    return user

   
    return user