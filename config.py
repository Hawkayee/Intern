import os

class Config:
    SECRET_KEY = "zephor-secret"

    SQLALCHEMY_DATABASE_URI = (
        "postgresql://zephor_user:ranjith05@localhost/zephor_db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
