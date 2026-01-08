import os
from dotenv import load_dotenv
load_dotenv(override=True)
print(f"Current Key in Env: {os.getenv('GOOGLE_API_KEY')}")
