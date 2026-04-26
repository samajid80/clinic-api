import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def get_openai_client() -> OpenAI:
    return OpenAI(
        base_url=os.environ["AZURE_OPENAI_ENDPOINT"] + "openai/v1/",
        api_key=os.environ["AZURE_OPENAI_KEY"]
    )

DEPLOYMENT = os.environ.get(
    "AZURE_OPENAI_DEPLOYMENT",
    "clinic-gpt4.1-mini"
)