import time

import requests
from decouple import config
from django.core.management.base import BaseCommand

from globaladmission.models import Program, School

API_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"
PROGRAMS_FIELD = "latest.programs.cip_4_digit"
BACHELORS_LEVEL = 3  # Scorecard credential level 3 = bachelor's degree


class Command(BaseCommand):
    help = "Pull each school's bachelor's programs from the College Scorecard API"

    def handle(self, *args, **options):
        api_key = config("SCORECARD_API_KEY")
        total = 0

        for school in School.objects.exclude(unitid=None):
            params = {
                "api_key": api_key,
                "id": school.unitid,
                "fields": f"id,{PROGRAMS_FIELD}",
            }
            try:
                response = requests.get(API_URL, params=params, timeout=30)
                response.raise_for_status()
            except requests.RequestException as e:
                self.stderr.write(f"ERROR {school}: {e}")
                continue

            results = response.json().get("results", [])
            if not results:
                self.stderr.write(f"NOT FOUND {school}")
                continue

            programs = results[0].get(PROGRAMS_FIELD) or []
            count = 0
            for p in programs:
                credential = p.get("credential") or {}
                level = credential.get("level", p.get("credential.level"))
                if level != BACHELORS_LEVEL:
                    continue

                code = str(p.get("code") or "").strip()
                title = (p.get("title") or "").strip().rstrip(".")
                if not code or not title:
                    continue

                Program.objects.update_or_create(
                    school=school,
                    cip_code=code,
                    defaults={"title": title},
                )
                count += 1

            total += count
            self.stdout.write(f"OK {school}: {count} bachelor's programs")
            time.sleep(0.2)

        self.stdout.write(self.style.SUCCESS(f"Done. {total} programs saved."))