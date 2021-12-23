from collections import OrderedDict

from django.db.models import Sum, Q, Window, F
from django.db.models.functions import Coalesce
from django_cte import With
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.main.models import Points
from apps.main.serializers.points import BalancePointSerializer, AddPointSerializer, PointSerializer, \
    SpendPointsSerializer


class PointsViewSet(generics.ListCreateAPIView):
    model = Points
    serializer_class = BalancePointSerializer

    def get_queryset(self):
        queryset = Points.objects.values('payer').annotate(points=Coalesce(Sum('points', filter=Q(spent=False)), 0)) \
            .order_by('payer')
        return queryset

    def post(self, request, *args, **kwargs):
        serializer = AddPointSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class SpendPointsViewSet(generics.CreateAPIView):
    def post(self, request, *args, **kwargs):
        serializer = SpendPointsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        points_to_spend = serializer.initial_data['points']

        if points_to_spend <= 0:
            raise ValidationError("Points to spend must be greater than 0")
        base_queryset = Points.objects.annotate(cumsum=Window(Sum('points'),
                                                              order_by=F('timestamp').asc())).filter(spent=False)

        cte = With(base_queryset)
        spent = cte.join(Points, id=cte.col.id).with_cte(cte).annotate(cumsum=cte.col.cumsum).filter(
            cumsum__lte=points_to_spend)
        if spent:
            points_to_spend -= spent.last().cumsum
        Points.objects.filter(id__in=spent.values_list('id', flat=True)).update(spent=True)

        remainder_item = Points.objects.filter(spent=False).order_by('timestamp').first()
        if remainder_item:
            remainder_item_data = PointSerializer(remainder_item).data
            remainder_item.points = points_to_spend
            remainder_item.spent = True
            remainder_item.save()

            remainder_item_data['points'] -= points_to_spend
            Points.objects.create(**remainder_item_data)
        elif points_to_spend != 0:
            raise ValidationError("You are attempting to spend more points than are available")

        payer_map = OrderedDict()
        for record in spent:
            if record.payer not in payer_map:
                payer_map[record.payer] = 0
            payer_map[record.payer] -= record.points
        if remainder_item:
            if remainder_item.payer not in payer_map:
                payer_map[remainder_item.payer] = 0
            payer_map[remainder_item.payer] += remainder_item.points * -1
        results = [{"payer": key, "points": value} for key, value in payer_map.items()]
        headers = self.get_success_headers(serializer.data)
        return Response(results, status=status.HTTP_200_OK, headers=headers)
