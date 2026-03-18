from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import tensorflow as tf

from config import getArtifactsDir
from db import loadCards


def configureTensorFlow() -> None:
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print(f"[TF] GPU habilitada: {len(gpus)} dispositivo(s).")
    else:
        print("[TF] GPU no detectada. Se usará CPU.")


def _safeInt(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        value = value.strip()
        if value.isdigit():
            return int(value)
    return 0


def _safeLen(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def _cardText(card: dict[str, Any]) -> str:
    apiData = card.get("api_data") or {}
    attacks = apiData.get("attacks") or []
    abilities = apiData.get("abilities") or []
    weaknesses = apiData.get("weaknesses") or []
    resistances = apiData.get("resistances") or []
    cardTypes = apiData.get("types") or []

    attackNames = " ".join(str(a.get("name", "")) for a in attacks if isinstance(a, dict))
    abilityNames = " ".join(str(a.get("name", "")) for a in abilities if isinstance(a, dict))
    weaknessTypes = " ".join(str(w.get("type", "")) for w in weaknesses if isinstance(w, dict))
    resistanceTypes = " ".join(str(r.get("type", "")) for r in resistances if isinstance(r, dict))

    return " ".join(
        [
            str(card.get("name") or ""),
            str(card.get("category") or ""),
            str(card.get("rarity") or ""),
            str(card.get("set_identifier") or ""),
            " ".join(str(t) for t in cardTypes),
            attackNames,
            abilityNames,
            weaknessTypes,
            resistanceTypes,
        ]
    ).strip()


def _cardNumericFeatures(card: dict[str, Any]) -> list[float]:
    apiData = card.get("api_data") or {}
    hp = _safeInt(apiData.get("hp"))
    attacks = apiData.get("attacks") or []
    abilities = apiData.get("abilities") or []
    weaknesses = apiData.get("weaknesses") or []
    resistances = apiData.get("resistances") or []
    cardTypes = apiData.get("types") or []
    variants = card.get("variants") or {}

    hasHolo = 1 if bool((variants or {}).get("holo")) else 0
    hasReverse = 1 if bool((variants or {}).get("reverse")) else 0
    hasFirstEdition = 1 if bool((variants or {}).get("firstEdition")) else 0

    return [
        float(hp),
        float(_safeLen(attacks)),
        float(_safeLen(abilities)),
        float(_safeLen(weaknesses)),
        float(_safeLen(resistances)),
        float(_safeLen(cardTypes)),
        float(hasHolo),
        float(hasReverse),
        float(hasFirstEdition),
    ]


@dataclass
class DatasetBundle:
    cardIds: np.ndarray
    numericFeatures: np.ndarray
    textFeatures: np.ndarray
    labelsCategory: np.ndarray
    labelsRarity: np.ndarray
    categoryVocab: list[str]
    rarityVocab: list[str]


def buildDataset() -> DatasetBundle:
    cards = loadCards()
    if len(cards) < 100:
        raise RuntimeError(
            f"Se esperaban >= 100 cartas para entrenar embeddings; encontradas: {len(cards)}"
        )

    cardIds = np.array([int(c["id"]) for c in cards], dtype=np.int32)
    textFeatures = np.array([_cardText(c) for c in cards], dtype=str)
    numericFeatures = np.array([_cardNumericFeatures(c) for c in cards], dtype=np.float32)

    categories = [str(c.get("category") or "Unknown") for c in cards]
    rarities = [str(c.get("rarity") or "Unknown") for c in cards]

    categoryVocab = sorted(set(categories))
    rarityVocab = sorted(set(rarities))
    categoryIndex = {name: idx for idx, name in enumerate(categoryVocab)}
    rarityIndex = {name: idx for idx, name in enumerate(rarityVocab)}

    labelsCategory = np.array([categoryIndex[name] for name in categories], dtype=np.int32)
    labelsRarity = np.array([rarityIndex[name] for name in rarities], dtype=np.int32)

    return DatasetBundle(
        cardIds=cardIds,
        numericFeatures=numericFeatures,
        textFeatures=textFeatures,
        labelsCategory=labelsCategory,
        labelsRarity=labelsRarity,
        categoryVocab=categoryVocab,
        rarityVocab=rarityVocab,
    )


def buildModel(categoryClasses: int, rarityClasses: int, embeddingDim: int = 64) -> tf.keras.Model:
    numericInput = tf.keras.Input(shape=(9,), dtype=tf.float32, name="numericInput")
    textInput = tf.keras.Input(shape=(1,), dtype=tf.string, name="textInput")

    textVectorizer = tf.keras.layers.TextVectorization(
        max_tokens=6000,
        output_mode="int",
        output_sequence_length=40,
        name="textVectorizer",
    )

    textTokenIds = textVectorizer(textInput)
    textEmbedding = tf.keras.layers.Embedding(6000, 64, name="tokenEmbedding")(textTokenIds)
    textEmbedding = tf.keras.layers.GlobalAveragePooling1D(name="textPooling")(textEmbedding)

    numericBranch = tf.keras.layers.LayerNormalization(name="numericNorm")(numericInput)
    numericBranch = tf.keras.layers.Dense(32, activation="relu", name="numericDense")(numericBranch)

    merged = tf.keras.layers.Concatenate(name="mergedFeatures")([numericBranch, textEmbedding])
    merged = tf.keras.layers.Dense(128, activation="relu", name="sharedDense1")(merged)
    embeddingVector = tf.keras.layers.Dense(
        embeddingDim, activation="relu", name="cardEmbedding"
    )(merged)
    shared = tf.keras.layers.Dropout(0.2, name="sharedDropout")(embeddingVector)

    categoryOutput = tf.keras.layers.Dense(
        categoryClasses, activation="softmax", name="categoryOutput"
    )(shared)
    rarityOutput = tf.keras.layers.Dense(
        rarityClasses, activation="softmax", name="rarityOutput"
    )(shared)

    model = tf.keras.Model(
        inputs=[numericInput, textInput],
        outputs=[categoryOutput, rarityOutput],
        name="CardEmbeddingModel",
    )

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss={
            "categoryOutput": "sparse_categorical_crossentropy",
            "rarityOutput": "sparse_categorical_crossentropy",
        },
        metrics={
            "categoryOutput": "accuracy",
            "rarityOutput": "accuracy",
        },
    )
    return model


def trainAndSaveModel(epochs: int = 25, batchSize: int = 32) -> Path:
    configureTensorFlow()
    data = buildDataset()

    model = buildModel(
        categoryClasses=len(data.categoryVocab),
        rarityClasses=len(data.rarityVocab),
        embeddingDim=64,
    )

    textVectorizer = model.get_layer("textVectorizer")
    textVectorizer.adapt(data.textFeatures.tolist())

    textInput = tf.expand_dims(
        tf.convert_to_tensor(data.textFeatures.tolist(), dtype=tf.string),
        axis=1,
    )
    model.fit(
        {"numericInput": data.numericFeatures, "textInput": textInput},
        {"categoryOutput": data.labelsCategory, "rarityOutput": data.labelsRarity},
        validation_split=0.15,
        epochs=epochs,
        batch_size=batchSize,
        verbose=2,
    )

    embeddingExtractor = tf.keras.Model(
        inputs=model.inputs,
        outputs=model.get_layer("cardEmbedding").output,
        name="CardEmbeddingExtractor",
    )
    embeddings = embeddingExtractor.predict(
        {"numericInput": data.numericFeatures, "textInput": textInput}, verbose=0
    )
    embeddings = tf.math.l2_normalize(embeddings, axis=1).numpy()

    artifactsDir = getArtifactsDir()
    modelPath = artifactsDir / "card_embedding_model.keras"
    indexPath = artifactsDir / "card_embedding_index.npz"
    metadataPath = artifactsDir / "embedding_metadata.json"

    model.save(modelPath)
    np.savez(indexPath, cardIds=data.cardIds, embeddings=embeddings)
    metadataPath.write_text(
        json.dumps(
            {
                "categoryVocab": data.categoryVocab,
                "rarityVocab": data.rarityVocab,
                "embeddingDim": int(embeddings.shape[1]),
                "cardCount": int(embeddings.shape[0]),
            },
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"[AI] Modelo guardado en: {modelPath}")
    print(f"[AI] Embeddings guardados en: {indexPath}")
    print(f"[AI] Metadata guardada en: {metadataPath}")
    return artifactsDir


if __name__ == "__main__":
    trainAndSaveModel()
