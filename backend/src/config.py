"""Configuration Management mit Pydantic Settings"""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Zentrale Konfiguration für VoiceKI Backend.
    Lädt Werte aus .env File oder Environment Variables.
    """
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )

    # OpenAI Configuration (für TypeScript Tool)
    openai_api_key: str = Field(
        default="",
        description="OpenAI API Key für Question Builder Tool"
    )

    # ElevenLabs Configuration
    elevenlabs_api_key: str = Field(
        default="",
        description="ElevenLabs API Key"
    )
    elevenlabs_agent_id: str = Field(
        default="",
        description="ElevenLabs Agent ID für Conversational AI"
    )

    # Data Source Configuration
    data_source_type: Literal["file", "api"] = Field(
        default="file",
        description="Typ der Datenquelle: 'file' oder 'api'"
    )
    data_dir: str = Field(
        default="../KI-Sellcruiting_VerarbeitungProtokollzuFragen/Input_datein_beispiele",
        description="Verzeichnis mit JSON-Dateien (für file data source)"
    )
    
    # API Data Source Configuration
    use_api_source: bool = Field(
        default=False,
        description="Verwende API als Datenquelle statt Files"
    )
    api_url: str = Field(
        default="https://high-office.hirings.cloud/api/v1",
        description="Base URL der API"
    )
    api_key: str = Field(
        default="",
        description="API Key für Authentifizierung"
    )
    api_status: str = Field(
        default="new",
        description="Bewerber-Status: 'new' oder 'not_reached'"
    )
    filter_test_applicants: bool = Field(
        default=True,
        description="Filtert Bewerber mit 'Test' im Namen"
    )
    
    # Webhook Configuration
    webhook_secret: str = Field(
        default="",
        description="Secret für Webhook-Authentifizierung"
    )
    
    # HOC Upload Configuration
    hoc_api_url: str = Field(
        default="https://high-office.hirings.cloud/api/v1",
        description="HOC API URL für Package Upload"
    )
    
    hoc_upload_enabled: bool = Field(
        default=False,
        description="Aktiviert Upload zu HOC Cloud"
    )

    # Questions.json Configuration
    questions_json_path: str = Field(
        default="../KI-Sellcruiting_VerarbeitungProtokollzuFragen/output/questions.json",
        description="Pfad zur generierten questions.json"
    )

    # TypeScript Tool Configuration
    typescript_tool_path: str = Field(
        default="../KI-Sellcruiting_VerarbeitungProtokollzuFragen",
        description="Pfad zum TypeScript Question Builder Tool"
    )
    generate_questions: bool = Field(
        default=False,
        description="Automatisch questions.json generieren via TypeScript Tool"
    )

    # Prompts Configuration
    prompts_dir: str = Field(
        default="../VoiceKI _prompts",
        description="Verzeichnis mit Phase-Prompts"
    )

    # Operational Settings
    dry_run: bool = Field(
        default=False,
        description="Dry-Run Modus (kein echter ElevenLabs Call)"
    )

    def get_data_dir_path(self) -> Path:
        """Gibt data_dir als Path-Objekt zurück"""
        return Path(self.data_dir)

    def get_questions_json_path(self) -> Path:
        """Gibt questions_json_path als Path-Objekt zurück"""
        return Path(self.questions_json_path)

    def get_typescript_tool_path(self) -> Path:
        """Gibt typescript_tool_path als Path-Objekt zurück"""
        return Path(self.typescript_tool_path)

    def get_prompts_dir_path(self) -> Path:
        """Gibt prompts_dir als Path-Objekt zurück"""
        return Path(self.prompts_dir)


# Singleton-Instanz
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    Gibt Singleton-Instanz der Settings zurück.
    Lazy-Loading beim ersten Aufruf.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

