import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME = "Northbridge Secure Banking MVP"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

settings = Settings()
