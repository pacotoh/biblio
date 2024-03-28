import requests
import concurrent.futures
import json
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
import os

CONFIG_JSON = 'config/gt_config.json'
config = json.load(open(file=CONFIG_JSON, encoding='utf-8'))
last_book_id = config['last_book_id']
BATCH_SIZE = int(config['batch_size'])
DATE_TIME = datetime.now().strftime('%Y%m%d%H%M%S')
DATE = datetime.now().strftime('%Y%m%d')
METADATA_FOLDER = f'{config["metadata_path"]}{DATE}'
CONTENT_FOLDER = f'{config["content_path"]}{DATE}'
NOT_FOUND = '<title>404 | Project Gutenberg</title>'
CHUNK_SIZE = 1024


logging.basicConfig(
    filename=f'../../logs/GT{DATE_TIME}.log',
    level=logging.INFO,
    format='[%(asctime)s]: %(levelname)s %(message)s'
)


def get_book(book_id: int):
    content_path = str(config['pathc']).replace('{book_id}', str(book_id))
    file_name = content_path.split('/')[-1]

    response = requests.get(content_path, stream=True)
    if NOT_FOUND not in response.text:
        with open(f'{CONTENT_FOLDER}/{file_name}', 'wb') as out_file:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    out_file.write(chunk)
    else:
        logging.info(msg=f'Book {book_id} not available')


def get_metadata(book_id: int):
    metadata_path = str(config['pathm']).replace('{book_id}', str(book_id))
    soup = BeautifulSoup(requests.get(metadata_path).text, features='html.parser')
    table = soup.find('table', {'class': 'bibrec'})

    if table:
        header = [td.text.replace('\n', '') for td in table.find_all('th')]
        data = [td.text.replace('\n', '') for td in table.find_all('td')][:-1]

        pd.DataFrame(columns=header, data=[data]).to_csv(
            f'{METADATA_FOLDER}/TMP{book_id}.csv',
            header=True,
            index=False)

        logging.info(msg=f'Book {book_id} in {metadata_path} processed')
    else:
        logging.error(msg=f'Book {book_id} in {metadata_path} not processed')


def compact_metadata():
    csv_files = [f for f in os.listdir(METADATA_FOLDER) if f.endswith('.csv') if f.startswith('TMP')]
    dfs = [pd.read_csv(os.path.join(METADATA_FOLDER, csv)) for csv in csv_files]

    pd.concat(dfs).to_csv(f'{METADATA_FOLDER}/{DATE_TIME}.csv', index=False)
    [os.remove(f'{METADATA_FOLDER}/{csv}') for csv in csv_files]


def update_book_id(current_id: int):
    config["last_book_id"] = current_id
    with open(CONFIG_JSON, 'w') as f:
        json.dump(config, f, indent=2)


def execute(function, executor, from_id, to_id):
    os.makedirs(METADATA_FOLDER, exist_ok=True)
    os.makedirs(CONTENT_FOLDER, exist_ok=True)

    future_to_url = {executor.submit(function, i): i for i in range(from_id, to_id)}

    for future in concurrent.futures.as_completed(future_to_url):
        url = future_to_url[future]
        try:
            future.result()
        except Exception as e:
            logging.info(msg='%r generated an exception: %s' % (url, e))


def exec():
    new_book_id = last_book_id + int(BATCH_SIZE)
    start_time = datetime.now()
    logging.info(msg=f'GT Scraping started at {start_time}')

    with concurrent.futures.ThreadPoolExecutor() as executor:
        execute(get_book, executor, last_book_id, new_book_id)
        execute(get_metadata, executor, last_book_id, new_book_id)

    logging.info(msg=f'GT Scraping ended at {datetime.now()}')
    update_book_id(new_book_id)
    compact_metadata()


if __name__ == '__main__':
    exec()
