from typing import Any

from bs4 import BeautifulSoup
import requests
import re
import json
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from datetime import datetime

options = Options()
options.add_argument("--headless")


# TODO: Convert this functions in methods -> Class GoodreadsScraper
def get_basic_info(soup: BeautifulSoup) -> dict[str, list[Any] | Any] | None:
    try:
        title = soup.find(class_='Text Text__title1').text
        authors = [cla.text for cla in soup.find_all(class_='ContributorLink__name')]
        rating = soup.find(class_="RatingStatistics__rating").text
        desc = soup.find(class_="DetailsLayoutRightParagraph__widthConstrained").text
        pub_info = soup.find('p', {'data-testid': 'publicationInfo'}).text
        cover = soup.find(class_='ResponsiveImage').get('src')
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


# TODO: create methods for reviews_count and genres creation
def get_advanced_info(book_data, book_url: str) -> dict | None:
    browser = webdriver.Firefox(options=options)
    browser.get(book_url)
    html_source = browser.page_source
    browser.quit()

    try:
        data_str = (re.findall('"details":.*,"work"', html_source)[0]
                    .replace('"details":', '')
                    .replace(',"work"', ''))

        data_dict = json.loads(data_str)

        book_data['id'] = book_url.split('/')[-1]
        book_data['format'] = data_dict['format']
        book_data['num_pages'] = data_dict['numPages']
        book_data['publication_timestamp'] = data_dict['publicationTime']
        book_data['publication_date'] = (datetime.fromtimestamp(
            int(data_dict['publicationTime'])/1000).strftime("%Y-%m-%d"))

        book_data['publisher'] = data_dict['publisher']
        book_data['isbn'] = data_dict['isbn']
        book_data['isbn13'] = data_dict['isbn13']
        book_data['language'] = data_dict['language']['name']

        rating_count = re.findall(r'"ratingCount":\d+', html_source)[0].replace('"ratingCount":', '')
        review_count = re.findall(r'"reviewCount":\d+', html_source)[0].replace('"reviewCount":', '')

        # Reviews count by language
        count_lang = re.findall(r'"count":\d+,"isoLanguageCode":"[a-z]+"', html_source)
        dict_count_lang = [json.loads('{' + lang + '}') for lang in count_lang]
        book_data['review_count_by_lang'] = {item['isoLanguageCode']: item['count'] for item in dict_count_lang}

        # Genres
        genres = re.findall('"bookGenres":.*}}],"details":', html_source)[0].replace(',"details":', '')
        dict_genres = [json.loads('{' + genres + '}')]
        book_data['genres'] = [genre['genre']['name'] for genre in dict_genres[0]['bookGenres']]

        book_data['rating_count'] = rating_count
        book_data['review_count'] = review_count
    except IndexError | TimeoutError:
        return None

    return book_data


# TODO: Pass only the book_id to the get_book method
def get_book(book_id: int, books: list):
    book = f'https://www.goodreads.com/book/show/{book_id}'
    soup = BeautifulSoup(requests.get(book).text, features='html.parser')
    books.append(get_advanced_info(get_basic_info(soup), str(book)))


# TODO: Remove this test main method
if __name__ == '__main__':
    my_books = []
    get_book(58473038, my_books)
    print(my_books)
