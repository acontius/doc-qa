from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.db import connection

class HealthResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    db = serializers.CharField()
    vector = serializers.CharField()
    llm_configured = serializers.BooleanField()


@extend_schema(
    responses=HealthResponseSerializer,
    description="Returns application and dependency health status.",
)

class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        database_status = "ok"
        vector_status = "ok"
        database_error = None
        vector_error = None

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception as exc:
            database_status = "error"
            database_error = str(exc)

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
            except Exception as exc:
                vector_status = "error"
                vector_error = str(exc)

        llm_configured = bool(
            settings.OPENROUTER_API_KEY
            and settings.OPENROUTER_MODEL
        )

        response = {
            "status": (
                "ok"
                if database_status == "ok"
                else "degraded"
            ),
            "db": database_status,
            "vector": vector_status,
            "llm_configured": llm_configured,
        }

        if database_error:
            response["db_error"] = database_error

        if vector_error:
            response["vector_error"] = vector_error

        return Response(response)