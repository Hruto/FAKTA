"""
FAKTA - LSTM Model Definition
Binary LSTM classifier: hoax vs valid.
Input: full article text.
"""

import os
from typing import Optional, Dict
import numpy as np


def build_lstm_model(
    max_words: int = 10000,
    max_len: int = 200,
    embedding_dim: int = 64,
    lstm_units: int = 32,
    dropout_rate: float = 0.5,
    num_classes: int = 2,
    use_bidirectional: bool = True,
    num_lstm_layers: int = 1,
) -> "keras.Model":
    """
    Build LSTM model for hoax classification.

    Args:
        max_words: Vocabulary size
        max_len: Maximum sequence length (padding)
        embedding_dim: Embedding dimension
        lstm_units: Number of LSTM units per layer
        dropout_rate: Dropout rate
        num_classes: Number of output classes (2: hoax, valid)
        use_bidirectional: Whether to use BiLSTM
        num_lstm_layers: Number of LSTM layers (1 or 2)

    Returns:
        Compiled Keras model
    """
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Embedding, LSTM, Bidirectional, Dense, Dropout

    model = Sequential([
        Embedding(
            input_dim=max_words,
            output_dim=embedding_dim,
            input_length=max_len,
            mask_zero=True,
        ),
        Dropout(dropout_rate),
    ])

    for i in range(num_lstm_layers):
        return_seq = (i < num_lstm_layers - 1)  # last layer: return_sequences=False
        if use_bidirectional:
            model.add(Bidirectional(
                LSTM(lstm_units, return_sequences=return_seq, dropout=dropout_rate)
            ))
        else:
            model.add(LSTM(lstm_units, return_sequences=return_seq, dropout=dropout_rate))

    model.add(Dense(16, activation="relu"))
    model.add(Dropout(dropout_rate))
    model.add(Dense(num_classes, activation="softmax"))

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    return model


class LSTMPredictor:
    """Wrapper for LSTM inference."""

    LABELS = ["valid", "hoax"]  # index matches class index

    def __init__(self, model_path: str, max_len: int = 200, max_words: int = 10000):
        import tensorflow as tf
        from tensorflow import keras
        self.max_len = max_len
        self.max_words = max_words
        self.model = keras.models.load_model(model_path)
        self.tokenizer = None
        self._load_tokenizer(model_path)

    def _load_tokenizer(self, model_path: str):
        """Load the tokenizer saved alongside the model."""
        import pickle
        model_dir = os.path.dirname(model_path)
        candidates = [
            os.path.join(model_dir, "tokenizer.pkl"),
            model_path.replace(".keras", "_tokenizer.pkl"),
            model_path.replace(".h5", "_tokenizer.pkl"),
        ]
        for tokenizer_path in candidates:
            if os.path.exists(tokenizer_path):
                with open(tokenizer_path, "rb") as f:
                    self.tokenizer = pickle.load(f)
                return

    def predict(self, text: str) -> Dict[str, float]:
        """
        Predict hoax probability for a single text.

        Returns:
            {"hoax": 0.xx, "valid": 0.xx}
        """
        import tensorflow as tf
        if self.tokenizer is None:
            return {"hoax": 0.5, "valid": 0.5}  # fallback

        seq = self.tokenizer.texts_to_sequences([text])
        padded = tf.keras.preprocessing.sequence.pad_sequences(
            seq, maxlen=self.max_len, padding="post", truncating="post"
        )

        predictions = self.model.predict(padded, verbose=0)
        probs = predictions[0]

        return {
            "hoax": float(probs[1]) if len(probs) > 1 else 0.0,
            "valid": float(probs[0]) if len(probs) > 0 else 0.0,
        }


if __name__ == "__main__":
    model = build_lstm_model()
    model.summary()
    print(f"\nTotal params: {model.count_params():,}")
