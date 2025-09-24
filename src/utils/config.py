"""
Configuration management for ESG reasoning project.
Loads settings from .env file and provides configuration objects.
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
from dataclasses import dataclass

# Load environment variables
load_dotenv()


@dataclass
class QwenConfig:
    """Qwen model configuration"""
    api_key: str
    api_base: str
    text_model: str
    vision_model: str
    embedding_model: str
    temperature: float
    max_tokens: int

    @classmethod
    def from_env(cls) -> 'QwenConfig':
        return cls(
            api_key=os.getenv("DASHSCOPE_API_KEY", ""),
            api_base=os.getenv("QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            text_model=os.getenv("QWEN_TEXT_MODEL", "qwen-plus"),
            vision_model=os.getenv("QWEN_VISION_MODEL", "qwen-vl-plus"),
            embedding_model=os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v4"),
            temperature=float(os.getenv("TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("MAX_TOKENS", "4096"))
        )


@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str
    collection_name: str

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        return cls(
            url=os.getenv("PG_URL", ""),
            collection_name=os.getenv("ESG_COLLECTION_NAME", "mmesgbench_esg_reasoning")
        )


@dataclass
class StorageConfig:
    """Storage configuration"""
    pdf_storage_path: str
    processed_data_path: str
    cache_path: str

    @classmethod
    def from_env(cls) -> 'StorageConfig':
        return cls(
            pdf_storage_path=os.getenv("PDF_STORAGE_PATH", "./source_documents/"),
            processed_data_path=os.getenv("PROCESSED_DATA_PATH", "./processed_data/"),
            cache_path=os.getenv("CACHE_PATH", "./cache/")
        )


@dataclass
class Config:
    """Main configuration object"""
    qwen: QwenConfig
    database: DatabaseConfig
    storage: StorageConfig

    @classmethod
    def load(cls) -> 'Config':
        """Load configuration from environment"""
        return cls(
            qwen=QwenConfig.from_env(),
            database=DatabaseConfig.from_env(),
            storage=StorageConfig.from_env()
        )

    def validate(self) -> bool:
        """Validate configuration"""
        errors = []

        if not self.qwen.api_key:
            errors.append("DASHSCOPE_API_KEY is required")

        if not self.database.url:
            errors.append("PG_URL is required")

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

        return True


# Global config instance
config = Config.load()