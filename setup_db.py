from app import app, db

def setup_database():
    with app.app_context():
        print("Dropping all existing tables...")
        db.drop_all()
        print("Creating new tables...")
        db.create_all()
        print("Database setup completed successfully!")

if __name__ == "__main__":
    setup_database()