from dotenv import load_dotenv
import os
import ast

data = "{'a': 1, 'b: 2,}"

try:
    dict = ast.literal_eval(data)
except Exception as e:
    print(e)
