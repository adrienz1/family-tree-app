from fastapi import FastAPI, Request, Form, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from database import Database

app = FastAPI()
database = Database()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
def home(request: Request, q: str = Query(None)):
    if q:
        people = database.find_person_by_name(q.strip())
        print(people)
    else:
        people = database.get_all_people()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "people": people}
    )


@app.get("/people/new")
def add_person_page(request: Request):
    return templates.TemplateResponse(
        "add_person.html",
        {"request": request}
    )


@app.post("/people/new")
def add_person(
    name: str = Form(...),
    location: str = Form(""),
    partner: str = Form(""),
):
    person_data = {
        "_id": None,
        "name": name,
        "location": location or None,
        "partner": partner or None,
        "generation": None,
        "parents": []
    }

    database.create_person(person_data)
    return RedirectResponse(url="/", status_code=303)


@app.get("/people/{person_id}")
def person_page(request: Request, person_id: str):
    person = database.find_person_by_id(person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")

    parents = database.find_parents(person_id)
    children = database.find_children(person_id)
    print(person)
    #person.partner = database.find_person_by_id(person.partner) if person.get("partner") else None
    
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