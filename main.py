from time import sleep
from flask import Blueprint, request
import os
import PyPDF2
from dotenv import load_dotenv
import json
import pymysql
import ast

from .Classes.inference import Predictions

# print(os.getcwd())


main = Blueprint("main", __name__)
load_dotenv()

UPLOAD_FOLDER = "uploads"

urls = os.getenv("DATABASE")
kaggle = os.getenv("KAGGLE_KEY")

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


@main.get("/getPreds")
def getPreds():
    batch = 10
    offset = 0

    while offset < 800:
        try:
            with connection.cursor() as cursor:
                query = f"SELECT * FROM scraped LIMIT {batch} OFFSET {offset}"
                cursor.execute(query)

            rows = cursor.fetchall()

            if not rows:
                break

            else:
                modelInference(rows)
                offset += batch
                # print(offset)
        except Exception as e:
            print(e)

    return "Predictions complete", 201


def modelInference(rows):
    for row in rows:
        data = {
            "title": row[1],
            "description": row[3],
        }
        key = row[0]
        print("Working on: ", key)
        model = Predictions(100, 0.8, data)
        msg = model.getSkills()

        pred = msg["choices"][0]["message"]["content"]

        try:
            pred = ast.literal_eval(pred)
        except Exception as e:
            print(e)
            continue

        packet = {
            "key": key,
            "role": pred["role"],
            "skills": pred["skills"],
            "domain": pred["domain"],
            "education": pred["education"],
        }

        addtoPreds(packet)


def addtoPreds(packet):
    # write to db
    try:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_PREDICTED_TABLE)
            cursor.execute(
                INSERT_PREDICTED,
                (
                    packet["role"],
                    packet["education"],
                    packet["domain"],
                    packet["skills"],
                    packet["key"],
                ),
            )
        connection.commit()
    except Exception as e:
        print(e)

    return


@main.get("/getDomainsCount")
def getDomainStats():
    stats = {}

    with connection.cursor() as cursor:
        cursor.execute(FETCH_ALL_DOMAINS)
        domains = cursor.fetchall()

        for item in domains:
            cursor.execute(
                f"""SELECT COUNT(*) AS domain_count FROM predicted WHERE domain = '{item[1]}'; """
            )
            stats[item[1]] = cursor.fetchall()[0][0]

    return json.dumps(stats), 201


@main.get("/getLocations")
def getGeneralLocations():
    with connection.cursor() as cursor:
        cursor.execute(FETCH_LOCATION_STATS)
        locations = cursor.fetchall()

    return json.dumps(locations), 201


@main.get("/getEducationLevel")
def getGeneralEducation():
    with connection.cursor() as cursor:
        cursor.execute(FETCH_EDUCATION_STATS)
        locations = cursor.fetchall()

    return json.dumps(locations), 201


# SQL STATEMENTS DEFINITIONS

# Scraping Statements
CREATE_SCRAPED_TABLE = "CREATE TABLE IF NOT EXISTS `scraped`(`id` SERIAL PRIMARY KEY, `title` TEXT, `nature` TEXT, `description` TEXT, `location` TEXT, `url` TEXT, `pred` BOOLEAN)"

INSERT_SCRAPED = "INSERT INTO `scraped`(`title`, `nature`, `description`, `location`, `url`, `pred`) VALUES (%s, %s, %s, %s, %s, FALSE) "

CLEAR_SCRAPED = "DELETE FROM scraped"

# Predictions Table Statementss
CREATE_PREDICTED_TABLE = "CREATE TABLE IF NOT EXISTS `predicted` (`id` SERIAL PRIMARY KEY,`role` TEXT,`education_level` TEXT,`skills` TEXT,`domain` TEXT,`scraped_id` BIGINT UNSIGNED, FOREIGN KEY (`scraped_id`) REFERENCES scraped(id) )"

INSERT_PREDICTED = "INSERT INTO `predicted`(`role`,`education_level`,`domain`,`skills`,`scraped_id` ) VALUES (%s,%s,%s,%s,%s)"

# Domains Table
CREATE_DOMAINS_TABLE = "CREATE TABLE IF NOT EXISTS `domains`(`id` SERIAL PRIMARY KEY, `domain` TEXT, `nature` TEXT, `description` TEXT, `location` TEXT, `url` TEXT, `pred` BOOLEAN)"

FETCH_ALL_DOMAINS = "SELECT * FROM domains"

# Data manipulation Queries

FETCH_LOCATION_STATS = (
    "SELECT location, COUNT(*) AS loc_count FROM scraped GROUP BY location;"
)
