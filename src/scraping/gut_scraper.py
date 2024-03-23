from bs4 import BeautifulSoup
import requests
import concurrent.futures


def get_book(book_id: int) -> dict | None:
    try:
        soup = BeautifulSoup(
            requests
            .get(f'https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}-images.html').text
        )

        return {'id': id, 'text': '. '.join([p.text for p in soup.find_all('p')])}
    except:  # FIXME: What kind of exception?
        return None


def main():
    test_books = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # TODO: Parametrize the range of execution
        future_to_url = {executor.submit(get_book, i): i for i in range(1, 3)}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                book = future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (url, exc))
            else:
                if book is not None:
                    test_books.append(book)

        print(test_books)


if __name__ == '__main__':
    main()
