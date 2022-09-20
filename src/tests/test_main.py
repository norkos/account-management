from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sql_app.database import Base

from main import fake_secret_token
from main import app, get_db

import uuid

# stub the DB
SQLALCHEMY_DATABASE_URL = f'sqlite:///./tmp/test_{uuid.uuid4().hex}.db'
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_read_main():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {'msg': 'Hello my friend !'}


def test_create_account():
    response = client.post(
        '/accounts/',
        headers={"X-Token": fake_secret_token},
        json={'name': 'my_name', 'email': 'test@mail.com'}
    )
    assert response.status_code == 200
    assert response.json()['name'] == 'my_name'
    assert response.json()['email'] == 'test@mail.com'


def test_read_accounts_bad_token():
    response = client.post(
        '/accounts/',
        headers={"X-Token": "wrong one"},
        json={'name': 'my_name', 'email': 'test@mail.com'}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid X-Token header"}


def test_read_account():
    response = client.get(
        '/accounts/1',
        headers={"X-Token": fake_secret_token}
    )
    assert response.status_code == 200
    assert response.json() == {
        'id': 1,
        'name': 'my_name',
        'email': 'test@mail.com',
    }


def test_read_account_bad_token():
    response = client.get(
        '/accounts/1',
        headers={"X-Token": "wrong one"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid X-Token header"}


def test_read_accounts():
    client.post(
        '/accounts/',
        headers={"X-Token": fake_secret_token},
        json={'name': 'my_name', 'email': 'test2@mail.com'}
    )

    client.post(
        '/accounts/',
        headers={"X-Token": fake_secret_token},
        json={'name': 'my_name', 'email': 'test3@mail.com'}
    )

    response = client.get(
        '/accounts/',
        headers={"X-Token": fake_secret_token}
    )
    assert response.status_code == 200
    assert len(response.json()) >= 3


def test_read_accounts_bad_token():
    response = client.get(
        '/accounts/',
        headers={"X-Token": "wrong one"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid X-Token header"}



