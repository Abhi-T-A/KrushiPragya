from app.database.connection import SessionLocal
from app.modules.ai.model_loader import model_loader


db = SessionLocal()

try:
    model_loader.load_models(db)
finally:
    db.close()