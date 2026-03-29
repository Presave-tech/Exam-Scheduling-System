import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Application configuration settings."""

    # Secret key for session management
    SECRET_KEY = os.environ.get("SECRET_KEY", "daa-exam-scheduler-secret-2024")

    # MySQL database URI (XAMPP Default: user root, no password)
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root@localhost/exam_db"

    # Disable modification tracking (not needed, saves memory)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Debug mode (set False in production)
    DEBUG = True
