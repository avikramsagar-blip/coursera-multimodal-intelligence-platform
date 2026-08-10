from dotenv import load_dotenv

load_dotenv()
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print("API Key:", api_key)

client = genai.Client(api_key=api_key)

for model in client.models.list():
    print(model.name)
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

for model in client.models.list():
    if "gemini" in model.name.lower():
        print(model.name)