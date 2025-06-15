from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
import io
import re
import csv
import numpy as np
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, Float, DateTime
from geoalchemy2 import Geometry
from sqlalchemy.future import select
from datetime import datetime
from pathlib import Path
import json
import xarray as xr
# from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
GEOJSON_FILE = DATA_DIR / "nigeria_admin1.geojson"

# Path to static folder
static_path = BASE_DIR / "static"

# Load dataset from static folder
datasets = []
for country_iso in ("TGO", "NGA", "NER", "BEN", "GHA"):
    dataset_path = static_path / "data" / f"{country_iso}_timeseries_daily_avg.nc"
    dataset = xr.open_dataset(dataset_path)
    datasets.append(dataset)
#dataset_path = static_path / "data" / "*.nc"



dataset = xr.concat(datasets, dim="location")

#dataset = xr.open_mfdataset(dataset_path, combine="by_coords")



app = FastAPI()

# app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(ProxyHeadersMiddleware)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

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


@app.get("/", response_class=HTMLResponse)
async def get_map(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/get_data/{selector}")
async def get_data(selector: str):
    try:
        # Slice using provided coordinate and value
        selected_data = np.round(dataset["value"].sel(location=selector).values / 1e6, 3)
        # Convert to dict for JSON serialization
        data_dict = selected_data.tolist()

        return data_dict

    except KeyError:
        raise HTTPException(status_code=404, detail="Value not found in dataset.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/csv/{region_name}")
async def download_region_csv(region_name: str):

    #TODO prevent injection with region_name by making sure it is within allowed names

    # Load the GeoJSON
    try:
        with open(GEOJSON_FILE, "r", encoding="utf-8") as f:
            geojson = json.load(f)
    except Exception as e:
        return HTMLResponse(content="Error reading GeoJSON file", status_code=500)

    # Find the region by name
    feature = next(
        (feat for feat in geojson.get("features", [])
         if feat.get("properties", {}).get("name", "").lower() == region_name.lower()),
        None
    )

    if not feature:
        return HTMLResponse(content="Region not found", status_code=404)

    props = feature.get("properties", {})

    # Convert to CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=props.keys())
    writer.writeheader()
    writer.writerow(props)
    output.seek(0)

    return StreamingResponse(output, media_type="text/csv", headers={
        "Content-Disposition": f"attachment; filename={region_name}.csv"
    })


@app.get("/imprint", response_class=HTMLResponse)
async def imprint(request: Request):
    return templates.TemplateResponse("imprint.html", {"request": request})

@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})

@app.get("/geojson/nigeria", response_class=FileResponse)
async def nigeria_geojson():
    return FileResponse(GEOJSON_FILE, media_type="application/geo+json")




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
