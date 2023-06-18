from flask import Flask
import psycopg2
from playwright.sync_api import Playwright, sync_playwright

def run(playwright: Playwright) -> list:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36")
    page.goto("https://www.sreality.cz/hledani/byty")

    with page.expect_navigation():
        page.locator("button:has-text(\"Zobrazit\")").click()
    page.wait_for_load_state("networkidle")

    elist = page.query_selector_all("span.name.ng-binding")
    titles = [element.text_content() for element in elist]

    imglinks = []
    elements = page.query_selector_all(".property.ng-scope")
    for element in elements:
        img_elements = element.query_selector_all("img")
        slist = []
        for img_element in img_elements:
            src = img_element.get_attribute("src")
            if src != "/img/camera.svg":
                slist.append(src)
        imglinks.append(slist)

    results = [(item, sub_item) for sublist, item in zip(imglinks, titles) for sub_item in sublist]
    browser.close()
    return results

def insert_data(listoftuples:list) -> None:
    connection = None
    try:
        connection = psycopg2.connect(
            host="postgres-db",
            port="5432",
            user="myuser",
            password="mypassword",
            database="mydatabase")
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS mytable(column1 VARCHAR, column2 VARCHAR);")
        cursor.execute("TRUNCATE mytable;")
        for vals in listoftuples:
            cursor.execute(f"INSERT INTO mytable(column1, column2) VALUES ('{vals[0]}', '{vals[1]}');")
        connection.commit()
        cursor.close()
        connection.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if connection is not None:
            connection.close()

def select_data():
    connection = psycopg2.connect(
        host="postgres-db",
        port="5432",
        user="myuser",
        password="mypassword",
        database="mydatabase")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM mytable;")
    result = cursor.fetchall()
    connection.commit()
    cursor.close()
    connection.close()
    return result

def format_tuples_to_html_table(data:list):
    table_html = "<table>"
    table_html += "<tr>"
    for header in ("Title", "Image URL"):
        table_html += f"<th>{header}</th>"
    table_html += "</tr>"

    for row in data:
        table_html += "<tr>"
        for item in row:
            table_html += f"<td>{item}</td>"
        table_html += "</tr>"
    table_html += "</table>"
    return table_html

app = Flask(__name__)

@app.route("/")
def route():
    with sync_playwright() as playwright:
        res = run(playwright)
    insert_data(res)
    inputlst = select_data()
    table_html = format_tuples_to_html_table(inputlst)
    resstr = f"<html><body>{table_html}</body></html>"
    return resstr

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
