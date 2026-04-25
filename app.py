import os
from urllib import request

from fastapi import FastAPI, Request, Form, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from jinja2 import select_autoescape
from starlette.middleware.sessions import SessionMiddleware

from backend.database import Database
from backend.parse import name_to_uuid

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key= os.getenv("MONGO_URI"),
    max_age=None,  # Session will last until the browser is closed
)
database = Database()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates",
                            autoescape=select_autoescape(["html", "xml"]))


@app.get("/")
def home(request: Request, q: str = Query(None)):
    print("TEMPLATES LOADER:", templates.env.loader)
    if q:
        people = database.find_person_by_name(q.strip())
    else:
        people = database.get_all_people()
    
    return templates.TemplateResponse(
        "index.html",
        {"request": request, 
         "people": people,
         "query": q}
    )

@app.get("/people/{person_id}")
def person_page(request: Request, person_id: str):
    person = database.find_person_by_id(person_id)
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")

    parent = database.find_parent(person_id)
    parent2 = database.find_spouse(parent["spouse"]) if parent and parent.get("spouse") else None

    children = database.find_children(person_id)
    spouse = database.find_spouse(person["spouse"]) if person.get("spouse") else None

    return templates.TemplateResponse(
        "person.html",
        {
            "request": request,
            "person": person,
            "parent": parent,
            "parent2": parent2,
            "children": children,
            "spouse": spouse
        }
    )

@app.get("/people/{person_id}/edit")
def edit_person_page(request: Request, person_id: str):
    if not request.session.get("is_admin"):
        return RedirectResponse(url="/", status_code=303)
    person = database.find_person_by_id(person_id)
    person["spouse"] = database.find_spouse(person["spouse"])["name"] if person.get("spouse") else None
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
    location: str = Form(""),
    spouse: str = Form(""),
    ):
    
    
    updated_data = {"name": name}
    
    if location:
        updated_data["location"] = location

    if spouse:
        updated_data["spouse"] = spouse
        
    updated = database.update_person(
        person_id=person_id,
        updated_data=updated_data
    )

    if not updated:
        person = database.find_person_by_id(person_id)
        if person is None:
            raise HTTPException(status_code=404, detail="Person not found")

    return RedirectResponse(url=f"/people/{person_id}", status_code=303)

@app.get("/people/{person_id}/add_person")
def add_child_page(request: Request, person_id: str):    
    if not request.session.get("is_admin"):
        return RedirectResponse(url="/", status_code=303)
    
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
    spouse: str = Form(""),
    ):
    parent = database.find_person_by_id(parent_id)
    person_data = {
        "_id": name_to_uuid(name + str(parent["generation"] + 1)),
        "name": name,
        "location": location or None,
        "spouse": spouse or None,
        "generation": parent["generation"] + 1,
        "parents": [parent_id, parent["spouse"]] if parent and parent.get("spouse") else [parent_id] if parent else []
    }

    database.add_person(person_data)
    return RedirectResponse(url="/", status_code=303)

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )

@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    if database.validate_user(username, password):
        request.session["is_admin"] = True
        return RedirectResponse(url="/", status_code=303)
     
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Nom d'utilisateur ou mot de passe invalide"}
    )
