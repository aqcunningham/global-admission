import time

import requests
from decouple import config
from django.core.management.base import BaseCommand
from django.utils import timezone

from globaladmission.models import School

API_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"

# Scorecard field -> School model field
FIELDS = {
    "school.name": "official_name",
    "school.city": "city",
    "school.state": "state",
    "school.school_url": "website",
    "latest.admissions.admission_rate.overall": "admission_rate",
    "latest.student.size": "undergrad_size",
    "latest.admissions.sat_scores.average.overall": "sat_average",
    "latest.cost.attendance.academic_year": "cost_of_attendance",
}
INTEGER_FIELDS = {"undergrad_size", "sat_average", "cost_of_attendance"}


class Command(BaseCommand):
    help = "Fill school details from the College Scorecard API"

    def handle(self, *args, **options):
        api_key = config("SCORECARD_API_KEY")
        schools = School.objects.exclude(unitid=None)

        for school in schools:
            params = {
                "api_key": api_key,
                "id": school.unitid,
                "fields": ",".join(["id", *FIELDS]),
            }
            try:
                response = requests.get(API_URL, params=params, timeout=30)
                response.raise_for_status()
            except requests.RequestException as e:
                self.stderr.write(f"ERROR {school}: {e}")
                continue

            results = response.json().get("results", [])
            if not results:
                self.stderr.write(f"NOT FOUND {school} ({school.unitid})")
                continue

            data = results[0]
            for api_field, model_field in FIELDS.items():
                value = data.get(api_field)
                if value is None:
                    continue
                if model_field == "website" and not value.startswith("http"):
                    value = "https://" + value
                if model_field in INTEGER_FIELDS:
                    value = int(value)
                setattr(school, model_field, value)

            school.scorecard_synced = timezone.now()
            school.save()
            self.stdout.write(f"OK {school}")
            time.sleep(0.2)

        self.stdout.write(self.style.SUCCESS("Done."))