from dotenv import load_dotenv
from starlette.config import Config

load_dotenv()

env = Config(".env")
