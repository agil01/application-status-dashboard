"""Initialize database tables."""
from src.database import init_database
from src.config import get_settings


def main():
    """Initialize database."""
    settings = get_settings()
    print(f"Initializing database at: {settings.database_path}")

    init_database()

    print("Database initialized successfully!")


if __name__ == "__main__":
    main()
