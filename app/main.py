from fastapi import Depends, FastAPI, HTTPException, Response, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Person
from app.schemas import (
    PersonRequest,
    PersonResponse,
    PersonUpdate,
    ValidationErrorResponse,
)

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    errors = {}

    for error in exc.errors():
        field = error["loc"][-1]
        errors[str(field)] = error["msg"]

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "message": "Invalid data",
            "errors": errors
        }
    )

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="OpenAPI definition",
        version="v1",
        routes=app.routes,
    )

    for path in openapi_schema["paths"].values():
        for operation in path.values():
            if isinstance(operation, dict):
                operation.get("responses", {}).pop("422", None)

    app.openapi_schema = openapi_schema
    return openapi_schema


app.openapi = custom_openapi


@app.get(
    "/api/v1/persons/{person_id}",
    response_model=PersonResponse
)
def get_person(
    person_id: int,
    db: Session = Depends(get_db)
):
    person = db.query(Person).filter(Person.id == person_id).first()

    if person is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )

    return person


@app.patch(
    "/api/v1/persons/{person_id}",
    response_model=PersonResponse,
    responses={
        400: {
            "description": "Invalid data",
            "model": ValidationErrorResponse
        },
        404: {
            "description": "Not found Person for ID"
        }
    }
)
def update_person(
    person_id: int,
    person_request: PersonUpdate,
    db: Session = Depends(get_db)
):
    person = db.query(Person).filter(Person.id == person_id).first()

    if person is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )

    print("BEFORE:", person.id, person.name, person.age, person.address, person.work)

    person.name = person_request.name
    person.address = person_request.address

    print("AFTER SET:", person.id, person.name, person.age, person.address, person.work)

    db.commit()

    print("AFTER COMMIT:", person.id, person.name, person.age, person.address, person.work)

    db.refresh(person)

    print("AFTER REFRESH:", person.id, person.name, person.age, person.address, person.work)

    return person

@app.delete("/api/v1/persons/{person_id}")
def delete_person(
    person_id: int,
    db: Session = Depends(get_db)
):
    person = db.query(Person).filter(Person.id == person_id).first()

    if person is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )

    db.delete(person)
    db.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )


@app.get(
    "/api/v1/persons",
    response_model=list[PersonResponse]
)
def get_persons(
    db: Session = Depends(get_db)
):
    return db.query(Person).all()


@app.post(
    "/api/v1/persons",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {
            "description": "Invalid data",
            "model": ValidationErrorResponse
        }
    }
)
def create_person(
    person_request: PersonRequest,
    db: Session = Depends(get_db)
):
    person = Person(
        name=person_request.name,
        age=person_request.age,
        address=person_request.address,
        work=person_request.work
    )

    db.add(person)
    db.commit()
    db.refresh(person)

    return Response(
        status_code=status.HTTP_201_CREATED,
        headers={
            "Location": f"/api/v1/persons/{person.id}"
        }
    )