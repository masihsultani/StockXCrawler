import sys
import requests
import datetime
import json
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime
import re

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 ' \
             'Safari/537.36 '
API_ENDPOINT = "https://stockx.com/api/products/"
COUNTRY = "US"
CURRENCY = "USD"


def check_request_status(status_code):
    """
    Check if request was approved
    :param status_code: status code from request
    """

    if status_code == 200:
        return True
    else:
        return False


def get_shoe_info(shoe):
    """
    Get basic information about shoe (name,releasedate,brand,model,sku,color)
    
    :param shoe: Name of the shoe given in url
    :return None
    """
    global USER_AGENT

    headers = {'User-Agent': USER_AGENT,
               'referer': 'https://google.com',
               }
    s = requests.Session()
    cookies = {"stockx_selected_locale": "en", "stockx_selected_region": "US",
               "stockx_dismiss_modal_set": "2020-05-12T18%3A27%3A45.914Z",
               "stockxdismiss_modal_expiration": "2021-05-12T18%3A27%3A45.913Z",
               "stockx_dismiss_modal": "true",
               "brwsr": "1e341001-947e-11ea-83c7-42010a246e0c"}

    results = s.get(f"https://stockx.com/{shoe}", headers=headers, cookies=cookies)
    if check_request_status(results.status_code):
        src = results.content
        soup = BeautifulSoup(src)

        x = json.loads(soup.find("div", class_="product-view").find('script', type='application/ld+json').text)
        date = datetime.strptime(x['releaseDate'], '%Y-%m-%d').date()
        shoe_data = [x['name'], date, x['brand'], x['model'], x['sku'], x['color']]

        return shoe_data
    else:
        return None


def crawl_stockx_data(shoe):
    """
    crawl all transaction data of a given shoe for stockx
    :param shoe: Name of the shoe taken from url
    :return:
    """
    global USER_AGENT
    shoe_info = get_shoe_info(shoe)
    if shoe_info is None:
        return None

    out_folder = Path()
    headers = {'User-Agent': USER_AGENT,
                'referer': 'https://google.com'}
    out_file = out_folder / f"stockx_{shoe}.csv"
    rows = []
    header = ["shoe_name", "release_date", "brand", "model", "shoe_id", "color", "time", "quantity", "shoe_size",
              "price", "currency"]

    query = API_ENDPOINT + shoe_info[
        4] + f"/activity?state=480&currency={CURRENCY}&limit=10000&page=1&sort=createdAt&order=DESC&country={COUNTRY}"

    while True:
        r = requests.get(query, headers=headers)
        if check_request_status(r.status_code):
            for x in r.json()["ProductActivity"]:
                d = datetime.fromisoformat(x["createdAt"])
                row = shoe_info + [d, x["amount"], x["shoeSize"], x["localAmount"], x["localCurrency"]]
                rows.append(row)
            if r.json()["Pagination"]["nextPage"] is None:
                break
            else:
                nextPage = re.findall('/activity.*', r.json()["Pagination"]["nextPage"])[0]
                query = API_ENDPOINT + shoe_info[4] + nextPage

    df_shoe = pd.DataFrame(data=rows, columns=header)
    df_shoe.drop_duplicates(inplace=True)
    df_shoe.to_csv(out_file, encoding="utf-8", index=None)
    return df_shoe


if __name__ == "__main__":
    shoe_name = sys.argv[1]
    df = crawl_stockx_data(shoe_name)
