from dotenv import find_dotenv, load_dotenv

env_path = find_dotenv(".env.test", raise_error_if_not_found=True)
load_dotenv(env_path, override=True)
