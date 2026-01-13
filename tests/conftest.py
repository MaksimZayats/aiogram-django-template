from dotenv import find_dotenv, load_dotenv

test_env_path = find_dotenv(".env.test", raise_error_if_not_found=False)
if test_env_path:
    load_dotenv(test_env_path, override=True)
