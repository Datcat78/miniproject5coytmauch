# INF601 - Advanced Programming in Python
# Coyt Mauch
# Mini Project 5

"""Browser tests for the Bootstrap delete modal and the responsive navbar.

Only a real browser runs Bootstrap's JavaScript, so these tests start the app
on a free port (with its own temporary database) and drive Microsoft Edge with
Selenium. pytest skips them unless Selenium is installed (pip install selenium)
and Edge is available. They also need internet access, because base.html loads
Bootstrap from a CDN.
"""

import itertools
import sqlite3
import threading

import pytest

pytest.importorskip("selenium", reason="pip install selenium to run the browser tests")

from selenium import webdriver  # noqa: E402
from selenium.common.exceptions import NoAlertPresentException, WebDriverException  # noqa: E402
from selenium.webdriver import ActionChains  # noqa: E402
from selenium.webdriver.common.by import By  # noqa: E402
from selenium.webdriver.common.keys import Keys  # noqa: E402
from selenium.webdriver.support import expected_conditions as EC  # noqa: E402
from selenium.webdriver.support.ui import WebDriverWait  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402

from tasktracker import create_app  # noqa: E402
from tasktracker.db import init_db  # noqa: E402

TASK_TITLES = ["Buy milk", "Call the dentist", "Write report"]
_user_numbers = itertools.count(1)


@pytest.fixture(scope="module")
def live_server(tmp_path_factory):
    """Run the app in a background thread, on a free port, with a temporary database."""
    database = str(tmp_path_factory.mktemp("browser") / "browser.sqlite")
    app = create_app({"TESTING": True, "DATABASE": database})
    with app.app_context():
        init_db()

    server = make_server("127.0.0.1", 0, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield {"url": f"http://127.0.0.1:{server.server_port}", "database": database}
    server.shutdown()
    thread.join()


@pytest.fixture(scope="module")
def driver():
    """One headless Edge browser, shared by the tests in this file."""
    options = webdriver.EdgeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1200,900")
    options.set_capability("ms:loggingPrefs", {"browser": "ALL"})
    try:
        edge = webdriver.Edge(options=options)
    except WebDriverException as e:
        pytest.skip(f"Microsoft Edge isn't available: {e.msg}")
    yield edge
    edge.quit()


class Site:
    """Use the app through the browser as one logged-in user."""

    def __init__(self, driver, server, user_id):
        self.driver = driver
        self.url = server["url"]
        self.database = server["database"]
        self.user_id = user_id
        self.wait = WebDriverWait(driver, 5)

    def js(self, script, *args):
        return self.driver.execute_script(script, *args)

    def open(self, path):
        self.driver.get(self.url + path)

    def find(self, css):
        return self.driver.find_element(By.CSS_SELECTOR, css)

    def press(self, *keys):
        ActionChains(self.driver).send_keys(*keys).perform()

    def shift_tab(self):
        ActionChains(self.driver).key_down(Keys.SHIFT).send_keys(Keys.TAB).key_up(Keys.SHIFT).perform()

    def focused(self):
        """The text (or aria-label) of the focused element, or OUTSIDE if it's not in the modal."""
        return self.js("""
            const el = document.activeElement;
            if (!document.getElementById('delete-task-modal').contains(el)) { return 'OUTSIDE'; }
            return el.textContent.trim() || el.getAttribute('aria-label');""")

    def wait_for_new_page(self, old_element):
        """Wait until a click or key press has replaced the page and the new one has loaded."""
        def old_page_gone(_):
            try:
                old_element.is_enabled()
                return False
            except WebDriverException:  # stale, or "node does not belong to the document"
                return True

        self.wait.until(old_page_gone)
        self.wait.until(lambda _: self.js("return document.readyState") == "complete")

    def query(self, sql, params=()):
        connection = sqlite3.connect(self.database)
        try:
            rows = connection.execute(sql, params).fetchall()
            connection.commit()
            return rows
        finally:
            connection.close()

    def task_titles(self):
        """This user's task titles, read straight from the database."""
        rows = self.query("SELECT title FROM tasks WHERE user_id = ? ORDER BY id", (self.user_id,))
        return [title for (title,) in rows]

    def task_id(self, title):
        return self.query(
            "SELECT id FROM tasks WHERE user_id = ? AND title = ?", (self.user_id, title)
        )[0][0]

    def delete_button(self, title):
        for button in self.driver.find_elements(By.CSS_SELECTOR, "[data-bs-target='#delete-task-modal']"):
            if button.get_attribute("data-task-title") == title:
                return button
        raise LookupError(f"No Delete button for {title!r}")

    def open_delete_modal(self, title):
        button = self.delete_button(title)
        button.click()
        # The page focuses Cancel once the modal has finished opening (shown.bs.modal)
        self.wait.until(lambda _: self.focused() == "Cancel")
        return button

    def wait_for_modal_closed(self):
        self.wait.until(EC.invisibility_of_element_located((By.ID, "delete-task-modal")))
        # The page removes the form's action attribute when the modal has finished closing
        # (hidden.bs.modal). get_dom_attribute reads the HTML attribute itself; get_attribute
        # would return the form's action property, which falls back to the page's URL.
        self.wait.until(lambda _: self.find("#delete-task-form").get_dom_attribute("action") is None)

    def alerts(self):
        return [alert.text.strip() for alert in self.driver.find_elements(By.CSS_SELECTOR, "main .alert")]


@pytest.fixture
def site(driver, live_server):
    """A new user with three tasks, logged in through the real login form."""
    username, password = f"browser{next(_user_numbers)}", "browser-password"
    connection = sqlite3.connect(live_server["database"])
    try:
        user_id = connection.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        ).lastrowid
        connection.executemany(
            "INSERT INTO tasks (user_id, title) VALUES (?, ?)",
            [(user_id, title) for title in TASK_TITLES],
        )
        connection.commit()
    finally:
        connection.close()

    site = Site(driver, live_server, user_id)
    site.open("/auth/login")
    driver.delete_all_cookies()
    site.open("/auth/login")
    site.find("#username").send_keys(username)
    site.find("#password").send_keys(password)
    button = site.find("main button[type=submit]")
    button.click()
    site.wait_for_new_page(button)
    assert driver.current_url == site.url + "/tasks/"
    return site


