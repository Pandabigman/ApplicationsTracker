from app.database import engine, Base
from app.models import Application

def init_database():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_database()
    
"""
Run this script to initialize the database
"""