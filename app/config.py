"""Environment-backed configuration. Loaded once at import time."""
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    # "mock" or "cloud"
    WHATSAPP_MODE: str = os.getenv("WHATSAPP_MODE", "mock").lower()

    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_TOKEN: str = os.getenv("WHATSAPP_TOKEN", "")
    WHATSAPP_API_VERSION: str = os.getenv("WHATSAPP_API_VERSION", "v21.0")

    META_APP_SECRET: str = os.getenv("META_APP_SECRET", "")
    WEBHOOK_VERIFY_TOKEN: str = os.getenv("WEBHOOK_VERIFY_TOKEN", "rezorra_verify_123")

    @property
    def graph_url(self) -> str:
        return (
            f"https://graph.facebook.com/{self.WHATSAPP_API_VERSION}"
            f"/{self.WHATSAPP_PHONE_NUMBER_ID}/messages"
        )

    @property
    def is_cloud(self) -> bool:
        return self.WHATSAPP_MODE == "cloud"


settings = Settings()
