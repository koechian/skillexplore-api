from flask import Blueprint, request
import os
import PyPDF2
import psycopg2
from dotenv import load_dotenv

main = Blueprint("main", __name__)
load_dotenv()
UPLOAD_FOLDER = "uploads"
url = os.getenv("DATABASE_URL")


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
    jsonData = request.get_json()
    return jsonData


def connect(status):
    if status:
        connection = psycopg2.connect(url)
        return connection


def toDatabase():
    # connect to db
    connection = connect(True)

    pass


# DEFINE SQL STATEMENTS
CREATE_SCRAPED_TABLE = "CREATE TABLE IF NOT EXISTS scraped(id SERIAL PRIMARY KEY, title TEXT, nature TEXT, description TEXT, location TEXT, url TEXT)"

INSERT_SCRAPED = "INSERT INTO scraped(title, nature, description, location, url) VALUES (%s,%s,%s,%s,%s) "
