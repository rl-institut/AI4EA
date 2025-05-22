import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from main import SensorData, Base, DATABASE_URL

async def seed():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        now = datetime.utcnow()
        for i in range(10):
            point = from_shape(Point(-120 + i, 35 + i), srid=4326)
            data = SensorData(
                location=point,
                timestamp=now - timedelta(days=i),
                value=20.0 + i
            )
            session.add(data)
        await session.commit()

asyncio.run(seed())
