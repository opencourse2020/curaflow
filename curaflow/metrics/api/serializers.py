"""
metrics/api/serializers.py

Lightweight serializers for chart data endpoints.

These operate on plain dicts produced by services.py — not model instances —
so we use Serializer (not ModelSerializer) throughout. This keeps the
serialisation layer thin: it only validates the output structure, not the DB schema.
"""

from rest_framework import serializers


class WeeklyRateSerializer(serializers.Serializer):
    """Generic weekly time-series point: {week, value}."""
    week = serializers.DateField()
    avg_rate = serializers.FloatField(required=False)
    avg_dropout_risk = serializers.FloatField(required=False)
    avg_value = serializers.FloatField(required=False)


class CategoryCompletionSerializer(serializers.Serializer):
    category = serializers.CharField()
    total = serializers.IntegerField()
    completed = serializers.IntegerField()
    rate = serializers.FloatField()


class ServiceUtilisationSerializer(serializers.Serializer):
    service = serializers.CharField()
    sessions = serializers.IntegerField()
    completed = serializers.IntegerField()
