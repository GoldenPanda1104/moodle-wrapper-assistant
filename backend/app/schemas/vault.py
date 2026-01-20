from pydantic import BaseModel


class VaultStoreRequest(BaseModel):
    moodle_username: str
    moodle_password: str
    app_password: str


class VaultStatus(BaseModel):
    has_credentials: bool
    cron_enabled: bool


class VaultCronToggleRequest(BaseModel):
    app_password: str
