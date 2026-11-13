import csv

from django.core.management.base import BaseCommand

from globaladmission.models import School


class Command(BaseCommand):
    help = "Load schools from unitid_matched.csv (safe to re-run)"

    def add_arguments(self, parser):
        parser.add_argument("csv_path")

    def handle(self, *args, **options):
        created = updated = skipped = 0
        with open(options["csv_path"], newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                name = (row.get("input_name") or row.get("name") or "").strip()
                if not name:
                    skipped += 1
                    continue
                unitid = (row.get("unitid") or "").strip()
                defaults = {
                    "name": name,
                    "official_name": (row.get("official_name") or "").strip(),
                    "city": (row.get("city") or "").strip(),
                    "state": (row.get("state") or "").strip().upper()[:2],
                }
                aid_group = (row.get("aid_group") or "").strip()
                if aid_group:
                    defaults["aid_group"] = aid_group

                if unitid:
                    _, is_new = School.objects.update_or_create(unitid=int(unitid), defaults=defaults)
                else:
                    _, is_new = School.objects.update_or_create(name=name, defaults=defaults)
                created += is_new
                updated += not is_new

        self.stdout.write(self.style.SUCCESS(
            f"Created {created}, updated {updated}, skipped {skipped}"
        ))