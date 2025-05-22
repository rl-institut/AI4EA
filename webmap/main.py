from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, Float, DateTime
from geoalchemy2 import Geometry
from sqlalchemy.future import select
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    location = Column(Geometry(geometry_type='POINT', srid=4326))
    timestamp = Column(DateTime, index=True)
    value = Column(Float)

@app.get("/data")
async def get_data(start: str, end: str):
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(SensorData).where(SensorData.timestamp.between(start_dt, end_dt))
        )
        data = result.scalars().all()
        features = []
        for d in data:
            coords = d.location.desc.split("(")[-1].strip(")").split()
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(coords[0]), float(coords[1])],
                },
                "properties": {
                    "timestamp": d.timestamp.isoformat(),
                    "value": d.value
                }
            })
        return {"type": "FeatureCollection", "features": features}
