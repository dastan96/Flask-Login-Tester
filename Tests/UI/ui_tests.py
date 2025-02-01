import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@pytest.fixture(scope="module")
def driver():
    # Set up the WebDriver (ChromeDriver in this case)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode for CI/CD
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def test_login_success(driver):
    driver.get("http://127.0.0.1:5000/login")

    # Interact with elements
    driver.find_element(By.ID, "username").send_keys("testuser")
    driver.find_element(By.ID, "password").send_keys("password123")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    # Wait for the result and assert
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    assert "Welcome to My Test" in driver.page_source
