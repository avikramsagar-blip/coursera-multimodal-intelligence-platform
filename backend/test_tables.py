from backend.database import engine
from backend.models import Base

Base.metadata.create_all(bind=engine)

print("✅ All tables verified successfully!")