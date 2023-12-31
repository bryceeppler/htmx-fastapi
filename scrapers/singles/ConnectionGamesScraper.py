from bs4 import BeautifulSoup
import requests
from .Scraper import Scraper

class ConnectionGamesScraper(Scraper):
    """
    Connection games uses no api, everything is server side.
    So we need to use bs4 to scrape the data.

    The advanced search allows us to request in-stock cards only.

    https://www.theconnectiongames.com/advanced_search?utf8=%E2%9C%93&search%5Bfuzzy_search%5D=herald%27s+horn&search%5Btags_name_eq%5D=&search%5Bsell_price_gte%5D=&search%5Bsell_price_lte%5D=&search%5Bbuy_price_gte%5D=&search%5Bbuy_price_lte%5D=&search%5Bin_stock%5D=0&search%5Bin_stock%5D=1&buylist_mode=0&search%5Bcategory_ids_with_descendants%5D%5B%5D=&search%5Bcategory_ids_with_descendants%5D%5B%5D=&search%5Bsort%5D=name&search%5Bdirection%5D=ascend&commit=Search&search%5Bcatalog_group_id_eq%5D=
    https://www.theconnectiongames.com/advanced_search?utf8=%E2%9C%93&search%5Bfuzzy_search%5D=krark-clan+ironworks&search%5Btags_name_eq%5D=&search%5Bsell_price_gte%5D=&search%5Bsell_price_lte%5D=&search%5Bbuy_price_gte%5D=&search%5Bbuy_price_lte%5D=&search%5Bin_stock%5D=0&search%5Bin_stock%5D=1&buylist_mode=0&search%5Bcategory_ids_with_descendants%5D%5B%5D=&search%5Bcategory_ids_with_descendants%5D%5B%5D=&search%5Bsort%5D=name&search%5Bdirection%5D=ascend&commit=Search&search%5Bcatalog_group_id_eq%5D=
    https://www.theconnectiongames.com/advanced_search?utf8=%E2%9C%93&search%5Bfuzzy_search%5D=wear+%2F%2F+tear&search%5Btags_name_eq%5D=&search%5Bsell_price_gte%5D=&search%5Bsell_price_lte%5D=&search%5Bbuy_price_gte%5D=&search%5Bbuy_price_lte%5D=&search%5Bin_stock%5D=0&search%5Bin_stock%5D=1&buylist_mode=0&search%5Bcategory_ids_with_descendants%5D%5B%5D=&search%5Bcategory_ids_with_descendants%5D%5B%5D=&search%5Bsort%5D=name&search%5Bdirection%5D=ascend&commit=Search&search%5Bcatalog_group_id_eq%5D=
    https://www.theconnectiongames.com/advanced_search?utf8=%E2%9C%93&search%5Bfuzzy_search%5D={ }&search%5Btags_name_eq%5D=&search%5Bsell_price_gte%5D=&search%5Bsell_price_lte%5D=&search%5Bbuy_price_gte%5D=&search%5Bbuy_price_lte%5D=&search%5Bin_stock%5D=0&search%5Bin_stock%5D=1&buylist_mode=0&search%5Bcategory_ids_with_descendants%5D%5B%5D=&search%5Bcategory_ids_with_descendants%5D%5B%5D=&search%5Bsort%5D=name&search%5Bdirection%5D=ascend&commit=Search&search%5Bcatalog_group_id_eq%5D=
   
    Split cards can be searched using one or two slashes in the url, the results are the same.
    We just have to convert slashes to "%2F" in the url.

    commas: %2C
    apostrophes: %27
    spaces: +
    slashes: %2F
    dashes: included in the name, don't touch

    """
    def __init__(self, cardName):
        Scraper.__init__(self, cardName)
        self.baseUrl = 'https://www.theconnectiongames.com'
        self.website = 'connectiongames'
        self.url = self.createUrl()

    def createUrl(self):
        urlCardName = self.cardName.replace(',', '%2C').replace("'", '%27').replace(' ', '+').replace('/', '%2F')
        searchPrepend = '/advanced_search?utf8=%E2%9C%93&search%5Bfuzzy_search%5D=' 
        searchAppend = '&search%5Btags_name_eq%5D=&search%5Bsell_price_gte%5D=&search%5Bsell_price_lte%5D=&search%5Bbuy_price_gte%5D=&search%5Bbuy_price_lte%5D=&search%5Bin_stock%5D=0&search%5Bin_stock%5D=1&buylist_mode=0&search%5Bcategory_ids_with_descendants%5D%5B%5D=&search%5Bcategory_ids_with_descendants%5D%5B%5D=&search%5Bsort%5D=name&search%5Bdirection%5D=ascend&commit=Search&search%5Bcatalog_group_id_eq%5D='
        return self.baseUrl + searchPrepend + urlCardName + searchAppend

    def scrape(self):
        page = requests.get(self.url)
    
        soup = BeautifulSoup(page.content, 'html.parser')
        results = soup.find_all('li', class_='product')

        if len(results) == 0:
            return None
        
        for result in results:
            try:

                name = result.select_one('div.meta h4.name').getText()
                if "art card" in name.lower() or "art series" in name.lower():
                    continue
                # foil status is in the name as - Foil, same with Borderless
                foil = False
                borderless = False
                if ' - Foil' in name:
                    foil = True
                    name = name.replace(' - Foil', '')
                if ' - Borderless' in name:
                    borderless = True
                    name = name.replace(' - Borderless', '')

                if ' - ' in name:
                    # split card
                    name = name.split(' - ')[0]

                if self.cardName.lower() not in name.lower():
                    continue


                # get the href from the a tag with an itemprop="url" attribute
                link = self.baseUrl + result.select_one('a[itemprop="url"]')['href']
                if 'magic_singles' not in link:
                    # not a magic card
                    continue

                # get the set from div.meta span.category
                setName = result.select_one('div.meta span.category').getText()

                # weird thing where they have tournament legality in setName
                if ' (Not Tournament Legal)' in setName:
                    setName = setName.replace(' (Not Tournament Legal)', '')

                # remove any other tags we dont want
                if ' - ' in setName:
                    setName = setName.split(' - ')[0]



                # get the image src from inside from the div with image class
                image = result.select_one('div.image img')['src']


                for variant in result.select('div.variants div.variant-row'):
                    condition = variant.select_one('span.variant-short-info').getText()
                    if 'NM' in condition:
                        condition = 'NM'
                    elif 'Light' in condition:
                        condition = 'LP'
                    elif 'Moderate' in condition:
                        condition = 'MP'
                    elif 'Heav' in condition:
                        condition = 'HP'
                    elif "dmg" or "dam" in condition.lower():
                        condition = 'DMG'

                    # price comes from the span with class = "regular price"
                    price = variant.select_one('span.regular.price').getText().replace('CAD$ ', '').replace(",", "")

                    card = {
                        'name': name,
                        'set': setName,
                        'condition': condition,
                        'price': float(price),
                        'link': link,
                        'image': image,
                        'foil': foil,
                        'website': self.website
                    }

                    self.results.append(card)
            except Exception as e:
                print(f'Error scraping {self.website} for {self.cardName}: {e}')
                continue
        
