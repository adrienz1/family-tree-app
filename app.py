from fastapi import FastAPI, Request, Form, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from backend.database import Database
from backend.parse import name_to_uuid

app = FastAPI()
database = Database()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.cache = {}


@app.get("/")
def home(request: Request, q: str = Query(None)):
    if q:
        people = database.find_person_by_name(q.strip())
    else:
        people = database.get_all_people()
    print(people)
    print(type(people))
    
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "people": people}
    )

@app.get("/people/{person_id}")
def person_page(request: Request, person_id: str):
    person = database.find_person_by_id(person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")

    parents = database.find_parents(person_id)
    children = database.find_children(person_id)
    person["partner"] = database.find_person_by_id(person["partner"])["name"] if person.get("partner") else None

    return templates.TemplateResponse(
        "person.html",
        {
            "request": request,
            "person": person,
            "parents": parents,
            "children": children,
        }
    )


@app.get("/people/{person_id}/edit")
def edit_person_page(request: Request, person_id: str):
    person = database.find_person_by_id(person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")

    return templates.TemplateResponse(
        "edit_person.html",
        {"request": request, "person": person}
    )


@app.post("/people/{person_id}/edit")
def edit_person(
    person_id: str,
    name: str = Form(...),
    birth_date: str = Form(""),
    notes: str = Form("")
    ):
    updated = database.update_person(
        person_id=person_id,
        update_data={
            "name": name,
            "birth_date": birth_date or None,
            "notes": notes or None
        }
    )

    if not updated:
        person = database.find_person_by_id(person_id)
        if person is None:
            raise HTTPException(status_code=404, detail="Person not found")

    return RedirectResponse(url=f"/people/{person_id}", status_code=303)

@app.get("/people/{person_id}/add_person")
def add_child_page(request: Request, person_id: str):
    parent = database.find_person_by_id(person_id)
    if parent is None:
        raise HTTPException(status_code=404, detail="Parent not found")

    return templates.TemplateResponse(
        "add_person.html",
        {"request": request, "parent": parent}
    )

@app.post("/people/{parent_id}/add_person")
def add_person(
    parent_id: str,
    name: str = Form(...),
    location: str = Form(""),
    partner: str = Form(""),
    ):
    parent = database.find_person_by_id(parent_id)
    person_data = {
        "_id": name_to_uuid(name + str(parent["generation"] + 1)),
        "name": name,
        "location": location or None,
        "partner": partner or None,
        "generation": parent["generation"] + 1,
        "parents": [parent_id, parent["partner"]] if parent and parent.get("partner") else [parent_id] if parent else []
    }

    database.create_person(person_data)
    return RedirectResponse(url="/", status_code=303)
