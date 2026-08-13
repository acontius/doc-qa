import logging

from django.conf import settings
from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView


logger = logging.getLogger(__name__)


class HealthResponseSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["ok", "degraded"])
    db = serializers.ChoiceField(choices=["ok", "error"])
    vector = serializers.ChoiceField(choices=["ok", "not_installed", "error"])
    llm_configured = serializers.BooleanField()


@extend_schema(
    tags=["health"],
    summary="Service health",

    responses=HealthResponseSerializer,
    description="Returns application and dependency health status.",
)
class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        database_status = "ok"
        vector_status = "ok"

        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            database_status = "error"
            logger.exception("Health check: database connection failed")

        # Check pgvector extension (only if DB is reachable)
        if database_status == "ok":
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT EXISTS (
                            SELECT 1
                            FROM pg_extension
                            WHERE extname = 'vector'
                        )
                        """
                    )
                    vector_installed = cursor.fetchone()[0]

                if not vector_installed:
                    vector_status = "not_installed"
            except Exception:
                vector_status = "error"
                logger.exception("Health check: pgvector extension check failed")

        # Check LLM configuration (no external call, just env vars)
        llm_configured = bool(
            settings.OPENROUTER_API_KEY
            and settings.OPENROUTER_MODEL
        )

        response = {
            "status": "ok" if database_status == "ok" else "degraded",
            "db": database_status,
            "vector": vector_status,
            "llm_configured": llm_configured,
        }

        return Response(response)