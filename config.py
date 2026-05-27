import os
import socket

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def is_mysql_available(host="localhost", port=3306, timeout=0.5):
    """Checks if a MySQL server is listening on the specified port."""
    try:
        socket.setdefaulttimeout(timeout)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
        return True
    except Exception:
        return False


class Config:
    """Application configuration settings."""

    # Secret key for session management
    SECRET_KEY = os.environ.get("SECRET_KEY", "daa-exam-scheduler-secret-2024")

    # Dynamic DB selection: Fallback to SQLite if MySQL (XAMPP) is not active
    if is_mysql_available():
        SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root@localhost/exam_db"
        DB_ENGINE = "MySQL"
    else:
        # Use absolute path inside instance folder
        instance_path = os.path.join(BASE_DIR, "instance", "exam.db")
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{instance_path}"
        DB_ENGINE = "SQLite"

    # Disable modification tracking (not needed, saves memory)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Debug mode (set False in production)
    DEBUG = True

