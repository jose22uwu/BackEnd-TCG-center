from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class MySqlConfig:
    host: str
    port: int
    database: str
    username: str
    password: str


def getMySqlConfig() -> MySqlConfig:
    return MySqlConfig(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_DATABASE", ""),
        username=os.getenv("DB_USERNAME", ""),
        password=os.getenv("DB_PASSWORD", ""),
    )


def getArtifactsDir() -> Path:
    artifactsDir = Path(__file__).resolve().parent / "artifacts"
    artifactsDir.mkdir(parents=True, exist_ok=True)
    return artifactsDir
