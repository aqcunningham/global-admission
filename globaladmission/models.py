from django.db import models

# Create your models here.

class Verifiable(models.Model):
    """Every fact keeps where it came from and when it was last checked."""
    source_url = models.URLField(blank=True)
    last_verified = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        abstract = True


class School(Verifiable):
    class AidGroup(models.TextChoices):
        NEED_BLIND_FULL = "need_blind_full", "Need-blind + full need (intl)"
        NEED_AWARE_FULL = "need_aware_full", "Need-aware + full need (intl)"
        MERIT_ONLY = "merit_only", "Merit only"
        MERIT_TUITION_ONLY = "merit_tuition_only", "Merit only (tuition only)"
        TUITION_FREE = "tuition_free", "Tuition-free / special model"
        PARTIAL = "partial", "Partial aid only"

    unitid = models.PositiveIntegerField(
        unique=True, null=True, blank=True,
        help_text="IPEDS UNITID (blank if the school isn't in IPEDS)",
    )
    name = models.CharField(max_length=255, help_text="Display name")
    official_name = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=2, blank=True)
    website = models.URLField(blank=True)
    aid_group = models.CharField(max_length=32, choices=AidGroup.choices, blank=True)
    common_app_member = models.BooleanField(default=True)
    admission_rate = models.FloatField(null=True, blank=True)
    undergrad_size = models.PositiveIntegerField(null=True, blank=True)
    sat_average = models.PositiveIntegerField(null=True, blank=True)
    cost_of_attendance = models.PositiveIntegerField(null=True, blank=True)
    scorecard_synced = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

class Program(Verifiable):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="programs")
    cip_code = models.CharField(max_length=10, help_text="e.g. 1107")
    title = models.CharField(max_length=255)
    direct_admit = models.BooleanField(
        default=False,
        help_text="Students must apply to this program when applying to the school",
    )

    class Meta:
        ordering = ["school", "title"]
        unique_together = [("school", "cip_code")]

    def __str__(self):
        return f"{self.title} ({self.school})"