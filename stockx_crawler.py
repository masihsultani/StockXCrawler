import json
import requests

import pandas as pd
from pathlib import Path
import sys
from bs4 import BeautifulSoup

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


def get_shoe_info(name):
    """
    Get basic information about shoe (name,releasedate,brand,model,sku,color)

    :param name: Name of the shoe given in url
    :return None
    """
    global USER_AGENT

    headers = {'User-Agent': USER_AGENT, "referer": 'https://google.com'}
    results = requests.get(f"https://stockx.com/{name}", headers=headers)

    if check_request_status(results.status_code):
        src = results.content
        soup = BeautifulSoup(src)
        x = json.loads(soup.find("div", class_="product-view").find('script', type='application/ld+json').text)
        shoe_data = [x['name'], x['releaseDate'], x['brand'], x['model'], x['sku'], x['color']]
        return shoe_data
    else:
        return None


def crawl_stockx_data(name):
    """
    crawl all transaction data of a given shoe for stockx
    :param name: Name of the shoe taken from url
    :return:
    """
    global USER_AGENT
    shoe_info = get_shoe_info(name)
    if shoe_info is None:
        return None

    out_folder = Path()
    headers = {'User-Agent': USER_AGENT, 'referer': 'https://google.com'}
    out_file = out_folder / f"stockx_{name}.csv"

    query = API_ENDPOINT + shoe_info[4] \
            + f"/activity?state=480&currency={CURRENCY}" \
                f"&limit=100000000&page=1&sort=createdAt&order=DESC&country={COUNTRY}"
    r = requests.get(query, headers=headers)
    if check_request_status(r.status_code):
        rows = []
        header = ["shoe_name", "release_date", "brand", "model", "shoe_id", "color", "time", "quantity", "shoe_size",
                  "price", "currency"]
        for x in r.json()["ProductActivity"]:
            row = shoe_info + [x["createdAt"], x["amount"], x["shoeSize"], x["localAmount"], x["localCurrency"]]
            rows.append(row)

        df = pd.DataFrame(data=rows, columns=header)
        df.to_csv(out_file, encoding="utf-8", index=None)


if __name__ == "__main__":
    shoe_name = sys.argv[1]
    crawl_stockx_data(shoe_name)
