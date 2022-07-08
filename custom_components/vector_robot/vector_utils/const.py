"""Consts for the data runner."""
from __future__ import annotations
from enum import IntEnum

# BASE_URL = "https://vector.trab.dk/dataset/{}"
BASE_URL = "https://raw.githubusercontent.com/MTrab/vector_robot/dev/Datasets/{}"

class VectorDatasets(IntEnum):
    """Vector dataset enum."""

    VARIATIONS = 0
    DIALOGS = 1
    JOKES = 2
    FACTS = 3
    WEATHER = 4


DATASETS = {
    VectorDatasets.DIALOGS: "dialog.json",
    VectorDatasets.FACTS: None,
    VectorDatasets.JOKES: "jokes.json",
    VectorDatasets.VARIATIONS: "variations.json",
    VectorDatasets.WEATHER: None,
}
