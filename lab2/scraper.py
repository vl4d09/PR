from bs4 import BeautifulSoup
from datetime import datetime
import requests
from main import create_table
import sqlite3


def fetch_html(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    return None

def clean_data(name, price):
    name = name.strip()
    price = price.replace('lei', '').replace(' ', '').strip()
    try:
        price = float(price.replace(',', '').strip())
    except ValueError:
        price = 0
    return name, price

def insert_product(name, price_mdl, price_eur, link, description, timestamp):
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (name, price_mdl, price_eur, link, description, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, price_mdl, price_eur, link, description, timestamp))
    conn.commit()
    conn.close()


def convert_currency(price_mdl):
    exchange_rate = 19.5
    return price_mdl / exchange_rate

def scrape_products(url):
    html_content = fetch_html(url)
    
    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
        product_tiles = soup.find_all('div', class_='col-sm-6 col-md-4')

        for product in product_tiles:
            name_element = product.find('a', class_='xp-title')
            name = name_element.text if name_element else 'N/A'
            price = product.find('div', class_='xbtn-card').text if product.find('div', class_='xbtn-card') else 'N/A'
            link = name_element['href'] if name_element and 'href' in name_element.attrs else 'N/A'

            name, price_mdl = clean_data(name, price)
            price_eur = convert_currency(price_mdl)
            timestamp = datetime.utcnow().isoformat() + 'Z'

            insert_product(name, price_mdl, price_eur, link, 'No description', timestamp)

if __name__ == "__main__":
    create_table()
    

    scrape_products('https://xstore.md/monitoare')
