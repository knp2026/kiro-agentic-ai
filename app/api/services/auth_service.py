```python
from app.database.repositories import user_repository
from app.utils.security import hash_password, verify_password, create_access_token

async def authenticate_user(username: str, password: str):
    user = await user_repository.get_user_by_username(username)
    if user and verify_password(password, user.hashed_password):
        return user
    return None

def generate_access_token(user):
    return create_access_token(user.id)
```