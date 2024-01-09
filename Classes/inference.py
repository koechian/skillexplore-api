import requests as r
from dotenv import load_dotenv
import os
import json


class Predictions:
    load_dotenv()

    def __init__(self, tokens, temp, message) -> None:
        self.model = "gpt-3.5-turbo-1106"
        self.max_tokens = tokens
        self.temp = temp
        self.message = message

    def getSkills(self):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ.get('KAGGLE_KEY')}",
        }
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a career services professional with over 10 years of experience in theTech Sector, primarily operating in the Kenya. You are tasked with finding tech relevant skills from a job description. Do not include soft skills such as leadership, attitude. You will be provided with the title of the listing and a job description You are to ONLY return a string of hard skills, the general domain from [Data Analytics, Artificial Intelligence, Software Development, Education/Research,Support,Dev Ops/Infastructure,Security,Quality Assuarance,Cloud,Networking], the predicted level of education from ['masters',degree,bootcamp,highschool,collage,phd,no_barrier] and the general role (no company affiliation or specifics) as a dict with keys 'role','skills', 'domain' and 'education'. Any other input other than a Job description should return an error. Return normalalized relatable skills such as java and Database management. Skills MUST be no more than 2 words long.",
                },
                {
                    "role": "user",
                    "content": (
                        self.message["title"] + "\n" + self.message["description"]
                    ),
                },
            ],
            "temperature": self.temp,
            "max_tokens": self.max_tokens,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
        }

        data = json.JSONEncoder().encode(data)

        response = r.post(
            url="https://api.openai.com/v1/chat/completions", data=data, headers=headers
        )

        return response.json()
