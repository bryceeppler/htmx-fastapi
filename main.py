from fastapi import FastAPI, Form
from fastapi import Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from fastapi.templating import Jinja2Templates
import asyncpg
from contextlib import asynccontextmanager


app = FastAPI()
templates = Jinja2Templates(directory="templates")

DATABASE_URL = "postgresql://postgres:postgres@localhost/htmx_fastapi"
# Global variable for the database connection
db_connection = None


@asynccontextmanager
async def lifespan_db_connection():
    global db_connection
    db_connection = await asyncpg.connect(DATABASE_URL)
    yield
    await db_connection.close()


def get_db_connection():
    global db_connection
    if db_connection is None:
        db_connection = asyncpg.connect(DATABASE_URL)
    return db_connection


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    context = {"request": request, "message": "Hello World", "title": "Home"}
    return templates.TemplateResponse("home.html", context)


@app.post("/search", response_class=HTMLResponse)
async def search(request: Request, query: str = Form(...)):
    async with get_db_connection() as db:
        query = "SELECT * FROM todo WHERE content LIKE $1"
        rows = await db.fetch(query, f"%{query}%")
    context = {"request": request, "rows": rows}
    return templates.TemplateResponse("todo/list.html", context)


@app.post("/add", response_class=HTMLResponse)
def post_add(request: Request, content: str = Form(...)):
    print(content)
    cards = [
        {
            "name": "Dockside Extortionist",
            "set": "Commander 2019",
            "price": 109.99,
            "foil": False,
            "condition": "NM",
            "image": "https://cdn11.bigcommerce.com/s-641uhzxs7j/products/249632/images/272731/571bc9eb-8d13-4008-86b5-2e348a326d58__63210.1587660227.220.290.jpg?c=1",
            "link": "https://www.facetofacegames.com/dockside-extortionist-c19/",
            "website": "facetoface"
        },
        {
            "name": "Dockside Extortionist",
            "image": "https://crystal-cdn1.crystalcommerce.com/photos/7908485/medium/mtg-cb.jpg",
            "link": "https://www.gauntletgamesvictoria.ca/catalog/magic_singles-mystery_booster__the_list/dockside_extortionist__the_list/1646356",
            "set": "Mystery Booster / The List",
            "foil": False,
            "condition": "NM",
            "price": 70.0,
            "website": "gauntlet"
        },
        {
            "name": "Dockside Extortionist",
            "set": "Commander 2019",
            "condition": "NM",
            "price": 83.41,
            "link": "https://www.sequencecomics.ca/catalog/card_singles-magic_singles-commander_sets-commander_2019/dockside_extortionist/1027258",
            "image": "https://crystal-cdn4.crystalcommerce.com/photos/6522815/medium/en_2UKUpFPSWV.png",
            "foil": False,
            "website": "sequencegaming"
        },
        # ... additional card entries ...
    ]


    context = {"request": request, "cards": cards + cards}
    # context = {"request": request, "content": content}
    return templates.TemplateResponse("fragments/result.html", context)


@app.get("/edit/{item_id}", response_class=HTMLResponse)
def get_edit(request: Request, item_id: int):
    context = {"request": request, "content": "sample content"}
    return templates.TemplateResponse("todo/form.html", context)


@app.put("/edit/{item_id}", response_class=HTMLResponse)
def put_edit(request: Request, item_id: int):
    context = {"request": request, "content": "sample content"}
    return templates.TemplateResponse("todo/item.html", context)


@app.delete("/delete/{item_id}", response_class=Response)
def delete(item_id: int):
    pass
