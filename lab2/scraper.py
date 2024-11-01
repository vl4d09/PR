import socket
from bs4 import BeautifulSoup
from datetime import datetime
import sqlite3
from main import create_table
import ssl

def get_db_connection():
    conn = sqlite3.connect('products.db')  
    conn.row_factory = sqlite3.Row  
    return conn

def fetch_html(url):
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url
    host = url.split('://')[1].split('/')[0]
    path = '/' + '/'.join(url.split('://')[1].split('/')[1:])

    context = ssl.create_default_context()

    try:
        sock = socket.create_connection((host, 443))
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3\r\nConnection: close\r\n\r\n"
            ssock.sendall(request.encode('utf-8'))

            response = b""
            while True:
                data = ssock.recv(4096)
                if not data:
                    break
                response += data

            response = response.decode('utf-8')
            headers, body = response.split("\r\n\r\n", 1)
            
            return body

    except Exception as e:
        print(f"Socket error: {e}")
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
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO products (name, price_mdl, price_eur, link, description, timestamp) VALUES (?, ?, ?, ?, ?, ?)", 
            (name, price_mdl, price_eur, link, description, timestamp)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

def convert_currency(price_mdl):
    exchange_rate = 19.5
    return price_mdl / exchange_rate

def scrape_products(base_url, max_pages):
    for page in range(1, max_pages + 1):
        url = f"{base_url}?page={page}"
        html_content = fetch_html(url)
        
        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            product_tiles = soup.find_all('div', class_='col-sm-6 col-md-4')

            if not product_tiles:
                print(f"No products found on page {page}")
                continue

            for product in product_tiles:
                name_element = product.find('a', class_='xp-title')
                name = name_element.text if name_element else 'N/A'
                price_element = product.find('div', class_='xbtn-card')
                price = price_element.text if price_element else 'N/A'
                link = name_element['href'] if name_element and 'href' in name_element.attrs else 'N/A'

                name, price_mdl = clean_data(name, price)
                price_eur = convert_currency(price_mdl)
                timestamp = datetime.utcnow().isoformat() + 'Z'

                product_html = fetch_html(link)
                description = "No description available"
                if product_html:
                    product_soup = BeautifulSoup(product_html, 'html.parser')
                    description_element = product_soup.find('h3', class_='mb-3 fw-bold')  
                    if description_element:
                        description = description_element.text.strip()

                insert_product(name, price_mdl, price_eur, link, description, timestamp)

if __name__ == "__main__":
    create_table()  
    scrape_products('https://xstore.md/monitoare', max_pages=3)  
