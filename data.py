from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

# Set up the WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# Specify the ASOS URL for a specific category or product page
url = 'https://www.asos.com/men/a-to-z-of-brands/asos-design/cat/?cid=27871&refine=attribute_10992:61388'

# Open the URL
driver.get(url)

# Wait for the page to load
wait = WebDriverWait(driver, 10)

# Extract product elements
products = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'productTile_U0clN')))

# Limit the number of products to process
max_products = 5  # Change this to the desired number of products

# Iterate through the first max_products
for i, product in enumerate(products[:max_products]):  # Only take the first max_products
    try:
        # Wait for the product element to be present again
        wait.until(EC.visibility_of(product))

        # Extract the name
        name = product.find_element(By.CLASS_NAME, 'productDescription_sryaw').text if product.find_elements(By.CLASS_NAME, 'productDescription_sryaw') else 'N/A'

        # Extract the price
        price = product.find_element(By.CLASS_NAME, 'container_s8SSI').text if product.find_elements(By.CLASS_NAME, 'container_s8SSI') else 'N/A'

        # Extract the product link
        link = product.find_element(By.TAG_NAME, 'a').get_attribute('href') if product.find_elements(By.TAG_NAME, 'a') else 'N/A'

        print(f"Product {i + 1}: {name}, Price: {price}, Link: {link}")

    except StaleElementReferenceException:
        print("Stale element reference encountered. Retrying this product...")
        continue  # Continue to the next product

    except TimeoutException:
        print("Timed out waiting for product elements.")
        break  # Exit the loop if elements cannot be found

    except Exception as e:
        print(f"An error occurred: {e}")

# Close the driver
driver.quit()
