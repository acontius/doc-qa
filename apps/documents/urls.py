from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DocumentViewSet, QuestionView, RetrievalView


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
    path(
        "questions/",
        QuestionView.as_view(),
        name="questions",
    ),
] + router.urls
