from django.contrib import admin

from .models import School


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "state", "unitid", "aid_group", "admission_rate", "undergrad_size", "sat_average", "scorecard_synced")
    list_filter = ("aid_group", "state", "common_app_member")
    search_fields = ("name", "official_name", "unitid")

    