import secrets
from fastapi import Depends, FastAPI, Request, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.db import get_db
from src.models import Shipment, SHIPMENT_STATUSES
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


@app.get("/shipments", response_model=list[ShipmentOut])
def list_shipments(status: str | None = None, db: Session = Depends(get_db)):
    if status is not None and status not in SHIPMENT_STATUSES:
        raise HTTPException(status_code=400, detail="unknown status")
    query = db.query(Shipment)
    if status is not None:
        query = query.filter(Shipment.status == status)
    return query.order_by(Shipment.id).all()


@app.get("/shipments/{shipment_id}", response_model=ShipmentOut)
def get_shipment(shipment_id: int, db: Session = Depends(get_db)):
    shipment = db.get(Shipment, shipment_id)
    if shipment is None:
        raise HTTPException(status_code=404, detail="shipment not found")
    return shipment