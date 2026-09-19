from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.db import get_db
from app.models import Person


def override_get_db():
    return MagicMock()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_create_person():
    mock_db = MagicMock()

    app.dependency_overrides[get_db] = lambda: mock_db

    person = Person(
        id=1,
        name="Ivan Ivanov",
        age=25,
        address="Moscow",
        work="Developer"
    )

    mock_db.refresh.side_effect = lambda obj: (
        setattr(obj, "id", person.id)
    )

    response = client.post(
        "/api/v1/persons",
        json={
            "name": "Ivan Ivanov",
            "age": 25,
            "address": "Moscow",
            "work": "Developer"
        }
    )

    assert response.status_code == 201
    assert response.text == ""
    assert response.headers["Location"] == "/api/v1/persons/1"

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


def test_get_person():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    person = Person(
        id=1,
        name="Ivan Ivanov",
        age=25,
        address="Moscow",
        work="Developer"
    )

    mock_db.query.return_value.filter.return_value.first.return_value = person

    response = client.get("/api/v1/persons/1")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["name"] == "Ivan Ivanov"
    assert data["age"] == 25
    assert data["address"] == "Moscow"
    assert data["work"] == "Developer"

    mock_db.query.assert_called_once_with(Person)


def test_get_person_not_found():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = client.get("/api/v1/persons/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Person not found"


def test_update_person():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    person = Person(
        id=1,
        name="Ivan Ivanov",
        age=25,
        address="Moscow",
        work="Developer"
    )

    mock_db.query.return_value.filter.return_value.first.return_value = person

    response = client.patch(
        "/api/v1/persons/1",
        json={
            "name": "Petr Petrov",
            "age": 25,
            "address": "Saint Petersburg",
            "work": "Engineer"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["name"] == "Petr Petrov"
    assert data["age"] == 30
    assert data["address"] == "Saint Petersburg"
    assert data["work"] == "Engineer"

    assert person.name == "Petr Petrov"
    assert person.age == 30
    assert person.address == "Saint Petersburg"
    assert person.work == "Engineer"

    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(person)


def test_update_person_not_found():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = client.patch(
        "/api/v1/persons/99999",
        json={
            "name": "Petr Petrov",
            "age": 30,
            "address": "Saint Petersburg",
            "work": "Engineer"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Person not found"

    mock_db.commit.assert_not_called()


def test_delete_person():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    person = Person(
        id=1,
        name="Ivan Ivanov",
        age=25,
        address="Moscow",
        work="Developer"
    )

    mock_db.query.return_value.filter.return_value.first.return_value = person

    response = client.delete("/api/v1/persons/1")

    assert response.status_code == 204
    assert response.text == ""

    mock_db.delete.assert_called_once_with(person)
    mock_db.commit.assert_called_once()


def test_delete_person_not_found():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = client.delete("/api/v1/persons/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Person not found"

    mock_db.delete.assert_not_called()
    mock_db.commit.assert_not_called()


def test_get_persons():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    persons = [
        Person(
            id=1,
            name="Ivan Ivanov",
            age=25,
            address="Moscow",
            work="Developer"
        ),
        Person(
            id=2,
            name="Petr Petrov",
            age=30,
            address="Saint Petersburg",
            work="Engineer"
        )
    ]

    mock_db.query.return_value.all.return_value = persons

    response = client.get("/api/v1/persons")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[0]["name"] == "Ivan Ivanov"
    assert data[1]["id"] == 2
    assert data[1]["name"] == "Petr Petrov"

    mock_db.query.assert_called_once_with(Person)


def test_create_person_validation_error():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db

    response = client.post(
        "/api/v1/persons",
        json={
            "age": 25,
            "address": "Moscow",
            "work": "Developer"
        }
    )

    assert response.status_code == 400

    data = response.json()

    assert data["message"] == "Invalid data"
    assert "name" in data["errors"]

    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()