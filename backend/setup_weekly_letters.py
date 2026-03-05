import os
from app import app, db
from models import WeeklyLetter
import sqlalchemy

def setup_weekly_letters():
    with app.app_context():
        # Check if table exists
        inspector = sqlalchemy.inspect(db.engine)
        if not inspector.has_table("weekly_letters"):
            print("Creating 'weekly_letters' table...")
            WeeklyLetter.__table__.create(db.engine)
            print("Successfully created 'weekly_letters' table.")
        else:
            print("'weekly_letters' table already exists. Checking columns...")
            # If we need to alter it later, we can do it here

if __name__ == "__main__":
    print("Setting up Weekly Letters schema...")
    setup_weekly_letters()
    print("Done.")
