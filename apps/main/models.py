from django.db import models
from django_cte import CTEManager, With


class Points(models.Model):
    objects = CTEManager()

    payer = models.CharField(max_length=255)
    points = models.IntegerField()
    timestamp = models.DateTimeField()
    spent = models.BooleanField(default=False)
