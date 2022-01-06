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
        # Group Points by payer, then get the sum of all unspent points and coalesce from null to 0 if payer
        # only has spent points
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
        # Create a base query where it calculates the cumulative sum based on a window size of 1 after ordering by
        # timestamp and returning only unspent points
        base_queryset = Points.objects.annotate(cumsum=Window(Sum('points'),
                                                              order_by=F('timestamp').asc())).filter(spent=False)

        # Common Table Expressions (CTE) for Django
        # Required because Django doesn't allow Window in a filter clause
        # With & CTE uses base_queryset as a subquery that is joined on and then applies a where clause of the cumsum
        # <= points_to_spend
        cte = With(base_queryset)
        spent = cte.join(Points, id=cte.col.id).with_cte(cte).annotate(cumsum=cte.col.cumsum).filter(
            cumsum__lte=points_to_spend)
        # WITH recursive cte AS
        # (
        #          SELECT   "main_points"."id",
        #                   "main_points"."payer",
        #                   "main_points"."points",
        #                   "main_points"."timestamp",
        #                   "main_points"."spent",
        #                   sum("main_points"."points") OVER (ORDER BY "main_points"."timestamp" ASC) AS "cumsum"
        #          FROM     "main_points"
        #          WHERE    NOT "main_points"."spent")
        # SELECT     "main_points"."id",
        #            "main_points"."payer",
        #            "main_points"."points",
        #            "main_points"."timestamp",
        #            "main_points"."spent",
        #            "cte"."cumsum" AS "cumsum"
        # FROM       "main_points"
        # INNER JOIN "cte"
        # ON         "main_points"."id" = "cte"."id"
        # WHERE      "cte"."cumsum" <= 500
        if spent:
            # Get's the remainder of points left to spend
            points_to_spend -= spent.last().cumsum

        # Update the points spent
        Points.objects.filter(id__in=spent.values_list('id', flat=True)).update(spent=True)

        # Get the most recent unspent points since that would be the part where the lte stopped at during the window sum
        remainder_item = Points.objects.filter(spent=False).order_by('timestamp').first()
        if remainder_item:
            # Update the existing record to the remainder spent
            remainder_item_data = PointSerializer(remainder_item).data
            remainder_item.points = points_to_spend
            remainder_item.spent = True
            remainder_item.save()

            remainder_item_data['points'] -= points_to_spend
            # Create new record of the remaining balance from the original record
            Points.objects.create(**remainder_item_data)
        elif points_to_spend != 0:
            raise ValidationError("You are attempting to spend more points than are available")

        # Build ordered map of payers
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
