```python
from sqlalchemy.future import select
from app.database.session import async_session
from app.database.models import User

async def get_user_by_username(username: str):
    async with async_session() as session:
        query = select(User).where(User.username == username)
        result = await session.execute(query)
        return result.scalar_one_or_none()
```