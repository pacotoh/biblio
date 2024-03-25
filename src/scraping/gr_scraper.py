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

options = Options()
options.add_argument("--headless")
browser = webdriver.Firefox(options=options)


@dataclass
class Book:
    url: str = field(init=False)
    soup: BeautifulSoup = field(init=False, repr=False)
    data: dict = field(init=False)

    def __post_init__(self):
        json_data = json.load(open(file='gr_config.json', encoding='utf-8'))
        self.url = f"{json_data['gr_path']}{json_data['last_book_id']}"
        # TODO: Need to create the soup/data when a Book is generated?
        self.soup = BeautifulSoup(requests.get(self.url).text, features='html.parser')

    def _get_basic_info(self) -> dict[str, list[Any] | Any] | None:
        try:
            title = self.soup.find(class_='Text Text__title1').text
            authors = [cla.text for cla in self.soup.find_all(class_='ContributorLink__name')]
            rating = self.soup.find(class_="RatingStatistics__rating").text
            desc = self.soup.find(class_="DetailsLayoutRightParagraph__widthConstrained").text
            pub_info = self.soup.find('p', {'data-testid': 'publicationInfo'}).text
            cover = self.soup.find(class_='ResponsiveImage').get('src')
        except AttributeError:
            return None

        return {
            'title': title,
            'authors': authors,
            'rating_value': rating,
            'desc': desc,
            'pub_info': pub_info,
            'cover': cover,
        }

    def _get_advanced_info(self, book_data: dict) -> dict | None:
        browser.get(self.url)
        html_source = browser.page_source
        browser.quit()

        try:
            data_str = (re.findall('"details":.*,"work"', html_source)[0]
                        .replace('"details":', '')
                        .replace(',"work"', ''))

            data_dict = json.loads(data_str)

            self._generate_publication_info(book_data, data_dict)

            rating_count = re.findall(r'"ratingCount":\d+', html_source)[0].replace('"ratingCount":', '')
            review_count = re.findall(r'"reviewCount":\d+', html_source)[0].replace('"reviewCount":', '')

            self._generate_count_by_lang(book_data, html_source)
            self._generate_genres(book_data, html_source)

            book_data['rating_count'] = rating_count
            book_data['review_count'] = review_count
        # FIXME: Not catching error reading the JSON file
        except IndexError | TimeoutError | json.decoder.JSONDecodeError:
            return None

        return book_data

    def _generate_publication_info(self, book_data, data_dict):
        book_data['id'] = self.url.split('/')[-1]
        book_data['format'] = data_dict['format']
        book_data['num_pages'] = data_dict['numPages']
        book_data['publication_timestamp'] = data_dict['publicationTime']
        book_data['publication_date'] = (datetime.fromtimestamp(
            int(data_dict['publicationTime']) / 1000).strftime("%Y-%m-%d"))
        book_data['publisher'] = data_dict['publisher']
        book_data['isbn'] = data_dict['isbn']
        book_data['isbn13'] = data_dict['isbn13']
        book_data['language'] = data_dict['language']['name']

    def _generate_count_by_lang(self, book_data, html_source):
        count_lang = re.findall(r'"count":\d+,"isoLanguageCode":"[a-z]+"', html_source)
        dict_count_lang = [json.loads('{' + lang + '}') for lang in count_lang]
        book_data['review_count_by_lang'] = {item['isoLanguageCode']: item['count'] for item in dict_count_lang}

    def _generate_genres(self, book_data, html_source):
        genres = re.findall('"bookGenres":.*}}],"details":', html_source)[0].replace(',"details":', '')
        dict_genres = [json.loads('{' + genres + '}')]
        book_data['genres'] = [genre['genre']['name'] for genre in dict_genres[0]['bookGenres']]


@dataclass
class GoodreadsScraper:
    path: str = field(init=False, repr=False)
    last_book_id: int = field(init=False, repr=False)
    books: list = field(default_factory=list, repr=False)
    output_folder: str = field(init=False, repr=False)
    json_data: str = field(init=False, repr=False)

    def __post_init__(self):
        self.json_data = json.load(open(file='gr_config.json', encoding='utf-8'))
        self.last_book_id = int(self.json_data['last_book_id'])
        self.path = self.json_data['gr_path']
        self.output_folder = self.json_data['data_path']
        # TODO: Retrieve from book info
        self.current_soup = BeautifulSoup(requests.get(f'{self.path}{self.last_book_id}').text, features='html.parser')

    def get_book(self):
        self.books.append(self._get_advanced_info(self._get_basic_info()))

    def _update_book_id(self):
        self.json_data["last_book_id"] = self.last_book_id
        with open('gr_config.json', 'w') as f:
            json.dump(self.json_data, f, indent=2)
        print(self.json_data)

    def _save_books_to_csv(self):
        date_string = datetime.now().strftime('%Y%m%d%H%M%S')
        df = pd.DataFrame(self.books)

        df.to_csv(f'{self.json_data["data_path"]}{date_string}', index=False)

    def exec(self, time_in_minutes: int = 20):
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=time_in_minutes)

        while True:
            self.get_book()
            self.last_book_id += 1
            current_time = datetime.now()
            if current_time >= end_time:
                break

        self._save_books_to_csv()
        self._update_book_id()


def main():
    scraper = GoodreadsScraper()
    scraper._update_book_id()


# TODO: Remove this test main method
if __name__ == '__main__':
    main()
