from __future__ import annotations

import json
from typing import Any

import mysql.connector

from config import getMySqlConfig


def getConnection() -> mysql.connector.MySQLConnection:
    db = getMySqlConfig()
    return mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.username,
        password=db.password,
        database=db.database,
    )


def _parseJson(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return {}
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def loadCards() -> list[dict[str, Any]]:
    sql = """
        SELECT
            id,
            api_identifier,
            name,
            category,
            rarity,
            set_identifier,
            set_name,
            local_id,
            variants,
            api_data
        FROM cards
        ORDER BY id ASC
    """
    with getConnection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

    cards: list[dict[str, Any]] = []
    for row in rows:
        row["variants"] = _parseJson(row.get("variants"))
        row["api_data"] = _parseJson(row.get("api_data"))
        cards.append(row)
    return cards


def loadUserCollection(userId: int) -> list[dict[str, Any]]:
    sql = """
        SELECT
            c.id,
            c.api_identifier,
            c.name,
            c.category,
            c.rarity,
            c.set_identifier,
            c.set_name,
            c.local_id,
            c.variants,
            c.api_data,
            uc.quantity
        FROM user_cards uc
        INNER JOIN cards c ON c.id = uc.card_id
        WHERE uc.user_id = %s
        ORDER BY uc.quantity DESC, c.name ASC
    """
    with getConnection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(sql, (userId,))
            rows = cursor.fetchall()

    collection: list[dict[str, Any]] = []
    for row in rows:
        row["variants"] = _parseJson(row.get("variants"))
        row["api_data"] = _parseJson(row.get("api_data"))
        collection.append(row)
    return collection


def loadCardsByIds(cardIds: list[int]) -> list[dict[str, Any]]:
    if not cardIds:
        return []
    placeholders = ",".join(["%s"] * len(cardIds))
    sql = f"""
        SELECT
            id,
            api_identifier,
            name,
            category,
            rarity,
            set_identifier,
            set_name,
            local_id,
            variants,
            api_data
        FROM cards
        WHERE id IN ({placeholders})
        ORDER BY id ASC
    """
    with getConnection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(sql, tuple(cardIds))
            rows = cursor.fetchall()

    cards: list[dict[str, Any]] = []
    for row in rows:
        row["variants"] = _parseJson(row.get("variants"))
        row["api_data"] = _parseJson(row.get("api_data"))
        cards.append(row)
    return cards


def _cardNameSearchVariants(name: str) -> list[str]:
    """Return search variants: full name, sin espacio antes de V/VMAX, y base sin sufijo."""
    raw = " ".join(name.strip().split())
    if not raw:
        return []
    variants = [raw]
    lower = raw.lower()
    for suffix in (" vmax", " vstar", " gx", " ex"):
        if suffix in lower:
            pos = lower.rfind(suffix)
            base = raw[:pos].strip()
            if base and base not in variants:
                variants.append(base)
            suffix_no_space = raw[pos + 1 : pos + len(suffix)]
            rest = raw[pos + len(suffix) :].strip()
            no_space = base + suffix_no_space + (" " + rest if rest else "")
            if no_space and no_space != raw and no_space not in variants:
                variants.append(no_space.strip())
    if " v " in lower and " vmax" not in lower and " vstar" not in lower:
        base = raw[: lower.rfind(" v ")].strip()
        if base and base not in variants:
            variants.append(base)
    return variants


def findCardIdByName(name: str) -> int | None:
    if not name or not name.strip():
        return None
    raw = name.strip()
    with getConnection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM cards WHERE LOWER(TRIM(name)) = LOWER(%s) LIMIT 1",
                (raw,),
            )
            row = cursor.fetchone()
            if row:
                return int(row[0])
            cursor.execute(
                "SELECT id FROM cards WHERE LOWER(name) LIKE LOWER(%s) LIMIT 1",
                (f"%{raw}%",),
            )
            row = cursor.fetchone()
            if row:
                return int(row[0])
            normalized = " ".join(raw.split())
            if normalized != raw:
                cursor.execute(
                    "SELECT id FROM cards WHERE LOWER(name) LIKE LOWER(%s) LIMIT 1",
                    (f"%{normalized}%",),
                )
                row = cursor.fetchone()
                if row:
                    return int(row[0])
            for variant in _cardNameSearchVariants(raw):
                if variant == raw or variant == normalized:
                    continue
                cursor.execute(
                    "SELECT id FROM cards WHERE LOWER(name) LIKE LOWER(%s) LIMIT 1",
                    (f"%{variant}%",),
                )
                row = cursor.fetchone()
                if row:
                    return int(row[0])
    return None


def loadUserById(userId: int) -> dict[str, Any] | None:
    sql = """
        SELECT u.id, u.username, u.name, ut.slug AS user_type_slug
        FROM users u
        INNER JOIN user_types ut ON ut.id = u.user_type_id
        WHERE u.id = %s
        LIMIT 1
    """
    with getConnection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(sql, (userId,))
            row = cursor.fetchone()
    return row