def test_bootstrap_loads_from_the_cdn(site):
    # If this fails, check the internet connection and the integrity hashes in base.html
    assert site.js("return typeof bootstrap") == "object"
    assert site.js("return bootstrap.Modal.VERSION") == "5.3.8"


def test_modal_names_the_task_and_targets_its_delete_url(site):
    site.open_delete_modal("Call the dentist")
    modal = site.find("#delete-task-modal")

    assert modal.is_displayed()
    assert site.find("#delete-task-title").text == "Call the dentist"
    assert site.find("#delete-task-form").get_attribute("action") == (
        f"{site.url}/tasks/{site.task_id('Call the dentist')}/delete"
    )
    # Screen readers announce it as a dialog called "Delete task?"
    assert modal.get_attribute("role") == "dialog"
    assert modal.get_attribute("aria-modal") == "true"
    assert site.js(
        "return document.getElementById(arguments[0].getAttribute('aria-labelledby')).textContent",
        modal,
    ) == "Delete task?"


def close_with_escape(site):
    site.press(Keys.ESCAPE)


def close_with_cancel(site):
    site.find("#delete-task-cancel").click()


def close_with_x_button(site):
    site.find("#delete-task-modal .btn-close").click()


def close_by_clicking_outside(site):
    # The .modal layer covers the window; this point is to the left of the dialog box
    ActionChains(site.driver).move_to_element_with_offset(
        site.find("#delete-task-modal"), -450, -200
    ).click().perform()


@pytest.mark.parametrize("close", (
    close_with_escape, close_with_cancel, close_with_x_button, close_by_clicking_outside,
), ids=("escape", "cancel", "x-button", "click-outside"))
def test_closing_the_modal_deletes_nothing(site, close):
    button = site.open_delete_modal("Call the dentist")
    close(site)
    site.wait_for_modal_closed()

    assert site.task_titles() == TASK_TITLES
    # Focus goes back to the Delete button that opened the modal
    assert site.js("return document.activeElement === arguments[0]", button)


@pytest.mark.parametrize("close", (
    close_with_escape, close_with_cancel, close_with_x_button, close_by_clicking_outside,
), ids=("escape", "cancel", "x-button", "click-outside"))
def test_focus_leaves_the_modal_before_it_is_hidden(site, close):
    # When the modal closes, Bootstrap sets aria-hidden="true" on it. If a button inside
    # still has focus at that moment, screen reader users lose their place and browsers
    # log a warning. Record where focus is at the exact moment the attribute is set.
    site.js("""
        const modal = document.getElementById('delete-task-modal');
        const setAttribute = modal.setAttribute.bind(modal);
        window.focusInsideWhenHidden = null;
        modal.setAttribute = (name, value) => {
            if (name === 'aria-hidden' && String(value) === 'true') {
                window.focusInsideWhenHidden = modal.contains(document.activeElement);
            }
            return setAttribute(name, value);
        };""")

    site.open_delete_modal("Call the dentist")
    close(site)
    site.wait_for_modal_closed()
    assert site.js("return window.focusInsideWhenHidden") is False


