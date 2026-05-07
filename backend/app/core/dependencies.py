from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_async_session

DBSession = Annotated[AsyncSession, Depends(get_async_session)]
