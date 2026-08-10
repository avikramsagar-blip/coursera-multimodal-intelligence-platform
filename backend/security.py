import os
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set in environment variables")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str):
    try:
        print("=== JWT DEBUG ===")
        print(f"SECRET_KEY loaded: {bool(SECRET_KEY)}")
        print(f"Token received: {repr(token[:30])}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"Decoded payload: {payload}")
        email = payload.get("sub")
        print(f"Email from payload: {email}")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        print("=== JWT DEBUG END ===")
        return email
    except HTTPException:
        raise
    except Exception as e:
        print(f"JWT Exception type: {type(e).__name__}")
        print(f"JWT Exception message: {str(e)}")
        print("=== JWT DEBUG END ===")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
