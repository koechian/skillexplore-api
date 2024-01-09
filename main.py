from flask import Blueprint, request
import os
import PyPDF2
import json
import pymysql
import ast
import pandas as pd

from .Classes.inference import Predictions


main = Blueprint("main", __name__)

UPLOAD_FOLDER = "uploads"

# Create connection to postgres
# Connect to the database


# @main.after_request
# def add_cors_headers(response):
#     response.headers.add("Access-Control-Allow-Origin", "http://localhost:1000")
#     return response


def createConnection():
    return pymysql.connect(host="127.0.0.1", port=3306)


def cleaner():
    files = os.listdir("uploads")
    for file in files:
        os.remove("uploads/" + file)


@main.post("/resume")
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
    conn = createConnection()
    cursor = conn.cursor()
    try:
        cursor.execute(CLEAR_SCRAPED)
    except Exception as e:
        return ("Purge failed: ", e), 401
    finally:
        conn.close()

    return " Purge Completed", 201


def scrapedtoDatabase(title, nature, description, location, url):
    # write to db
    conn = createConnection()
    cursor = conn.cursor()
    try:
        cursor.execute(CREATE_SCRAPED_TABLE)
        cursor.execute(INSERT_SCRAPED, (title, nature, description, location, url))
    except Exception as e:
        print(e)


@main.get("/getPreds")
def getPreds():
    batch = 10
    offset = 0
    conn = createConnection()
    cursor = conn.cursor()

    while offset < 800:
        try:
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
        finally:
            conn.close()

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
    conn = createConnection()
    cursor = conn.cursor()

    try:
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
    except Exception as e:
        print(e)
    finally:
        conn.close()

    return


@main.get("/getDomainsCount")
def getDomainStats():
    stats = {}

    conn = createConnection()
    cursor = conn.cursor()

    try:
        cursor.execute(FETCH_ALL_DOMAINS)
        domains = cursor.fetchall()

        for item in domains:
            cursor.execute(
                f"""SELECT COUNT(*) AS domain_count FROM predicted WHERE domain = '{item[1]}'; """
            )
            stats[item[1]] = cursor.fetchall()[0][0]
    except Exception as e:
        print(e)
    finally:
        conn.close()
    return json.dumps(stats), 200


@main.get("/getLocations")
def getGeneralLocations():
    conn = createConnection()
    cursor = conn.cursor()

    try:
        cursor.execute(FETCH_LOCATION_STATS)
        locations = cursor.fetchall()
    except Exception as e:
        print(e)
    finally:
        conn.close()

    return json.dumps(locations), 201


@main.get("/getEducationLevel")
def getGeneralEducation():
    conn = createConnection()
    cursor = conn.cursor()

    try:
        cursor.execute(FETCH_EDUCATION_STATS)
        levels = cursor.fetchall()
    except Exception as e:
        print(e)
    finally:
        conn.close()

    return json.dumps(levels[:6]), 200


@main.post("/getEducationLevelByDomain")
def getDomainEducation():
    domain = request.get_json(force=True)
    domain = domain["domain"]

    query = f"SELECT education_level, COUNT(*) AS ed_count FROM predicted WHERE domain = '{domain}' GROUP BY education_level ORDER BY ed_count DESC;"

    conn = createConnection()
    cursor = conn.cursor()

    try:
        cursor.execute(query)
        levels = cursor.fetchall()
    except Exception as e:
        print(e)
    finally:
        conn.close()

    return json.dumps(levels[:6]), 200


@main.get("/getDomains")
def getDomains():
    query = "SELECT * FROM domains"

    conn = createConnection()
    cursor = conn.cursor()

    try:
        cursor.execute(query)
        domains = cursor.fetchall()
    except Exception as e:
        print(e)
    finally:
        conn.close()

    return json.dumps(domains)


@main.get("/getGeneralSkills")
def skillsAnalysis():
    conn = createConnection()
    cursor = conn.cursor()

    try:
        cursor.execute(MOST_WANTED_SKILLS)
        skills = cursor.fetchall()

        df = pd.DataFrame(skills, columns=["skills"])

        # Split comma-separated skills and create a list of skills
        skills_list = [
            skill.strip().lower()
            for skills in df["skills"].str.split(",")
            for skill in skills
        ]

        # Create a DataFrame to store the counts
        skills_counts = pd.DataFrame(skills_list, columns=["skill"])
        skills_counts["count"] = 1

        # Perform the analysis, for example, get the top 10 skills
        top_skills = (
            skills_counts.groupby("skill")
            .count()
            .sort_values(by="count", ascending=False)
            .head(14)
        )
        data = {
            "skills_info": top_skills.to_dict(),
            "total_count": skills_counts["skill"].nunique(),
        }
    except Exception as e:
        print(e)
    finally:
        conn.close()

    return json.dumps(data), 200


@main.post("/skillsByDomain")
def skillsPerDomain():
    data = request.get_json()
    # print(data)

    domain = data.get("domain")

    query = f"""SELECT skills FROM predicted WHERE domain = '{domain}';"""

    conn = createConnection()
    cursor = conn.cursor()

    try:
        cursor.execute(query)
        skills = cursor.fetchall()

        df = pd.DataFrame(skills, columns=["skills"])

        # Split comma-separated skills and create a list of skills
        skills_list = [
            skill.strip().lower()
            for skills in df["skills"].str.split(",")
            for skill in skills
        ]

        # Create a DataFrame to store the counts
        skills_counts = pd.DataFrame(skills_list, columns=["skill"])
        skills_counts["count"] = 1

        # Perform the analysis, for example, get the top 10 skills
        top_skills = (
            skills_counts.groupby("skill")
            .count()
            .sort_values(by="count", ascending=False)
            .head(14)
        )
        data = {
            "skills_info": top_skills.to_dict(),
            "total_count": skills_counts["skill"].nunique(),
        }
    except Exception as e:
        print(e)
    finally:
        conn.close()

    return json.dumps(data), 201


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

FETCH_LOCATION_STATS = "SELECT location, COUNT(*) AS loc_count FROM scraped GROUP BY location HAVING loc_count > 5;"
FETCH_EDUCATION_STATS = "SELECT education_level, COUNT(*) AS ed_count FROM predicted GROUP BY education_level HAVING ed_count > 3 ORDER BY ed_count DESC;"

FETCH_ROLES_STATS = "SELECT roles, COUNT(*) AS role_count FROM predicted GROUP BY role ORDER BY role DESC;"

# fetch all skills from the predicted table
MOST_WANTED_SKILLS = "SELECT skills FROM predicted"
