from configurations import Configuration

from api.configs.settings import AllSettings


class TestSettings(AllSettings, Configuration):
    DEBUG = True

    @classmethod
    def post_setup(cls) -> None:
        print("Post setup for TestSettings")
