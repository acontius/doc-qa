from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DocumentViewSet, RetrievalView


router = DefaultRouter()

router.register(
    "documents",
    DocumentViewSet,
    basename="document",
)

urlpatterns = [
    path(
        "retrieval/",
        RetrievalView.as_view(),
        name="retrieval",
    ),
] + router.urls
