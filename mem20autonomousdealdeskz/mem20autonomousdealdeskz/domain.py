"""Autonomous deal desk: pricing, terms, approval, negotiation."""
import math


def price_deal(product, customer, discount_cap=0.2):
    base = product.get("price", 0)
    volume = customer.get("volume", 1)
    volume_discount = min(discount_cap, (volume / 1000.0) * 0.05)
    price = base * (1 - volume_discount)
    return round(price, 2)


def terms_score(terms):
    score = 0.0
    if terms.get("payment_days", 30) <= 30:
        score += 0.3
    if terms.get("contract_months", 12) >= 12:
        score += 0.4
    if terms.get("auto_renew"):
        score += 0.3
    return round(score, 3)


def approval_required(deal_value, threshold=10000):
    return deal_value > threshold


def negotiate_round(current_price, counter_offer, rounds_left):
    if rounds_left <= 0:
        return current_price
    midpoint = (current_price + counter_offer) / 2
    return round(midpoint, 2)


def deal_health(deal):
    score = 0.0
    if deal.get("signed"):
        score += 0.4
    if deal.get("paid"):
        score += 0.3
    if deal.get("renewed"):
        score += 0.3
    return round(score, 3)
