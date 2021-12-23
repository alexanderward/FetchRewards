from django.core.management.base import BaseCommand, CommandError
from apps.main.models import Points


class Command(BaseCommand):
    help = 'Insert Mock Points'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        Points.objects.all().delete()
        data = [
            {"payer": "DANNON", "points": 300, "timestamp": "2020-10-31T10:00:00Z"},
            {"payer": "UNILEVER", "points": 200, "timestamp": "2020-10-31T11:00:00Z"},
            {"payer": "DANNON", "points": -200, "timestamp": "2020-10-31T15:00:00Z"},
            {"payer": "MILLER COORS", "points": 10000, "timestamp": "2020-11-01T14:00:00Z"},
            {"payer": "DANNON", "points": 1000, "timestamp": "2020-11-02T14:00:00Z"},
        ]

        Points.objects.bulk_create([Points(**x) for x in data])
        # self.stdout.write(self.style.SUCCESS('Successfully inserted mock data'))
