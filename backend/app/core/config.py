from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "区域血液调度协同系统"
    API_V1_STR: str = "/api/v1"
    
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "blood"
    POSTGRES_PASSWORD: str = "blood123"
    POSTGRES_DB: str = "blood_dispatch"
    POSTGRES_PORT: int = 5432
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
