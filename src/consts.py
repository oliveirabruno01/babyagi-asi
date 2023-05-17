import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
_BARD_API_KEY = os.getenv('_BARD_API_KEY', "")
USE_GPT4 = False
USE_BARD_API = False


GLOBAL_HL = os.getenv("GLOBAL_HL", "")
GLOBAL_GL = os.getenv("GLOBAL_GL", "")
GLOBAL_LOCATION = os.getenv("GLOBAL_LOCATION", "")

OBJECTIVE = os.getenv("OBJECTIVE", "")
TASKS_LIST = eval(os.getenv("TASKS_LIST", ""))

PINECONE_DB = True
SERP_API = False

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
if PINECONE_API_KEY != "":
    PINECONE_DB = True
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")
    PINECONE_TABLE_NAME = os.getenv("PINECONE_TABLE_NAME", "")

SERP_API_KEY = os.getenv("SERP_API_KEY", "")
if SERP_API_KEY != "":
    SERP_API = True

N_SHOT = int(os.getenv("N_SHOT", "1"))

LOAD_FROM=""

# WARNING, BASI WILL RUN FOREVER IN CONTINUOUS MODE
CONTINUOUS_MODE = True

USER_IN_THE_LOOP = False