def test_modal_updates_for_each_task(site):
    site.open_delete_modal("Call the dentist")
    site.press(Keys.ESCAPE)
    site.wait_for_modal_closed()

    site.open_delete_modal("Write report")
    assert site.find("#delete-task-title").text == "Write report"
    assert site.find("#delete-task-form").get_attribute("action") == (
        f"{site.url}/tasks/{site.task_id('Write report')}/delete"
    )


def test_confirming_deletes_only_that_task(site):
    site.open_delete_modal("Call the dentist")
    confirm = site.find("#delete-task-confirm")
    confirm.click()
    site.wait_for_new_page(confirm)

    assert site.task_titles() == ["Buy milk", "Write report"]
    assert site.driver.current_url == site.url + "/tasks/"
    assert site.alerts()[0].startswith('Task "Call the dentist" deleted.')
    with pytest.raises(LookupError):
        site.delete_button("Call the dentist")


def test_modal_works_with_keyboard_only(site):
    button = site.delete_button("Write report")
    site.js("arguments[0].focus()", button)
    site.press(Keys.ENTER)
    site.wait.until(lambda _: site.focused() == "Cancel")

    # Tab and Shift+Tab cycle through the modal's three buttons without leaving it
    tab_order = []
    for _ in range(4):
        site.press(Keys.TAB)
        tab_order.append(site.focused())
    assert tab_order == ["Delete task", "Close", "Cancel", "Delete task"]

    shift_tab_order = []
    for _ in range(4):
        site.shift_tab()
        shift_tab_order.append(site.focused())
    assert shift_tab_order == ["Cancel", "Close", "Delete task", "Cancel"]

    # From Cancel, Tab to "Delete task" and press Enter
    site.press(Keys.TAB)
    confirm = site.find("#delete-task-confirm")
    site.press(Keys.ENTER)
    site.wait_for_new_page(confirm)
    assert site.task_titles() == ["Buy milk", "Call the dentist"]


def test_modal_shows_html_in_a_title_as_plain_text(site):
    title = '"><img src=x onerror=alert(1)>'
    site.query("INSERT INTO tasks (user_id, title) VALUES (?, ?)", (site.user_id, title))
    site.open("/tasks/")

    site.open_delete_modal(title)
    assert site.find("#delete-task-title").text == title
    assert site.js("return document.querySelectorAll('#delete-task-modal img').length") == 0
    with pytest.raises(NoAlertPresentException):
        site.driver.switch_to.alert


def test_navbar_collapses_into_a_menu_on_phones(site):
    site.driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True,
    })
    try:
        site.open("/tasks/")
        site.wait.until(lambda _: site.js("return window.innerWidth") == 390)
        toggler = site.find(".navbar-toggler")
        add_task_link = site.find("#main-nav a[href='/tasks/new']")

        assert toggler.is_displayed()
        assert not add_task_link.is_displayed()
        assert site.js("return document.documentElement.scrollWidth <= window.innerWidth")

        toggler.click()
        site.wait.until(lambda _: add_task_link.is_displayed())
        assert toggler.get_attribute("aria-expanded") == "true"

        toggler.click()
        site.wait.until(EC.invisibility_of_element_located((By.ID, "main-nav")))
        assert toggler.get_attribute("aria-expanded") == "false"
    finally:
        site.driver.execute_cdp_cmd("Emulation.clearDeviceMetricsOverride", {})


def test_no_console_errors_or_warnings(site):
    try:
        site.driver.get_log("browser")  # Throw away messages from earlier pages
    except WebDriverException:
        pytest.skip("This browser driver doesn't share console logs")

    site.open("/tasks/")
    site.open_delete_modal("Buy milk")
    site.press(Keys.ESCAPE)
    site.wait_for_modal_closed()
    confirm_button = site.find("#delete-task-confirm")
    site.open_delete_modal("Buy milk")
    confirm_button.click()
    site.wait_for_new_page(confirm_button)

    problems = [
        entry["message"] for entry in site.driver.get_log("browser")
        if entry["level"] in ("SEVERE", "WARNING") and entry["message"].startswith(site.url)
    ]
    assert problems == []
