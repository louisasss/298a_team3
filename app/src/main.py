import secrets
from fastapi import Depends, FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.db import get_db
from src.models import Shipment
from src.schemas import ShipmentCreate, ShipmentOut

app = FastAPI(title="ParcelPost")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail":jsonable_encoder(exc.errors())},
    )

@app.get("/healthz")
def healthz():
    return {"status":"ok"}

@app.get("/readyz")
def readyz(db: Session =  Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"status":"not ready"})
    return {"status":"ready"}

def generate_tracking_code() -> str:
    return "PP-" + secrets.token_hex(4).upper()


@app.post("/shipments", response_model=ShipmentOut, status_code=201)
def create_shipment(payload: ShipmentCreate, db: Session = Depends(get_db)):
    shipment = Shipment(
        tracking_code=generate_tracking_code(),
        origin=payload.origin,
        destination=payload.destination,
        status="created",
    )
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    return shipment