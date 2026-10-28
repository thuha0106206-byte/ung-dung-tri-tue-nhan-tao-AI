import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

# Nap cac bien moi truong tu file .env
load_dotenv()

DB_TYPE = os.getenv("DB_TYPE", "sqlite").strip().lower()

engine = None
SQLALCHEMY_DATABASE_URL = None

if DB_TYPE == "mysql":
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "quan_ly_sua_chua")

    # 1. Tu dong kiem tra va khoi tao Database MySQL neu chua co
    try:
        import pymysql
        conn = pymysql.connect(
            host=DB_HOST,
            port=int(DB_PORT),
            user=DB_USER,
            password=DB_PASSWORD
        )
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        conn.commit()
        conn.close()
    except Exception as e:
        # Bo qua neu chua ket noi duoc o buoc nay (se bat tiep o engine)
        pass

    # 2. Xay dung ket noi SQLAlchemy voi MySQL
    safe_password = quote_plus(DB_PASSWORD)
    SQLALCHEMY_DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"mysql+pymysql://{DB_USER}:{safe_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )

    try:
        mysql_engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        # Kiem tra ket noi thuc te
        with mysql_engine.connect() as test_conn:
            pass
        engine = mysql_engine
        print(f"[OK] Ket noi thanh cong Database MySQL: {DB_NAME} ({DB_HOST}:{DB_PORT})")
    except Exception as err:
        print(f"[CANH BAO] Khong the ket noi MySQL: {err}")
        print("-> He thong tu dong chuyen sang SQLite (database.db) de ung dung tiep tuc hoat dong.")
        print("-> Hay kiem tra lai DB_USER, DB_PASSWORD trong file .env khi muon dung MySQL.")
        engine = None

# Neu chon SQLite hoac ket noi MySQL that bai, su dung SQLite de khong bi crash
if engine is None:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./database.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    print("[INFO] Dang su dung Co so du lieu SQLite: database.db")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()