from src.db import SessionLocal
from src.models import Shipment

SEED_SHIPMENTS = [
    ("PP-9F3A1C2E", "San Jose", "Austin", "created"),
    ("PP-7B4D8E01", "Seattle", "Denver", "created"),
    ("PP-2C6F9A55", "Chicago", "New York", "picked_up"),
    ("PP-8E1B4D90", "Portland", "Phoenix", "picked_up"),
    ("PP-5A9C3F77", "Miami", "Atlanta", "in_transit"),
    ("PP-1D7E6B28", "Boston", "San Jose", "in_transit"),
    ("PP-4F2A9C61", "Dallas", "Seattle", "out_for_delivery"),
    ("PP-6C8D2E34", "Denver", "Chicago", "out_for_delivery"),
    ("PP-3B5F7A19", "Austin", "Miami", "delivered"),
    ("PP-9A4C6D82", "New York", "Boston", "delivered"),
]


def main():
    db = SessionLocal()
    try:
        existing = db.query(Shipment).count()
        if existing > 0:
            print(f"Shipments table already has {existing} rows; skipping seed")
            return
        for tracking_code, origin, destination, status in SEED_SHIPMENTS:
            db.add(
                Shipment(
                    tracking_code=tracking_code,
                    origin=origin,
                    destination=destination,
                    status=status,
                )
            )
        db.commit()
        print(f"Seeded {len(SEED_SHIPMENTS)} shipments.")
    finally:
        db.close()


if __name__ == "__main__":
    main()