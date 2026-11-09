from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db import get_db
from src.main import app


def make_client(database_url:str) -> TestClient:
    engine = create_engine(database_url)
    testing_session = sessionmaker(bind=engine)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_healthz_returns_ok():
    client = make_client("sqlite://")
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status":"ok"}

def test_readyz_returns_ready_when_db_is_reachable():
    client = make_client("sqlite://")
    response = client.get("/readyz")
    assert response.status_code == 200

def test_readyz_returns_503_when_db_is_unreachable():
    client = make_client("sqlite:////nonexistent-directory/parcelpost.db")
    response = client.get("/readyz")
    assert response.status_code == 503