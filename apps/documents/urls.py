from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DocumentViewSet, QuestionViewSet, RetrievalView


router = DefaultRouter()

router.register(
    "documents",
    DocumentViewSet,
    basename="document",
)

router.register(
    "questions",
    QuestionViewSet,
    basename="question",
)

urlpatterns = [
    path(
        "retrieval/",
        RetrievalView.as_view(),
        name="retrieval",
    ),
] + router.urls
