from app.database import create_tables

if __name__ == "__main__":
    print("Creating database tables...")
    try:
        create_tables()
        print("✅ Tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        print("Please check database permissions and try again.")
