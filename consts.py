import os, sys
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
USE_GPT4 = False

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east1-gcp")
YOUR_TABLE_NAME = os.getenv("TABLE_NAME", "")

OBJECTIVE = sys.argv[1] if len(sys.argv) > 1 else os.getenv("OBJECTIVE", "")
YOUR_FIRST_TASK = os.getenv("FIRST_TASK", "")

SERP_API_KEY = os.getenv("SERP_API_KEY", "")

GLOBAL_HL = os.getenv("GLOBAL_HL", "")
GLOBAL_HL = GLOBAL_HL if GLOBAL_HL != "" else None

GLOBAL_GL = os.getenv("GLOBAL_GL", "")
GLOBAL_GL = GLOBAL_GL if GLOBAL_GL != "" else None

GLOBAL_LOCATION = os.getenv("GLOBAL_LOCATION", "")
GLOBAL_LOCATION = GLOBAL_LOCATION if GLOBAL_LOCATION != "" else None