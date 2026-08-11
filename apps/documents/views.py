import logging

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
)
from rest_framework import status, viewsets
from rest_framework.parsers import (
    FormParser,
    JSONParser,
    MultiPartParser,
)
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Document
from .serializers import (
    DocumentDetailSerializer,
    DocumentListSerializer,
    DocumentWriteSerializer,
)
from .services import (
    DocumentIngestionError,
    create_document,
    delete_document,
    reindex_document,
    update_document,
)

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="List documents",
        description="Return a paginated list of indexed documents.",
    ),
    retrieve=extend_schema(
        summary="Get document",
        description="Return a document and its extracted full text.",
    ),
    create=extend_schema(
        summary="Upload DOCX document",
        description=(
            "Upload and synchronously index a DOCX document."
        ),
    ),
    update=extend_schema(
        summary="Replace document",
    ),
    partial_update=extend_schema(
        summary="Update document",
    ),
    destroy=extend_schema(
        summary="Delete document",
    ),
)
class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]

    def get_serializer_class(self):
        if self.action == "list":
            return DocumentListSerializer

        if self.action == "retrieve":
            return DocumentDetailSerializer

        return DocumentWriteSerializer

    def handle_exception(self, exc):
        response = super().handle_exception(exc)

        if response is not None:
            if response.status_code == status.HTTP_400_BAD_REQUEST:
                response.data = {
                    "error": {
                        "code": "validation_error",
                        "message": "اطلاعات ارسالی معتبر نیست.",
                        "details": response.data,
                    }
                }

            elif response.status_code == status.HTTP_404_NOT_FOUND:
                response.data = {
                    "error": {
                        "code": "not_found",
                        "message": "سند موردنظر پیدا نشد.",
                    }
                }

            return response

        logger.exception(
            "Unhandled exception in Document API",
        )

        return Response(
            {
                "error": {
                    "code": "internal_error",
                    "message": "خطای داخلی سرور رخ داد.",
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        try:
            document = create_document(
                title=serializer.validated_data["title"],
                uploaded_file=serializer.validated_data["file"],
            )

        except DocumentIngestionError as exc:
            return Response(
                {
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            logger.exception(
                "Unexpected document creation failure",
            )

            return Response(
                {
                    "error": {
                        "code": "document_creation_failed",
                        "message": "ایجاد سند با خطا مواجه شد.",
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        output = DocumentDetailSerializer(
            document,
        )

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )

    def update(
        self,
        request,
        *args,
        **kwargs,
    ):
        partial = kwargs.pop(
            "partial",
            False,
        )

        document = self.get_object()

        serializer = self.get_serializer(
            document,
            data=request.data,
            partial=partial,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        title = serializer.validated_data.get(
            "title",
            document.title,
        )

        uploaded_file = serializer.validated_data.get(
            "file",
        )

        try:
            document = update_document(
                document,
                title=title,
                uploaded_file=uploaded_file,
            )

        except DocumentIngestionError as exc:
            return Response(
                {
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            logger.exception(
                "Unexpected document update failure",
            )

            return Response(
                {
                    "error": {
                        "code": "document_update_failed",
                        "message": "ویرایش سند با خطا مواجه شد.",
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        output = DocumentDetailSerializer(
            document,
        )

        return Response(output.data)

    def destroy(
        self,
        request,
        *args,
        **kwargs,
    ):
        document = self.get_object()

        try:
            delete_document(document)

        except Exception:
            logger.exception(
                "Unexpected document deletion failure",
            )

            return Response(
                {
                    "error": {
                        "code": "document_deletion_failed",
                        "message": "حذف سند با خطا مواجه شد.",
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="reindex",
    )
    @extend_schema(
        summary="Reindex document",
        description=(
            "Re-extract, rechunk, and re-embed the stored DOCX file."
        ),
        request=None,
        responses=DocumentDetailSerializer,
    )
    def reindex(
        self,
        request,
        pk=None,
    ):
        document = self.get_object()

        try:
            document = reindex_document(
                document,
            )

        except DocumentIngestionError as exc:
            return Response(
                {
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception:
            logger.exception(
                "Unexpected document reindex failure",
            )

            return Response(
                {
                    "error": {
                        "code": "document_reindex_failed",
                        "message": "بازسازی ایندکس سند با خطا مواجه شد.",
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            DocumentDetailSerializer(document).data,
        )