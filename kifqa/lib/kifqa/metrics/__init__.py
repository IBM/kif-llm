from typing import List


def true_positives(preds: List, gts: List) -> int:
    tp = 0
    for pred in preds:
        if pred in gts:
            tp += 1

    return tp


def precision(preds: List[str], gts: List[str]) -> float:
    try:
        # When nothing is predicted, precision = 0
        if len(preds) == 0:
            return 0.0
        # When the predictions are not empty
        return min(true_positives(preds, gts) / len(preds), 1.0)
    except TypeError:
        return 0.0


def recall(preds: List[str], gts: List[str]) -> float:
    try:
        # When ground truth is empty return 1
        # even if there are predictions (edge case)
        if len(gts) == 0:
            return 1.0
        # When the ground truth is not empty
        return min(true_positives(preds, gts) / len(gts), 1.0)
    except TypeError:
        return 0.0


def f1_score(p: float, r: float) -> float:
    try:
        return (2 * p * r) / (p + r)
    except ZeroDivisionError:
        return 0.0
