from fastapi import FastAPI, Form
from fastapi import Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from fastapi.templating import Jinja2Templates
import asyncpg
import re 
import threading
from contextlib import asynccontextmanager
import os
import time
import dotenv
import random
import concurrent.futures
from utils.customExceptions import TooManyRequestsError
from requests.exceptions import ProxyError, Timeout, SSLError, RetryError
from scrapers.singles.AetherVaultScraper import AetherVaultScraper
from scrapers.singles.AtlasScraper import AtlasScraper
from scrapers.singles.ConnectionGamesScraper import ConnectionGamesScraper
from scrapers.singles.FaceToFaceScraper import FaceToFaceScraper
from scrapers.singles.FirstPlayerScraper import FirstPlayerScraper
from scrapers.singles.FusionScraper import FusionScraper
from scrapers.singles.GauntletScraper import GauntletScraper
from scrapers.singles.Jeux3DragonsScraper import Jeux3DragonsScraper
from scrapers.singles.KanatacgScraper import KanatacgScraper
from scrapers.singles.MagicStrongholdScraper import MagicStrongholdScraper
from scrapers.singles.ManaforceScraper import ManaforceScraper
from scrapers.singles.OrchardCityScraper import OrchardCityScraper
from scrapers.singles.SequenceScraper import SequenceScraper
from scrapers.singles.TheComicHunterScraper import TheComicHunterScraper
from scrapers.singles.TopDeckHeroScraper import TopDeckHeroScraper


dotenv.load_dotenv()
proxies_env = os.environ["PROXIES"]
proxies_list = proxies_env.split(";")
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

def runScrapers(cardName):
    results = []
    results_lock = threading.Lock()  # Create a lock for thread-safe operations

    def transform(scraper):
        nonlocal results  # Reference the nonlocal results list
        try:
            temp_proxies = proxies_list.copy()
            num_failed_proxies = 0
            if scraper.usesProxies:
                print(f"scraper {scraper.website} uses proxies")
                while temp_proxies:  # try as long as there are proxies left
                    proxy = random.choice(temp_proxies)
                    try:
                        scraper.scrape(proxy)
                        scraperResults = scraper.getResults()
                        for result in scraperResults:
                            results.append(result)
                        return
                    except (
                        ProxyError,
                        Timeout,
                        SSLError,
                        RetryError,
                        TooManyRequestsError,
                    ):
                        temp_proxies.remove(
                            proxy
                        )  # remove the failing proxy from the list
                        num_failed_proxies += 1
                        print(
                            f"{num_failed_proxies} Proxy {proxy} failed for {scraper.website}"
                        )

                if not temp_proxies:
                    print(f"*** All proxies failed for {scraper.website}")
                    return
                
                for result in scraperResults:
                    with results_lock:  # Acquire the lock before modifying the list
                        results.append(result)
            else:
                # Non-proxy scraping
                scraper.scrape()
                scraperResults = scraper.getResults()
                with results_lock:  # Acquire the lock before modifying the list
                    for result in scraperResults:
                        results.append(result)
        except Exception as e:
            print("Error in search_single while trying to scrape")
            print(e)
            return

    scrapers = fetchScrapers(cardName)
    scrapers = scrapers.values()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(transform, scrapers))  # No need to store results from map

    return results

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    context = {"request": request, "message": "Hello World", "title": "Home"}
    return templates.TemplateResponse("home.html", context)


@app.post("/search", response_class=HTMLResponse)
def post_search(request: Request, content: str = Form(...)):
    shopify_results = searchShopifyInventory(content, shopifyInventoryDb)
    scraper_results = runScrapers(content)
    results = shopify_results
    results.extend(scraper_results)
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
