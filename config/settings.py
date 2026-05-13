import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Fyers credentials (optional — bot works without live data)
    FYERS_CLIENT_ID: Optional[str] = None
    FYERS_SECRET_KEY: Optional[str] = None
    FYERS_REDIRECT_URI: str = "http://localhost:8080"
    FYERS_ACCESS_TOKEN: Optional[str] = None

    # Telegram credentials (required)
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_ADMIN_ID: int

    # Database Paths
    NIFTY_DATABASE_PATH: str = os.path.join("nifty", "storage", "nifty.db")
    XAUUSD_DATABASE_PATH: str = os.path.join("xauusd", "storage", "xauusd.db")

    # Schedule & Instrument
    RESET_TIME_IST: str = "02:00"
    NIFTY_INSTRUMENT: str = "NSE:NIFTY50-INDEX"
    XAUUSD_INSTRUMENT: str = "GC=F" # Gold Futures (tracks spot closely and is more reliable)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
