import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.health import router as health_router
from api.routes.analyze import router as analyze_router
from api.routes.transit import router as transit_router

app = FastAPI(
    title="Property Analyzer API",
    description="Barcelona property analysis — POIs, safety, valuation, composite score",
    version="0.1.0",
)

_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
_ALLOWED_ORIGINS = (
    ["*"]
    if _raw_origins.strip() == "*"
    else [o.strip() for o in _raw_origins.split(",") if o.strip()]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=_ALLOWED_ORIGINS != ["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

app.include_router(health_router)
app.include_router(analyze_router)
app.include_router(transit_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
