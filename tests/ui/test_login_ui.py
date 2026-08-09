from playwright.sync_api import Page, expect


VALID_USERNAME = "automation_user1"
VALID_PASSWORD = "secret_pass123"


def open_login_page(page: Page, login_ui_base_url: str):
    page.goto(f"{login_ui_base_url}/login")


def username_field(page: Page):
    return page.get_by_label("Username")


def password_field(page: Page):
    return page.get_by_label("Password")


def login_button(page: Page):
    return page.get_by_role("button", name="Login")


def test_ui_01_login_page_loads(page: Page, login_ui_base_url: str):
    open_login_page(page, login_ui_base_url)

    expect(page.get_by_role("heading", name="QA Lab")).to_be_visible()
    expect(username_field(page)).to_be_visible()
    expect(password_field(page)).to_be_visible()
    expect(login_button(page)).to_be_visible()
    expect(login_button(page)).to_be_enabled()


def test_ui_02_valid_login_shows_success(page: Page, login_ui_base_url: str):
    open_login_page(page, login_ui_base_url)

    username_field(page).fill(VALID_USERNAME)
    password_field(page).fill(VALID_PASSWORD)
    login_button(page).click()

    expect(page).to_have_url(f"{login_ui_base_url}/login")
    expect(page.get_by_role("status")).to_contain_text("Login successful")


def test_ui_03_invalid_credentials_show_error(page: Page, login_ui_base_url: str):
    open_login_page(page, login_ui_base_url)

    username_field(page).fill(VALID_USERNAME)
    password_field(page).fill("wrong_password")
    login_button(page).click()

    expect(page).to_have_url(f"{login_ui_base_url}/login")
    expect(page.get_by_role("alert")).to_contain_text("Invalid credentials. Try again.")


def test_ui_04_missing_username_required_validation(page: Page, login_ui_base_url: str):
    open_login_page(page, login_ui_base_url)

    password_field(page).fill(VALID_PASSWORD)
    login_button(page).click()

    username = username_field(page)
    assert username.evaluate("element => !element.validity.valid")
    assert username.evaluate("element => element.validationMessage") != ""
    expect(page.get_by_role("status")).not_to_be_visible()
    expect(page).to_have_url(f"{login_ui_base_url}/login")


def test_ui_05_missing_password_required_validation(page: Page, login_ui_base_url: str):
    open_login_page(page, login_ui_base_url)

    username_field(page).fill(VALID_USERNAME)
    login_button(page).click()

    password = password_field(page)
    assert password.evaluate("element => !element.validity.valid")
    assert password.evaluate("element => element.validationMessage") != ""
    expect(page.get_by_role("status")).not_to_be_visible()
    expect(page).to_have_url(f"{login_ui_base_url}/login")
