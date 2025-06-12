from app.db.database import Base, engine
from app.models.simple_user import User

# Create all tables
Base.metadata.create_all(bind=engine)
print("Database tables created successfully!")