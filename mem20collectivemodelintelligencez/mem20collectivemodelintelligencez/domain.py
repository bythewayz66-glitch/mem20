"""Collective model intelligence: ensemble, voting, aggregation."""
import math


def ensemble_predict(predictions, weights=None):
    if not predictions:
        return None
    if weights is None:
        weights = [1.0] * len(predictions)
    total_w = sum(weights)
    if total_w == 0:
        return None
    if isinstance(predictions[0], (int, float)):
        return round(sum(p * w for p, w in zip(predictions, weights)) / total_w, 4)
    # classification: weighted vote
    votes = {}
    for p, w in zip(predictions, weights):
        votes[p] = votes.get(p, 0) + w
    return max(votes, key=votes.get)


def diversity_score(models_predictions):
    """Measure diversity among model predictions."""
    if len(models_predictions) < 2:
        return 0.0
    disagreements = 0
    total = 0
    for i in range(len(models_predictions)):
        for j in range(i + 1, len(models_predictions)):
            total += 1
            if models_predictions[i] != models_predictions[j]:
                disagreements += 1
    return round(disagreements / max(1, total), 4)


def knowledge_distill(teacher_preds, student_preds, temperature=2.0):
    """KL-like distillation loss (simplified)."""
    loss = 0.0
    for t, s in zip(teacher_preds, student_preds):
        loss += (t - s) ** 2
    return round(loss / max(1, len(teacher_preds)), 4)


def aggregate_confidence(confidences):
    if not confidences:
        return 0.0
    return round(sum(confidences) / len(confidences), 4)
