from django.contrib import admin

from .models import CommunityResource


@admin.register(CommunityResource)
class CommunityResourceAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "city",
        "state",
        "active",
        "wheelchair_accessible",
    ]
    list_filter = ["active", "wheelchair_accessible", "state"]
    search_fields = ["name", "city", "description"]