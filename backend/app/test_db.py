from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from model.account_database import Base, Accounts
import random

# Database URL
DATABASE_URL = "postgresql://postgres:Ashank%403115@localhost:5432/AI_Code_Review_Assistant"

def test_connection():
    engine = create_engine(DATABASE_URL, echo=True)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("Connection test:", result.scalar())
    
    # Get table info
    inspector = inspect(engine)
    print("\nExisting tables:", inspector.get_table_names())
    
    if 'accounts' in inspector.get_table_names():
        print("\nAccounts table columns:")
        for column in inspector.get_columns('accounts'):
            print(f"- {column['name']}: {column['type']}")
    
    # Create session
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Try creating a test account with random contact
        random_contact = f"{random.randint(1000000000, 9999999999)}"
        test_account = Accounts(
            name="Test User",
            email=f"test{random.randint(1,1000)}@example.com",
            password="password123",
            contact=random_contact
        )
        
        db.add(test_account)
        db.commit()
        print(f"\nTest account created with contact: {random_contact}")
        
        # Query and show all accounts
        print("\nExisting accounts:")
        accounts = db.query(Accounts).all()
        for account in accounts:
            print(f"- {account.name} ({account.email})")
            
    except IntegrityError as e:
        db.rollback()
        print(f"\nError creating account (this is normal if account exists): {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_connection()