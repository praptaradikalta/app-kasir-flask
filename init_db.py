from app import app, db
import models

with app.app_context():
    print("Tabel yang dikenali SQLAlchemy:", db.metadata.tables.keys())
    db.create_all()
    print("DB + 12 tabel berhasil dibuat!")