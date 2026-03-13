from rest_framework import serializers

class StatsResponseSerializer(serializers.Serializer):
    blog = serializers.DictField()
    exchange_rates = serializers.DictField()
    current_time = serializers.CharField()