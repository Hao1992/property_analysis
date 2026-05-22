import os
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    db_url = os.getenv("DATABASE_URL", "")
    db_status = "not_configured"
    db_error = None
    if db_url:
        try:
            import psycopg
            conn = psycopg.connect(db_url, autocommit=True, connect_timeout=5)
            conn.execute("SELECT 1")
            conn.close()
            db_status = "ok"
        except Exception as e:
            db_status = "error"
            db_error = str(e)
    return {
        "status": "ok",
        "service": "property-analyzer",
        "db": db_status,
        **({"db_error": db_error} if db_error else {}),
    }
