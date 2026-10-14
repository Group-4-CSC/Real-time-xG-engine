import math


def compute_xg(shot):
    """Temporary placeholder until the analytics model is integrated."""
    x = shot["x"]
    y = shot["y"]
    body_part = shot["body_part"]

    centrality = 1 - abs(y - 50) / 50
    logit = -4.0 + (0.035 * x) + (0.75 * centrality)
    if body_part == "head":
        logit -= 0.5
    elif body_part == "other":
        logit -= 0.25

    return 1 / (1 + math.exp(-logit))