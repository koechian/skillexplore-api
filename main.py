from flask import Blueprint, request
import os
import PyPDF2
from dotenv import load_dotenv
import json
import pymysql

main = Blueprint("main", __name__)
load_dotenv()

UPLOAD_FOLDER = "uploads"

urls = os.getenv("DATABASE")
keys = os.getenv("KEYS")

# Create connection to postgres
# Connect to the database
connection = pymysql.connect(host="127.0.0.1", port=3306)


def cleaner():
    files = os.listdir("uploads")
    for file in files:
        os.remove("uploads/" + file)


@main.route("/resume", methods=["POST"])
def uploadedResume():
    if "file" not in request.files:
        return "No file present"

    file = request.files["file"]

    if file.filename == " ":
        return "Empty Filename"

    if file:
        print("file present")
        # Create the upload folder if it doesn't exist
        if not os.path.exists("uploads/"):
            os.makedirs("uploads/")

        file.save(os.path.join("uploads", file.filename))

        # return "File Uploaded"

        return resumeParser(file)


def resumeParser(resume):
    reader = PyPDF2.PdfFileReader(resume, strict=False)
    txt = []

    for page in reader.pages:
        content = page.extract_text()
        txt.append(content)

        return txt


@main.post("/scraped")
def scraped_to_db():
    # try:
    jsonData = request.get_json()
    jsonData = json.loads(jsonData)
    # print("Recieved JSON Data:", jsonData)

    # print(len(jsonData.values()))

    for item in jsonData.values():
        title = item["title"]
        description = item["description"]
        location = item["location"]
        url = item["url"]
        nature = item["nature"]

        # print(index)
        scrapedtoDatabase(title, nature, description, location, url)
    return "printed"
    # except Exception as e:
    #     print("Error Message:", e)

    # return "meh"


def purgeScraped():
    try:
        with connection.cursor() as cursor:
            cursor.execute(CLEAR_SCRAPED)
    except Exception as e:
        return ("Purge failed: ", e), 401

    return " Purge Completed", 201


def scrapedtoDatabase(title, nature, description, location, url):
    # write to db
    try:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_SCRAPED_TABLE)
            cursor.execute(INSERT_SCRAPED, (title, nature, description, location, url))
        connection.commit()
    except Exception as e:
        print(e)


def getPreds():
    pass


# SQL STATEMENTS DEFINITIONS
CREATE_SCRAPED_TABLE = "CREATE TABLE IF NOT EXISTS `scraped`(`id` SERIAL PRIMARY KEY, `title` TEXT, `nature` TEXT, `description` TEXT, `location` TEXT, `url` TEXT, `pred` BOOL)"

INSERT_SCRAPED = "INSERT INTO `scraped`(`title`, `nature`, `description`, `location`, `url`, `pred`) VALUES (%s, %s, %s, %s, %s, FALSE) "

CLEAR_SCRAPED = "DELETE FROM scraped"
