import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Global Airdrop Hunter"
    app_version: str = "1.0.0"
    debug: bool = False

    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_token: Optional[str] = None

    database_path: str = ""
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.database_path:
            app_data = os.environ.get('LOCALAPPDATA', os.environ.get('APPDATA', os.path.expanduser('~')))
            self.database_path = str(Path(app_data) / 'GlobalAirdropHunter' / 'app.db')

    @property
    def database_dir(self) -> Path:
        return Path(self.database_path).parent

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()