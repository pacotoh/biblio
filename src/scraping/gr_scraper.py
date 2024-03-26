import time
from typing import Any
from bs4 import BeautifulSoup
import requests
import re
import json
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import pandas as pd
import logging
import schedule

options = Options()
options.add_argument("--headless")
CONFIG_JSON = 'gr_config.json'
LOG_FILE = datetime.now().strftime('%Y%m%d%H%M%S')

logging.basicConfig(
    filename=f'../../logs/{LOG_FILE}.log',
    level=logging.INFO,
    format='[%(asctime)s]: %(levelname)s %(message)s'
)


@dataclass
class Book:
    url: str = field(init=False)
    soup: BeautifulSoup = field(init=False, repr=False)
    book_id: int = field()
    data: dict = field(default_factory=dict)

    def __post_init__(self):
        json_data = json.load(open(file=CONFIG_JSON, encoding='utf-8'))
        self.url = f"{json_data['gr_path']}{self.book_id}"
        self.soup = BeautifulSoup(requests.get(self.url).text, features='html.parser')
        self._load_data()

    def _get_basic_info(self) -> dict[str, list[Any] | Any] | None:
        try:
            title = self.soup.find(class_='Text Text__title1').text
            authors = [cla.text for cla in self.soup.find_all(class_='ContributorLink__name')]
            rating = self.soup.find(class_="RatingStatistics__rating").text
            desc = self.soup.find(class_="DetailsLayoutRightParagraph__widthConstrained").text
            pub_info = self.soup.find('p', {'data-testid': 'publicationInfo'}).text
            cover = self.soup.find(class_='ResponsiveImage').get('src')
        except AttributeError:
            logging.error(msg=f'Basic info not available for book_id: {self.book_id}')
            return None

        return {
            'title': title,
            'authors': authors,
            'rating_value': rating,
            'desc': desc,
            'pub_info': pub_info,
            'cover': cover,
        }

    def _load_data(self):
        browser = webdriver.Firefox(options=options)
        browser.get(self.url)
        html_source = browser.page_source
        browser.quit()

        self.data = self._get_basic_info()

        try:
            data_str = (re.findall('{"__typename":"BookDetails".*,"work"', html_source)[0]
                        .replace('"details":', '')
                        .replace(',"work"', ''))

            data_dict = json.loads(data_str)

            self._generate_publication_info(data_dict)

            rating_count = re.findall(r'"ratingCount":\d+', html_source)[0].replace('"ratingCount":', '')
            review_count = re.findall(r'"reviewCount":\d+', html_source)[0].replace('"reviewCount":', '')

            self._generate_count_by_lang(html_source)
            self._generate_genres(html_source)

            self.data['rating_count'] = rating_count
            self.data['review_count'] = review_count
        except Exception as e:
            logging.error(msg=f'Advanced info not available for book_id: {self.book_id} -> {e}')

    def _generate_publication_info(self, data_dict):
        self.data['id'] = self.url.split('/')[-1]
        self.data['format'] = data_dict['format']
        self.data['num_pages'] = data_dict['numPages']
        self.data['publication_timestamp'] = data_dict['publicationTime']
        self.data['publication_date'] = (datetime.fromtimestamp(
            int(data_dict['publicationTime']) / 1000).strftime("%Y-%m-%d"))
        self.data['publisher'] = data_dict['publisher']
        self.data['isbn'] = data_dict['isbn']
        self.data['isbn13'] = data_dict['isbn13']
        self.data['language'] = data_dict['language']['name']

    def _generate_count_by_lang(self, html_source):
        count_lang = re.findall(r'"count":\d+,"isoLanguageCode":"[a-z]+"', html_source)
        dict_count_lang = [json.loads('{' + lang + '}') for lang in count_lang]
        self.data['review_count_by_lang'] = {item['isoLanguageCode']: item['count'] for item in dict_count_lang}

    def _generate_genres(self, html_source):
        genres = re.findall('"bookGenres":.*}}],"details":', html_source)
        if len(genres) == 0:
            self.data['genres'] = []
        else:
            dict_genres = [json.loads('{' + genres[0].replace(',"details":', '') + '}')]
            self.data['genres'] = [genre['genre']['name'] for genre in dict_genres[0]['bookGenres']]


@dataclass
class GoodreadsScraper:
    path: str = field(init=False, repr=False)
    last_book_id: int = field(init=False, repr=False)
    books: list = field(default_factory=list, repr=False)
    output_folder: str = field(init=False, repr=False)
    json_data: str = field(init=False, repr=False)

    def __post_init__(self):
        self.json_data = json.load(open(file=CONFIG_JSON, encoding='utf-8'))
        self.last_book_id = int(self.json_data['last_book_id'])
        self.path = self.json_data['gr_path']
        self.output_folder = self.json_data['data_path']

    def _append_book(self):
        book = Book(book_id=self.last_book_id)
        if book and book.data:
            self.books.append(book.data)
            logging.info(msg=f'Book {self.last_book_id} added')

        self.last_book_id += 1

    def _update_book_id(self):
        self.json_data["last_book_id"] = self.last_book_id
        with open(CONFIG_JSON, 'w') as f:
            json.dump(self.json_data, f, indent=2)

    def _save_books_to_csv(self):
        date_string = datetime.now().strftime('%Y%m%d%H%M%S')
        df = pd.DataFrame(self.books)

        df.to_csv(f'{self.json_data["data_path"]}{date_string}.csv', index=False, header=False)
        logging.info(msg=f'{len(self.books)} books added to {self.json_data["data_path"]}{date_string}.csv')

    def exec(self, time_in_minutes: int = 30):
        start = datetime.now()
        end = start + timedelta(minutes=time_in_minutes)

        while True:
            self._append_book()
            current = datetime.now()
            if current >= end:
                break

        self._save_books_to_csv()
        self._update_book_id()


if __name__ == '__main__':
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=8)
    logging.info(msg=f'GR Scraping started at {start_time}')

    schedule.every().minute.do(GoodreadsScraper().exec)
    while True:
        schedule.run_pending()

        current_time = datetime.now()
        if current_time >= end_time:
            break

    logging.info(msg=f'GR Scraping ended at {datetime.now()}')
