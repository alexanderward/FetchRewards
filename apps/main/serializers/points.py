from rest_framework import serializers

from apps.main.models import Points


class PointSerializer(serializers.ModelSerializer):

    class Meta:
        model = Points
        fields = ['payer', 'points', 'timestamp', 'spent']


class AddPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = Points
        fields = ['payer', 'points', 'timestamp']


class SpendPointsSerializer(serializers.Serializer):
    points = serializers.IntegerField(write_only=True)

    class Meta:
        fields = ['points']

class BalancePointSerializer(serializers.Serializer):
    payer = serializers.CharField(read_only=True)
    points = serializers.IntegerField(read_only=True)

    class Meta:
        fields = ['payer', 'points']
