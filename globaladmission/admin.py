from django.contrib import admin

from .models import School, Program

class ProgramInline(admin.TabularInline):
    model = Program
    extra = 0
    fields = ("title", "cip_code", "direct_admit")
    
@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "state", "unitid", "aid_group", "admission_rate", "undergrad_size", "sat_average", "scorecard_synced")
    list_filter = ("aid_group", "state", "common_app_member")
    search_fields = ("name", "official_name", "unitid")
    inlines = [ProgramInline]

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("title", "school", "cip_code", "direct_admit")
    list_filter = ("direct_admit", "school")
    search_fields = ("title", "cip_code", "school__name")