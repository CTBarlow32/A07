'''
Carter Barlow
IS303- A07
Book Market: I am scraping a book market (books.toscrape.com) to print out an analysis what will show a average price
of ratings for the books.

IPO's:
Inputs: books.toscrape.com

Processes: scrape/fetch data from website (title, rating, price), store in SQLite database, query data with pandas,
have pandas analyze what average cost per rating, visualize as a chart of average price by rating

Outputs: printed analysis, chart file of average price of rating, database file

books.toscrape.com
'''

#importing
import requests
from bs4 import BeautifulSoup
from peewee import SqliteDatabase, Model, CharField, FloatField, IntegerField
import pandas as pd
import matplotlib.pyplot as plt
import time
import sqlite3

#database setup
db = SqliteDatabase('books.db')
class Book(Model):
    title = CharField(unique=True)
    rating = FloatField()
    price = FloatField()

    class Meta:
        database = db
db.connect()
db.create_tables([Book])

#fetch url
def fetch_and_parse(url, retries=3, delay=2):
    """Fetch URL, return BeautifulSoup or None."""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return BeautifulSoup(response.text, "html.parser")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Request to {url} failed ({e}); retry {attempt + 1}/{retries}")
            time.sleep(delay)
    return None


#parse books
RATING_WORDS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

def parse_books(soup):
    """Extract title, price, and rating for each book on a page."""
    books = []
    for article in soup.find_all("article", class_="product_pod"):
        title = article.h3.a["title"]

        price_text = article.find("p", class_="price_color").text
        price = float(price_text.strip("£Â"))

        rating_classes = article.find("p", class_="star-rating")["class"]
        rating_word = next(c for c in rating_classes if c != "star-rating")
        rating = RATING_WORDS[rating_word]

        books.append({"title": title, "price": price, "rating": rating})
    return books

#scrape all catalogue pages
def scrape_all_books():
    '''Loop through every catalogue page and collect all books'''
    all_books = []
    page = 1
    while True:
        url=f"https://books.toscrape.com/catalogue/page-{page}.html"
        soup = fetch_and_parse(url)
        if soup is None:
            break
        books = parse_books(soup)
        all_books.extend(books)
        print(f"Page {page}: {len(books)} books")
        page +=1
        time.sleep(1)
    return all_books

#save books to database
def save_books(books):
    '''Insert scraped books into database, skipping any that already exist'''
    with db.atomic():
        Book.insert_many(books).on_conflict_ignore().execute()

#load books into a dataframe
def load_dataframe():
    '''Query the books table and return it as a pandas Dataframe'''
    conn = sqlite3.connect('books.db')
    df = pd.read_sql("SELECT * FROM book", conn)
    conn.close()
    return df

#analyze average price per rating
def analyze_books(df):
    '''Compute the average price for each star rating'''
    return df.groupby("rating")["price"].mean()

#chart average price per rating
def plot_avg_price(avg_price_by_rating):
    '''Create and save a bar chart of average price per rating'''
    ax = avg_price_by_rating.plot(kind="bar", color="steelblue")
    ax.set_xlabel("Rating (stars)")
    ax.set_ylabel("Average Price")
    ax.set_title("Average Book Price by Rating")
    plt.tight_layout()
    plt.savefig("avg_price_by_rating.png")
    plt.show()
    plt.close()



def main():
    '''Run the full scrape, store, analyze, and visualize pipeline'''
    books = scrape_all_books()
    print(f"Scraped {len(books)} books total")
    save_books(books)
    print(f"Saved {Book.select().count()} books to {db.database}")

    df = load_dataframe()
    print(df.head())

    print(f"\nOverall average price: £{df['price'].mean():.2f}")
    print(f"Price range: £{df['price'].min():.2f} - £{df['price'].max():.2f}")

    avg_price_by_rating = analyze_books(df)
    print("\nAverage price by rating:")
    print(avg_price_by_rating)

    highest_rating = avg_price_by_rating.idxmax()
    lowest_rating = avg_price_by_rating.idxmin()
    print(f"\nFinding: {highest_rating}-star books have the highest average price "
          f"(£{avg_price_by_rating[highest_rating]:.2f}), while {lowest_rating}-star "
          f"books have the lowest (£{avg_price_by_rating[lowest_rating]:.2f}).")

    plot_avg_price(avg_price_by_rating)
    print("\nChart saved to avg_price_by_rating.png")


if __name__ == "__main__":
    main()