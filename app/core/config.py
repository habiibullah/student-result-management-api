from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---------------------------------------------------------
    # APPLICATION
    # ---------------------------------------------------------

    app_env: str = "development"
    enable_docs: bool = True

    # Comma-separated values.
    #
    # Examples:
    # CORS_ORIGINS=https://admin.example.com,https://portal.example.com
    # ALLOWED_HOSTS=api.example.com,www.api.example.com
    cors_origins: str = ""
    allowed_hosts: str = "*"

    # ---------------------------------------------------------
    # DATABASE
    # ---------------------------------------------------------

    database_url: str

    # ---------------------------------------------------------
    # AUTHENTICATION
    # ---------------------------------------------------------

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # ---------------------------------------------------------
    # FLUTTERWAVE
    # ---------------------------------------------------------

    flutterwave_secret_key: str = ""
    flutterwave_secret_hash: str = ""
    flutterwave_redirect_url: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        if not self.cors_origins.strip():
            return []

        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def allowed_host_list(self) -> list[str]:
        if not self.allowed_hosts.strip():
            return ["*"]

        return [
            host.strip()
            for host in self.allowed_hosts.split(",")
            if host.strip()
        ]


settings = Settings()
