import secrets

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.db import get_db
from src.failure import maybe_inject_failure
from src.metrics import VERSION, MetricsMiddleware, metrics_response
from src.models import NEXT_STATUS, SHIPMENT_STATUSES, Shipment
from src.schemas import ShipmentCreate, ShipmentOut, ShipmentStatusUpdate

app = FastAPI(title="ParcelPost")
app.add_middleware(MetricsMiddleware)


@app.middleware("http")
async def add_version_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-App-Version"] = VERSION
    return response


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
        # Any failure means not ready: answer 503, never leak a 500.
    except Exception: # noqa: BLE001
        return JSONResponse(status_code=503, content={"status":"not ready"})
    return {"status":"ready"}


@app.get("/metrics")
def metrics():
    return metrics_response()

@app.get("/version")
def version():
    return {"version": VERSION}


def generate_tracking_code() -> str:
    return "PP-" + secrets.token_hex(4).upper()


@app.post("/shipments", response_model=ShipmentOut, status_code=201)
def create_shipment(request: Request, payload: ShipmentCreate, db: Session = Depends(get_db)):
    maybe_inject_failure(request)
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
def list_shipments(request: Request, status: str | None = None, db: Session = Depends(get_db)):
    maybe_inject_failure(request)
    if status is not None and status not in SHIPMENT_STATUSES:
        raise HTTPException(status_code=400, detail="unknown status")
    query = db.query(Shipment)
    if status is not None:
        query = query.filter(Shipment.status == status)
    return query.order_by(Shipment.id).all()


@app.get("/shipments/{shipment_id}", response_model=ShipmentOut)
def get_shipment(request: Request, shipment_id: int, db: Session = Depends(get_db)):
    maybe_inject_failure(request)
    shipment = db.get(Shipment, shipment_id)
    if shipment is None:
        raise HTTPException(status_code=404, detail="shipment not found")
    return shipment


@app.patch("/shipments/{shipment_id}/status", response_model=ShipmentOut)
def update_shipment_status(
    request: Request, 
    shipment_id: int, payload: ShipmentStatusUpdate, db: Session = Depends(get_db)
):
    maybe_inject_failure(request)
    if payload.status not in SHIPMENT_STATUSES:
        raise HTTPException(status_code=400, detail="unknown status")
    shipment = db.get(Shipment, shipment_id)
    if shipment is None:
        raise HTTPException(status_code=404, detail="shipment not found")
    if NEXT_STATUS.get(shipment.status) != payload.status:
        raise HTTPException(status_code=409, detail="illegal status transition")
    shipment.status = payload.status
    db.commit()
    db.refresh(shipment)
    return shipment
