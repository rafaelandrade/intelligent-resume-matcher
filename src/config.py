from os import environ

from dotenv import load_dotenv

load_dotenv()

env = environ.get("API_ENV", "development")

config = {
    "LLM_API_KEY": None,
    "DEBUG": False,
    "LOG_LEVEL": "INFO",
}

if env == "production":
    config.update(
        {
            "LLM_API_KEY": environ.get("LLM_API_KEY"),
            "DEBUG": False,
            "LOG_LEVEL": "WARNING",
        }
    )
elif env == "development":
    config.update(
        {
            "LLM_API_KEY": environ.get("LLM_API_KEY"),
            "DEBUG": True,
            "LOG_LEVEL": "DEBUG",
        }
    )
elif env == "test":
    config.update(
        {
            "LLM_API_KEY": "test_key",
            "DEBUG": True,
            "LOG_LEVEL": "DEBUG",
        }
    )

if env != "test" and not config["LLM_API_KEY"]:
    raise ValueError(f"LLM_API_KEY not found for environment '{env}'")
