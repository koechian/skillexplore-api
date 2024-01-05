from flask import Flask, request
import os

UPLOAD_FOLDER = "uploads"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def cleaner():
    files = os.listdir("uploads")
    for file in files:
        os.remove("uploads/" + file)


@app.route("/resume", methods=["POST"])
def uploadedResume():
    if "file" not in request.files:
        return "No file present"

    file = request.files["file"]

    if file.filename == "":
        return "Empty Filename"

    if file:
        # Create the upload folder if it doesn't exist
        if not os.path.exists(app.config["UPLOAD_FOLDER"]):
            os.makedirs(app.config["UPLOAD_FOLDER"])

        file.save(os.path.join(app.config["UPLOAD_FOLDER"], file.filename))

        return "File uploaded successfully!"


if __name__ == "__main__":
    # cleaner()
    app.run()
