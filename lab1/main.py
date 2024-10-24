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

def custom_serialize(data):
    serialized = []
    
    def serialize_item(item):
        if isinstance(item, dict):
            items = [f"{serialize_item(k)}:{serialize_item(v)}" for k, v in item.items()]
            return f"dict{{{','.join(items)}}}"
        elif isinstance(item, list):
            items = [serialize_item(i) for i in item]
            return f"list[{','.join(items)}]"
        elif isinstance(item, str):
            return f"str({item})"
        elif isinstance(item, int):
            return f"int({item})"
        elif isinstance(item, float):
            return f"float({item})"
        else:
            return f"unknown({item})"
    
    for key, value in data.items():
        serialized.append(f"{serialize_item(key)}:{serialize_item(value)}")
    
    return "; ".join(serialized)

def custom_deserialize(serialized_str):
    def deserialize_item(item_str):
        if item_str.startswith("dict{"):
            item_str = item_str[5:-1]  
            items = item_str.split(",")
            deserialized_dict = {}
            for item in items:
                if ':' in item:
                    k, v = item.split(':', 1)  
                    deserialized_dict[deserialize_item(k.strip())] = deserialize_item(v.strip())
            return deserialized_dict

        elif item_str.startswith("list["):
            item_str = item_str[5:-1]  
            items = item_str.split(",")  
            return [deserialize_item(i.strip()) for i in items]

        elif item_str.startswith("str("):
            return item_str[4:-1]  
        elif item_str.startswith("float("):
            return float(item_str[6:-1])  
        elif item_str.startswith("int("):
            return int(item_str[4:-1])  
        else:
            return item_str.strip()  

    deserialized = {}
    items = serialized_str.split("; ")  
    for item in items:
        if ":" in item:
            key, value = item.split(":", 1)  
            deserialized_key = deserialize_item(key.strip())
            deserialized_value = deserialize_item(value.strip())
            deserialized[deserialized_key] = deserialized_value

    return deserialized

def serialize_to_json(data):
    import json
    return json.dumps(data, indent=4)

def deserialize_from_json(serialized_str):
    import json
    return json.loads(serialized_str)

def serialize_to_xml(data):
    xml = ['<products>']
    for product in data.get('filtered_products', []):
        xml.append('  <product>')
        for key, value in product.items():
            xml.append(f'    <{key}>{value}</{key}>')
        xml.append('  </product>')
    xml.append('</products>')
    return '\n'.join(xml)

def deserialize_from_xml(serialized_str):
    from xml.etree import ElementTree as ET
    root = ET.fromstring(serialized_str)
    products = []
    for product in root.findall('product'):
        product_data = {}
        for child in product:
            product_data[child.tag] = child.text
        products.append(product_data)
    return {'filtered_products': products}

def calculate_total_price(products, currency):
    total = sum(product['price_mdl'] if currency == 'MDL' else product['price_eur'] for product in products)
    return total

url = 'https://xstore.md/monitoare'
html_content = fetch_html(url)

if html_content:
    soup = BeautifulSoup(html_content, 'html.parser')
    product_tiles = soup.find_all('div', class_='col-sm-6 col-md-4')

    product_data = []
    processed_count = 0

    for product in product_tiles:
        if processed_count >= 5:
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

    filtered_products = filter_products(product_data, 50, 5000)

    total_price_mdl = calculate_total_price(filtered_products, 'MDL')
    total_price_eur = calculate_total_price(filtered_products, 'EUR')

    final_data_model = {
        'filtered_products': filtered_products,
        'total_price_mdl': total_price_mdl,
        'total_price_eur': total_price_eur,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }

    format_choice = input("Choose output format (json, xml, custom): ").strip().lower()

    if format_choice == "json":
        serialized_data = serialize_to_json(final_data_model)
        print("Serialized Data in JSON:")
        print(serialized_data)

        deserialized_data = deserialize_from_json(serialized_data)
        print("Deserialized Data from JSON:")
        print(deserialized_data)

    elif format_choice == "xml":
        serialized_data = serialize_to_xml(final_data_model)
        print("Serialized Data in XML:")
        print(serialized_data)

        deserialized_data = deserialize_from_xml(serialized_data)
        print("Deserialized Data from XML:")
        print(deserialized_data)

    elif format_choice == "custom":
        serialized_data = custom_serialize(final_data_model)
        print("Serialized Data in Custom Format:")
        print(serialized_data)

        deserialized_data = custom_deserialize(serialized_data)
        print("Deserialized Data from Custom Format:")
        print(deserialized_data)

    else:
        print("Invalid format choice.")

else:
    print("No HTML content to parse.")
