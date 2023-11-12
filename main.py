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

async def get_db_connection():
    global db_connection
    if db_connection is None:
        db_connection = await asyncpg.connect(DATABASE_URL)
    return db_connection

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    context = {
        "request": request,
        "message": "Hello World",
        "title": "Home"
    }
    return templates.TemplateResponse("home.html", context)


@app.post("/add", response_class=HTMLResponse)
async def post_add(request: Request, content: str = Form(...)):
    async with get_db_connection() as db:
        query = "INSERT INTO todo (content) VALUES ($1)"
        await db.execute(query, content)
    context = {"request": request, "content": content}
    return templates.TemplateResponse("todo/item.html", context)


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
