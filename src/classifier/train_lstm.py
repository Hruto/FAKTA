"""
FAKTA - LSTM Training Script
Trains binary LSTM classifier (hoax vs valid) on balanced dataset.
"""

import os
import sys
import pickle
import json
import yaml
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, f1_score, recall_score, precision_score


def load_dataset(data_dir: str) -> pd.DataFrame:
    """Load training dataset from CSV files."""
    files = list(Path(data_dir).glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    dfs = []
    for f in files:
        df = pd.read_csv(f)
        if "text" not in df.columns or "label" not in df.columns:
            print(f"Skipping {f}: missing text or label column")
            continue
        dfs.append(df[["text", "label"]])

    if not dfs:
        raise ValueError("No valid datasets found")

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined.dropna(subset=["text", "label"])
    combined["label"] = combined["label"].str.lower().str.strip()
    combined = combined[combined["label"].isin(["hoax", "valid"])]

    print(f"Loaded {len(combined)} samples:")
    print(combined["label"].value_counts().to_string())

    return combined


def prepare_sequences(texts: list, labels: list, max_words: int = 10000, max_len: int = 200):
    """Tokenize texts and pad sequences. Returns tokenizer, X, y."""
    import tensorflow as tf
    from tensorflow.keras.preprocessing.text import Tokenizer
    from tensorflow.keras.preprocessing.sequence import pad_sequences

    tokenizer = Tokenizer(num_words=max_words, oov_token="<OOV>")
    tokenizer.fit_on_texts(texts)

    sequences = tokenizer.texts_to_sequences(texts)
    X = pad_sequences(sequences, maxlen=max_len, padding="post", truncating="post")

    label_map = {"valid": 0, "hoax": 1}
    y = np.array([label_map[l] for l in labels])

    return tokenizer, X, y


def undersample_to_balance(df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    """Undersample the majority class to match the minority class (1:1 ratio)."""
    counts = df["label"].value_counts()
    min_count = counts.min()

    print(f"\nBefore undersampling:")
    print(f"  hoax:  {counts.get('hoax', 0)}")
    print(f"  valid: {counts.get('valid', 0)}")
    print(f"  Total: {len(df)}")

    hoax = df[df["label"] == "hoax"].sample(n=min_count, random_state=seed)
    valid = df[df["label"] == "valid"].sample(n=min_count, random_state=seed)

    balanced = pd.concat([hoax, valid], ignore_index=True)
    balanced = balanced.sample(frac=1, random_state=seed).reset_index(drop=True)

    print(f"\nAfter undersampling (1:1 ratio):")
    print(f"  hoax:  {len(hoax)}")
    print(f"  valid: {len(valid)}")
    print(f"  Total: {len(balanced)}")

    return balanced


def train_model(data_dir: str, model_dir: str, config_path: str = "configs/lstm_config.yaml"):
    """Full training pipeline."""
    import tensorflow as tf
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

    # Load config
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = yaml.safe_load(f)
    else:
        config = {}

    max_words = config.get("max_words", 10000)
    max_len = config.get("max_len", 200)
    embedding_dim = config.get("embedding_dim", 64)
    lstm_units = config.get("lstm_units", 32)
    dropout_rate = config.get("dropout_rate", 0.5)
    num_lstm_layers = config.get("num_lstm_layers", 1)
    epochs = config.get("epochs", 20)
    batch_size = config.get("batch_size", 64)
    random_seed = config.get("random_seed", 42)

    # Load data
    print("Loading dataset...")
    df = load_dataset(data_dir)

    # Balance to 1:1
    df = undersample_to_balance(df, seed=random_seed)

    # Split: 70/15/15 stratified
    train_df, test_df = train_test_split(df, test_size=0.15, random_state=random_seed, stratify=df["label"])
    train_df, val_df = train_test_split(train_df, test_size=0.18, random_state=random_seed, stratify=train_df["label"])

    print(f"\nTrain: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

    # Prepare sequences
    tokenizer, X_train, y_train = prepare_sequences(
        train_df["text"].tolist(), train_df["label"].tolist(),
        max_words=max_words, max_len=max_len,
    )
    _, X_val, y_val = prepare_sequences(
        val_df["text"].tolist(), val_df["label"].tolist(),
        max_words=max_words, max_len=max_len,
    )
    _, X_test, y_test = prepare_sequences(
        test_df["text"].tolist(), test_df["label"].tolist(),
        max_words=max_words, max_len=max_len,
    )

    # Class weights
    classes = np.unique(y_train)
    from sklearn.utils.class_weight import compute_class_weight
    weights = compute_class_weight("balanced", classes=classes, y=y_train)
    class_weight = dict(zip(classes, weights))
    print(f"Class weights: {class_weight}")

    # Build model
    from src.classifier.lstm_model import build_lstm_model
    model = build_lstm_model(
        max_words=max_words,
        max_len=max_len,
        embedding_dim=embedding_dim,
        lstm_units=lstm_units,
        dropout_rate=dropout_rate,
        num_classes=2,
        num_lstm_layers=num_lstm_layers,
    )

    print(f"\nModel architecture:")
    model.summary()

    # Callbacks
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "lstm_model.keras")
    tokenizer_path = os.path.join(model_dir, "tokenizer.pkl")

    callbacks = [
        EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True, verbose=1),
        ModelCheckpoint(model_path, save_best_only=True, monitor="val_loss"),
    ]

    # Train
    print("\nTraining...")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        class_weight=class_weight,
        callbacks=callbacks,
    )

    # Save tokenizer
    with open(tokenizer_path, "wb") as f:
        pickle.dump(tokenizer, f)

    # === Evaluation ===
    print("\n" + "=" * 60)
    print("TEST SET EVALUATION")
    print("=" * 60)

    loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
    print(f"\nTest Loss:    {loss:.4f}")
    print(f"Test Accuracy: {accuracy:.4f}")

    y_pred = np.argmax(model.predict(X_test), axis=1)
    label_names = ["valid", "hoax"]

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=label_names))

    # Detailed metrics
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    per_class_recall = recall_score(y_test, y_pred, average=None, labels=[0, 1])
    per_class_precision = precision_score(y_test, y_pred, average=None, labels=[0, 1])

    print(f"Macro-F1: {macro_f1:.4f}")
    print(f"Recall valid:  {per_class_recall[0]:.4f}")
    print(f"Recall hoax:   {per_class_recall[1]:.4f}")
    print(f"Precision valid:  {per_class_precision[0]:.4f}")
    print(f"Precision hoax:   {per_class_precision[1]:.4f}")

    # Save metrics
    metrics = {
        "test_loss": round(float(loss), 4),
        "test_accuracy": round(float(accuracy), 4),
        "macro_f1": round(float(macro_f1), 4),
        "recall_valid": round(float(per_class_recall[0]), 4),
        "recall_hoax": round(float(per_class_recall[1]), 4),
        "precision_valid": round(float(per_class_precision[0]), 4),
        "precision_hoax": round(float(per_class_precision[1]), 4),
        "dataset_info": {
            "total_samples": len(df),
            "hoax_samples": len(df[df["label"] == "hoax"]),
            "valid_samples": len(df[df["label"] == "valid"]),
            "ratio": "1:1 (balanced via undersampling)",
        },
        "model_config": {
            "max_words": max_words,
            "max_len": max_len,
            "embedding_dim": embedding_dim,
            "lstm_units": lstm_units,
            "num_lstm_layers": num_lstm_layers,
            "dropout_rate": dropout_rate,
            "epochs": epochs,
            "batch_size": batch_size,
        },
    }

    metrics_path = os.path.join(model_dir, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nModel saved to      {model_path}")
    print(f"Tokenizer saved to  {tokenizer_path}")
    print(f"Metrics saved to    {metrics_path}")

    return model, history


if __name__ == "__main__":
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data/training"
    model_dir = sys.argv[2] if len(sys.argv) > 2 else "models/lstm"
    train_model(data_dir, model_dir)
