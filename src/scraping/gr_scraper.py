from typing import Any
from bs4 import BeautifulSoup
import requests
import re
import json
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from datetime import datetime
from dataclasses import dataclass, field

options = Options()
options.add_argument("--headless")


# TODO: Continue with the BookInfo dataclass
@dataclass
class BookInfo:
    book_url: str = field(init=False)
    book_soup: BeautifulSoup = field(init=False, repr=False)

    def __post_init__(self):
        json_data = json.load(open(file='gr_config.json', encoding='utf-8'))
        self.book_url = f"{json_data['gr_path']}{json_data['last_book_id']}"
        self.book_soup = BeautifulSoup(requests.get(self.book_url).text, features='html.parser')


@dataclass
class GoodreadsScraper:
    path: str = field(init=False, repr=False)
    last_book_id: int = field(init=False, repr=False)
    books: list = field(default_factory=list, repr=False)
    output_folder: str = field(init=False, repr=False)

    def __post_init__(self):
        json_data = json.load(open(file='gr_config.json', encoding='utf-8'))
        self.last_book_id = int(json_data['last_book_id'])
        self.path = json_data['gr_path']
        self.output_folder = json_data['data_path']
        # TODO: Retrieve from book info
        self.current_soup = BeautifulSoup(requests.get(f'{self.path}{self.last_book_id}').text, features='html.parser')

    def _get_basic_info(self) -> dict[str, list[Any] | Any] | None:
        try:
            title = self.current_soup.find(class_='Text Text__title1').text
            authors = [cla.text for cla in self.current_soup.find_all(class_='ContributorLink__name')]
            rating = self.current_soup.find(class_="RatingStatistics__rating").text
            desc = self.current_soup.find(class_="DetailsLayoutRightParagraph__widthConstrained").text
            pub_info = self.current_soup.find('p', {'data-testid': 'publicationInfo'}).text
            cover = self.current_soup.find(class_='ResponsiveImage').get('src')
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

    def get_book(self):
        self.books.append(self._get_advanced_info(self._get_basic_info()))

    # TODO: This method should update the value of the last_book_id into the gr_config.json file
    def _update_book_id(self):
        pass

# FIXME: Fix the book_url accesing the url from the BookInfo object
    def _get_advanced_info(self, book_data, book_url) -> dict | None:
        browser = webdriver.Firefox(options=options)
        browser.get(book_url)
        html_source = browser.page_source
        browser.quit()

        try:
            data_str = (re.findall('"details":.*,"work"', html_source)[0]
                        .replace('"details":', '')
                        .replace(',"work"', ''))

            data_dict = json.loads(data_str)

            generate_publication_info(book_data, book_url, data_dict)

            rating_count = re.findall(r'"ratingCount":\d+', html_source)[0].replace('"ratingCount":', '')
            review_count = re.findall(r'"reviewCount":\d+', html_source)[0].replace('"reviewCount":', '')

            generate_count_by_lang(book_data, html_source)
            generate_genres(book_data, html_source)

            book_data['rating_count'] = rating_count
            book_data['review_count'] = review_count
        # FIXME: Not catching error reading the JSON file
        except IndexError | TimeoutError | json.decoder.JSONDecodeError:
            return None

        return book_data


def generate_publication_info(book_data, book_url, data_dict):
    book_data['id'] = book_url.split('/')[-1]
    book_data['format'] = data_dict['format']
    book_data['num_pages'] = data_dict['numPages']
    book_data['publication_timestamp'] = data_dict['publicationTime']
    book_data['publication_date'] = (datetime.fromtimestamp(
        int(data_dict['publicationTime']) / 1000).strftime("%Y-%m-%d"))
    book_data['publisher'] = data_dict['publisher']
    book_data['isbn'] = data_dict['isbn']
    book_data['isbn13'] = data_dict['isbn13']
    book_data['language'] = data_dict['language']['name']


# TODO: These two methods are part of the dataclass too
def generate_count_by_lang(book_data, html_source):
    count_lang = re.findall(r'"count":\d+,"isoLanguageCode":"[a-z]+"', html_source)
    dict_count_lang = [json.loads('{' + lang + '}') for lang in count_lang]
    book_data['review_count_by_lang'] = {item['isoLanguageCode']: item['count'] for item in dict_count_lang}


def generate_genres(book_data, html_source):
    genres = re.findall('"bookGenres":.*}}],"details":', html_source)[0].replace(',"details":', '')
    dict_genres = [json.loads('{' + genres + '}')]
    book_data['genres'] = [genre['genre']['name'] for genre in dict_genres[0]['bookGenres']]


def main():
    bi = BookInfo()
    print(bi)


# TODO: Remove this test main method
if __name__ == '__main__':
    main()
