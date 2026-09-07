from typing import Literal


FIELD_LOCAL_CREDIT = "local_credit"
FIELD_ECTS = "ects"

SemanticField = Literal["local_credit", "ects"]
DetectionConfidence = Literal["high", "medium", "low"]

RELIABLE_CONFIDENCES: set[DetectionConfidence] = {
    "high",
    "medium",
}
