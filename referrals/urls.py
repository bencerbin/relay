from django.urls import path

from .views import IntakeView, RecommendationView

urlpatterns = [
    path(
        "recommendations/",
        RecommendationView.as_view(),
        name="recommendations",
    ),
    path(
        "intake/",
        IntakeView.as_view(),
        name="intake",
    ),
    path(
        "intake/sessions/<uuid:session_id>/search/",
        SessionSearch.as_view(),
        name="session-search"
    )
]

# from django.contrib import admin
# from django.urls import include, path

# urlpatterns = [
#     path("admin/", admin.site.urls),
#     path("api/", include("referrals.urls")),
# ]