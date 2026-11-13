from django.contrib import admin

from .models import School


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "state", "unitid", "aid_group", "common_app_member", "last_verified")
    list_filter = ("aid_group", "state", "common_app_member")
    search_fields = ("name", "official_name", "unitid")