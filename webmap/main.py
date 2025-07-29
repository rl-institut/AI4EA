import os
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
import numpy as np
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import xarray as xr
import logging
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
    try:
        dataset = xr.open_dataset(dataset_path)
        datasets.append(dataset)
    except FileNotFoundError:
        logging.error(f"The file '{dataset_path}' wasn't found, please refer to the 'Local setup' section of the README")

if datasets:
    # Combine all datasets within one larger one
    dataset = xr.concat(datasets, dim="location")
else:
    dataset=None

app = FastAPI()

app.add_middleware(ProxyHeadersMiddleware)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Define allowed origins
origins = [
]

if os.getenv("ENV") != "prod":
    origins.append("http://localhost:8000")
else:
    origins.append(os.getenv("TRUSTED_HOST"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)



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


@app.get("/imprint", response_class=HTMLResponse)
async def imprint(request: Request):
    return templates.TemplateResponse("imprint.html", {"request": request})

@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})

@app.get("/geojson/nigeria", response_class=FileResponse)
async def nigeria_geojson():
    return FileResponse(GEOJSON_FILE, media_type="application/geo+json")




