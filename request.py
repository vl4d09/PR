from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import time

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
        price = float(price)  # Convert to float to handle prices like 40.00
        if price.is_integer():  
            price = int(price)  # Convert to int if it is
        else:
            raise ValueError("Price must be a valid integer.")
    except ValueError:
        raise ValueError("Price must be a valid integer.")

    return name, price

for i in range(min(max_products, len(products))):  # Use range to avoid index out of range
    try:
        product = products[i] 

        wait.until(EC.visibility_of(product))

        # Extract the name
        name = product.find_element(By.CLASS_NAME, 'productDescription_sryaw').text if product.find_elements(By.CLASS_NAME, 'productDescription_sryaw') else 'N/A'

        # Extract the price
        price = product.find_element(By.CLASS_NAME, 'container_s8SSI').text if product.find_elements(By.CLASS_NAME, 'container_s8SSI') else 'N/A'

        # Clean and validate data
        try:
            name, price = clean_and_validate_data(name, price)
        except ValueError as ve:
            print(f"Validation error for product {i + 1}: {ve}")
            continue  

        # Extract the product link
        link = product.find_element(By.TAG_NAME, 'a').get_attribute('href') if product.find_elements(By.TAG_NAME, 'a') else 'N/A'

        print(f"Product {i + 1}: {name}, Price: £{price}, Link: {link}")

        driver.get(link)

        time.sleep(2)  # As u like adjust 

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

# Close the driver
driver.quit()
