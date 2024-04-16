import json
from datetime import datetime, timedelta
import logging
import requests
from bs4 import BeautifulSoup
import os
import concurrent.futures
import schedule
import argparse
import re

CONFIG_JSON = 'config/wk_config.json'
config = json.load(open(file=CONFIG_JSON, encoding='utf-8'))
data_path = config['data_path']
wiki_path = config['wiki_path']
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
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(get_article): i for i in range(BATCH_SIZE)}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (url, exc))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--lang',
                        type=str,
                        default='en',
                        help='language option in [en, es]')

    args = vars(parser.parse_args())
    lang: str = args.get("lang")

    try:
        wiki_path = re.sub('{lang}', lang, wiki_path)
        data_path = config[re.sub('{lang}', lang, data_path)]
    except IndexError:
        wiki_path = re.sub('{lang}', 'en', wiki_path)
        data_path = config[re.sub('{lang}', 'en', data_path)]

    logging.info(msg=f'Article {wiki_path} processed')

    start_time = datetime.now()
    logging.info(msg=f'WK Scraping started at {start_time}')
    os.makedirs(f'{DATA_PATH}', exist_ok=True)

    end_time = start_time + timedelta(hours=8)
    config = json.load(open(file=CONFIG_JSON, encoding='utf-8'))
    os.makedirs(f'{config["data_path"]}', exist_ok=True)

    schedule.every().minute.do(exec)
    while True:
        schedule.run_pending()

        current_time = datetime.now()
        if current_time >= end_time:
            break

    logging.info(msg=f'WK Scraping ended at {datetime.now()}')
