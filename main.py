from fastapi import FastAPI, Form
from fastapi import Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from fastapi.templating import Jinja2Templates
import asyncpg
from contextlib import asynccontextmanager
import os
import dotenv

dotenv.load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

mongo_db_conn = None
mongo_client = None
shopify_inventory_db = None
@asynccontextmanager
async def lifespan_db_connection():
    global mongo_db_conn
    global mongo_client
    global shopify_inventory_db
    mongo_client = MongoClient(os.environ["MONGO_URI"])
    mongo_db_conn = mongo_client["snapcaster"]
    shopify_inventory_db = mongo_client["shopify-inventory"]
    yield
    await mongo_db_conn.close()


def get_db_connection():
    global db_connection
    if db_connection is None:
        db_connection = asyncpg.connect(DATABASE_URL)
    return db_connection


app.mount("/static", StaticFiles(directory="static"), name="static")

mongoClient = MongoClient(os.environ["MONGO_URI"])
db = mongoClient["snapcaster"]
shopifyInventoryDb = mongoClient["shopify-inventory"]


def fetchScrapers(cardName):
    # Arrange scrapers
    gauntletScraper = GauntletScraper(cardName)
    kanatacgScraper = KanatacgScraper(cardName)
    fusionScraper = FusionScraper(cardName)
    magicStrongholdScraper = MagicStrongholdScraper(cardName)
    faceToFaceScraper = FaceToFaceScraper(cardName)
    connectionGamesScraper = ConnectionGamesScraper(cardName)
    topDeckHeroScraper = TopDeckHeroScraper(cardName)
    jeux3DragonsScraper = Jeux3DragonsScraper(cardName)
    sequenceScraper = SequenceScraper(cardName)
    atlasScraper = AtlasScraper(cardName)
    manaforceScraper = ManaforceScraper(cardName)
    firstPlayerScraper = FirstPlayerScraper(cardName)
    orchardCityScraper = OrchardCityScraper(cardName)
    aetherVaultScraper = AetherVaultScraper(cardName)
    theComicHunterScraper = TheComicHunterScraper(cardName)

    # Map scrapers to an identifier keyword
    return {
        "gauntlet": gauntletScraper,
        "kanatacg": kanatacgScraper,
        "fusion": fusionScraper,
        "magicstronghold": magicStrongholdScraper,
        "facetoface": faceToFaceScraper,
        "connectiongames": connectionGamesScraper,
        "topdeckhero": topDeckHeroScraper,
        "jeux3dragons": jeux3DragonsScraper,
        "sequencegaming": sequenceScraper,
        "atlas": atlasScraper,
        "firstplayer": firstPlayerScraper,
        "manaforce": manaforceScraper,
        "orchardcity": orchardCityScraper,
        "aethervault": aetherVaultScraper,
        "thecomichunter": theComicHunterScraper,
    }

def searchShopifyInventory(search_term, db):
    mtgSinglesCollection = db['mtgSingles']
    # case insensitive and punctuation insensitive using full text search on index "title"
    result = list(mtgSinglesCollection.find({"$text": {"$search": search_term}}))
    # drop the _id field from the result
    for item in result:
        item.pop('_id')
        item.pop('timestamp')
    return result


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    context = {"request": request, "message": "Hello World", "title": "Home"}
    return templates.TemplateResponse("home.html", context)


@app.post("/search", response_class=HTMLResponse)
def post_search(request: Request, content: str = Form(...)):
    results = searchShopifyInventory(content, shopifyInventoryDb)
    filteredResults = []
    for result in results:
        if content.lower() in result["name"].lower():
            if (
                "token" in result["name"].lower()
                and "token" not in content.lower()
                and "emblem" not in content.lower()
            ):
                continue
            elif (
                "emblem" in result["name"].lower()
                and "emblem" not in content.lower()
                and "token" not in content.lower()
            ):
                continue
            else:
                filteredResults.append(result)
        else:
            continue

    results = filteredResults


    context = {"request": request, "cards": results}
    # context = {"request": request, "content": content}
    return templates.TemplateResponse("fragments/result.html", context)
