from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import time
from datetime import datetime
from functools import reduce

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

url = 'https://www.asos.com/men/a-to-z-of-brands/asos-design/cat/?cid=27871&refine=attribute_10992:61388'
driver.get(url)

wait = WebDriverWait(driver, 10)
products = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'productTile_U0clN')))
max_products = 2

def clean_and_validate_data(name, price):
    name = name.strip()
    price = price.replace('£', '').strip()
    try:
        price = float(price)
        if price.is_integer():
            price = int(price)
        else:
            raise ValueError("Price must be a valid integer.")
    except ValueError:
        raise ValueError("Price must be a valid integer.")
    return name, price

def convert_currency(price, to_currency):
    exchange_rate = 22.5
    if to_currency == 'MDL':
        return price * exchange_rate
    return price

def filter_products(products, min_price, max_price):
    return [product for product in products if min_price <= product['price'] <= max_price]

product_data = []

for i in range(min(max_products, len(products))):
    try:
        product = products[i]
        wait.until(EC.visibility_of(product))

        name = product.find_element(By.CLASS_NAME, 'productDescription_sryaw').text if product.find_elements(By.CLASS_NAME, 'productDescription_sryaw') else 'N/A'
        price = product.find_element(By.CLASS_NAME, 'container_s8SSI').text if product.find_elements(By.CLASS_NAME, 'container_s8SSI') else 'N/A'

        try:
            name, price = clean_and_validate_data(name, price)
        except ValueError as ve:
            print(f"Validation error for product {i + 1}: {ve}")
            continue

        price_in_mdl = convert_currency(price, 'MDL')
        link = product.find_element(By.TAG_NAME, 'a').get_attribute('href') if product.find_elements(By.TAG_NAME, 'a') else 'N/A'

        product_data.append({
            'name': name,
            'price': price_in_mdl,
            'link': link,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })

        print(f"Product {i + 1}: {name}, Price: £{price}, Link: {link}")

        driver.get(link)
        time.sleep(2)

        try:
            description = driver.find_element(By.CLASS_NAME, 'nnYzW').text if driver.find_elements(By.CLASS_NAME, 'nnYzW') else 'No description available'
            print(f"Description: {description}")
        except Exception as e:
            print(f"Error extracting description: {e}")

        driver.back()
        time.sleep(2)

        products = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'productTile_U0clN')))

    except StaleElementReferenceException:
        print("Stale element reference encountered. Retrying this product...")
        continue

    except TimeoutException:
        print("Timed out waiting for product elements.")
        break

    except Exception as e:
        print(f"An error occurred: {e}")

filtered_products = filter_products(product_data, 100, 1000)
total_price = reduce(lambda acc, product: acc + product['price'], filtered_products, 0)

final_data_model = {
    'filtered_products': filtered_products,
    'total_price': total_price,
    'timestamp': datetime.utcnow().isoformat() + 'Z'
}

print("Final Data Model:")
print(final_data_model)

driver.quit()
