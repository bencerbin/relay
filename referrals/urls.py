from django.urls import path

from .views import RecommendationView

urlpatterns = [
    path(
        "recommendations/",
        RecommendationView.as_view(),
        name="recommendations",
    ),
]

# from django.contrib import admin
# from django.urls import include, path

# urlpatterns = [
#     path("admin/", admin.site.urls),
#     path("api/", include("referrals.urls")),
# ]