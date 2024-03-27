import json
from datetime import datetime
import logging
import requests
from bs4 import BeautifulSoup
import os
import concurrent.futures

CONFIG_JSON = 'config/wk_config.json'
config = json.load(open(file=CONFIG_JSON, encoding='utf-8'))
wiki_path = config['path']
data_path = config['data_path']
DATE_TIME = datetime.now().strftime('%Y%m%d%H%M%S')
DATE = datetime.now().strftime('%Y%m%d')
DATA_PATH = f'{config["data_path"]}{DATE}'
BATCH_SIZE = config['batch_size']

logging.basicConfig(
    filename=f'../../logs/WK{DATE_TIME}.log',
    level=logging.INFO,
    format='[%(asctime)s]: %(levelname)s %(message)s'
)


def get_article():
    response = requests.get(f'{wiki_path}')
    soup = BeautifulSoup(response.text, features='html.parser')
    content = ''.join([p.text for p in soup.find_all('p')])
    name = f'{response.url.split("/")[-1]}.txt'

    with open(f'{DATA_PATH}/{name}', 'w') as out_file:
        out_file.write(content)

    logging.info(msg=f'Article {name} processed')


def exec():
    start_time = datetime.now()
    logging.info(msg=f'GT Scraping started at {start_time}')

    os.makedirs(f'{DATA_PATH}', exist_ok=True)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(get_article): i for i in range(1, BATCH_SIZE+1)}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (url, exc))

    logging.info(msg=f'WK Scraping ended at {datetime.now()}')


if __name__ == '__main__':
    exec()
