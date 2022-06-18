"""For handling states."""
from __future__ import annotations

STIMULATION_TO_TEXT = {
    "ReactToSoundAwake": "Heard something",
    "PettingStarted": "Being petted",
    "PettingBlissLevelIncrease": "Being petted",
    "PettingReachedMaxBliss": "Being petted",
    "ReactToMotion": "Saw something moving",
    "ReactToObstacle": "Reacted to an obstacle",
    "ReactToUnexpectedMovement": "Reacted to unexpected movement",
    "Asleep": "Sleeping",
    "DanceToTheBeat": "Dancing to the beat",
    "KeepawayStarted": "Keepaway action",
}

FEATURES_TO_IGNORE = ["NoFeature", "SDK"]
STIMULATIONS_TO_IGNORE = ["PlacesOnCharger"]


class VectorStates(dict):
    """Handling Vector events."""
