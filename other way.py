import socket
import ssl
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_html(url):
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url
    host = url.split('://')[1].split('/')[0]
    path = '/' + '/'.join(url.split('://')[1].split('/')[1:])

    context = ssl.create_default_context()

    try:
        sock = socket.create_connection((host, 443))
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
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

def convert_currency(price, from_currency, to_currency):
    exchange_rates = {
        'MDL': 1,        
        'EUR': 19.5,     
    }
    
    if from_currency in exchange_rates and to_currency in exchange_rates:
        return price / exchange_rates[to_currency] * exchange_rates[from_currency]
    return price

def filter_products(products, min_price, max_price):
    return [product for product in products if min_price <= product['price_eur'] <= max_price]

def validate_product_data(name, price_mdl):
    if price_mdl <= 0:
        return False, "Price must be greater than 0."
    if not name or len(name.strip()) == 0:
        return False, "Product name cannot be empty."
    return True, ""

def fetch_product_description(link):
    html_content = fetch_html(link)
    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
        description_element = soup.find('h3', class_='mb-3 fw-bold')  
        return description_element.text.strip() if description_element else 'No description available'
    return 'Failed to fetch description'

url = 'https://xstore.md/monitoare'
html_content = fetch_html(url)

if html_content:
    soup = BeautifulSoup(html_content, 'html.parser')
    product_tiles = soup.find_all('div', class_='col-sm-6 col-md-4')

    product_data = []
    processed_count = 0

    for product in product_tiles:
        if processed_count >= 2:
            break
        try:
            name_element = product.find('a', class_='xp-title')
            name = name_element.text if name_element else 'N/A'
            price = product.find('div', class_='xbtn-card').text if product.find('div', class_='xbtn-card') else 'N/A'
            link = name_element['href'] if name_element and 'href' in name_element.attrs else 'N/A'

            name, price_mdl = clean_data(name, price)

            is_valid, error_message = validate_product_data(name, price_mdl)
            if not is_valid:
                print(f"Validation error for product '{name}': {error_message}")
                continue

            price_eur = convert_currency(price_mdl, 'MDL', 'EUR')

            description = fetch_product_description(link)

            product_data.append({
                'name': name,
                'price_mdl': price_mdl,
                'price_eur': price_eur,
                'link': link,
                'description': description,  
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })

            processed_count += 1

        except Exception as e:
            print(f"Error extracting product data: {e}")

    filtered_products = filter_products(product_data, 50, 150)

    final_data_model = {
        'filtered_products': filtered_products,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

    print("Final Data Model:")
    print(final_data_model)

else:
    print("No HTML content to parse.")
