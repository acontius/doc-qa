import logging

from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.parsers import (
    FormParser,
    JSONParser,
    MultiPartParser,
)
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Document, Question
from .serializers import (
    DocumentDetailSerializer,
    DocumentListSerializer,
    DocumentWriteSerializer,
    RetrievalRequestSerializer,
    RetrievalResponseSerializer,
    QuestionRequestSerializer,
    QuestionResponseSerializer,
    QuestionListSerializer,
    QuestionDetailSerializer,
    APIErrorSerializer,
)
from .services import (
    DocumentIngestionError,
    DocumentRetrievalError,
    RAGError,
    answer_question,
    ask_and_persist_question,
    create_document,
    delete_document,
    reindex_document,
    retrieve_chunks,
    update_document,
)

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        tags=["documents"],
        summary="List documents",
        description=(
            "Paginated list of indexed documents. "
            "Default page size is 20 (PageNumberPagination)."
        ),
        responses={200: DocumentListSerializer, 400: APIErrorSerializer},
    ),
    retrieve=extend_schema(
        tags=["documents"],
        summary="Get document",
        description="Return a document and its extracted full text.",
        responses={200: DocumentDetailSerializer, 404: APIErrorSerializer},
    ),
    create=extend_schema(
        tags=["documents"],
        summary="Upload DOCX document",
        description=(
            "Upload and synchronously index a DOCX file.\n\n"
            "Content-Type: multipart/form-data\n"
            "- title (required)\n"
            "- file (required, .docx only)\n"
            "Max size: MAX_UPLOAD_SIZE_MB.\n\n"
            "Pipeline: validate → extract → chunk → embed → pgvector."
        ),
        request=DocumentWriteSerializer,
        responses={
            201: DocumentDetailSerializer,
            400: APIErrorSerializer,
            500: APIErrorSerializer,
        },
    ),
    update=extend_schema(
        tags=["documents"],
        summary="Replace document (PUT)",
        responses={
            200: DocumentDetailSerializer,
            400: APIErrorSerializer,
            404: APIErrorSerializer,
        },
    ),
    partial_update=extend_schema(
        tags=["documents"],
        summary="Update document (PATCH)",
        description=(
            "PATCH title only: metadata, no reindex. "
            "PATCH with file: full re-ingestion."
        ),
        responses={
            200: DocumentDetailSerializer,
            400: APIErrorSerializer,
            404: APIErrorSerializer,
        },
    ),
    destroy=extend_schema(
        tags=["documents"],
        summary="Delete document",
        description="Delete document, chunks, and stored DOCX file.",
        responses={
            204: OpenApiResponse(description="Deleted"),
            404: APIErrorSerializer,
        },
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
        tags=["documents"],
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



class RetrievalView(APIView):
    """
    Hybrid retrieval over indexed document chunks.
    Does not call an LLM.
    """

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
            return response

        logger.exception("Unhandled exception in Retrieval API")
        return Response(
            {
                "error": {
                    "code": "internal_error",
                    "message": "خطای داخلی سرور رخ داد.",
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @extend_schema(
        tags=["retrieval"],
        summary="Retrieve relevant chunks",
        description=(
            "Hybrid retrieval only (no LLM).\n\n"
            "Embed question → pgvector cosine candidates "
            "(top_k * RETRIEVER_CANDIDATE_MULTIPLIER) → "
            "keyword score → final_score = 0.7*vector + 0.3*keyword → top_k.\n\n"
            "Optional document_ids limits search to specific documents."
        ),
        request=RetrievalRequestSerializer,
        responses={
            200: RetrievalResponseSerializer,
            400: APIErrorSerializer,
            500: APIErrorSerializer,
        },
        examples=[
            OpenApiExample(
                "Persian question",
                value={
                    "question": "میزان مرخصی سالانه کارکنان چقدر است؟",
                    "top_k": 6,
                },
                request_only=True,
            ),
            OpenApiExample(
                "Filtered documents",
                value={
                    "question": "ساعات کاری چیست؟",
                    "top_k": 3,
                    "document_ids": [1, 2],
                },
                request_only=True,
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        serializer = RetrievalRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data["question"]
        top_k = serializer.validated_data.get("top_k")
        document_ids = serializer.validated_data.get("document_ids")

        try:
            results = retrieve_chunks(
                question,
                top_k=top_k,
                document_ids=document_ids,
            )
        except DocumentRetrievalError as exc:
            return Response(
                {
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
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
            logger.exception("Unexpected retrieval failure")
            return Response(
                {
                    "error": {
                        "code": "retrieval_failed",
                        "message": "بازیابی اطلاعات با خطا مواجه شد.",
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        payload = {
            "question": question,
            "results": [
                {
                    "document_id": item.document_id,
                    "document_title": item.document_title,
                    "chunk_index": item.chunk_index,
                    "text": item.text,
                    "distance": item.distance,
                    "vector_score": item.vector_score,
                    "keyword_score": item.keyword_score,
                    "final_score": item.final_score,
                }
                for item in results
            ],
        }

        return Response(payload, status=status.HTTP_200_OK)


class QuestionViewSet(viewsets.GenericViewSet):
    """
    Ask grounded questions (with history) and browse past Q&A.
    """

    queryset = Question.objects.select_related("answer").all()

    def get_serializer_class(self):
        if self.action == "create":
            return QuestionRequestSerializer
        if self.action == "list":
            return QuestionListSerializer
        return QuestionDetailSerializer


    @extend_schema(
        tags=["questions"],
        summary="Ask a grounded question",
        description=(
            "Full RAG with history persistence.\n\n"
            "1. Validate + create Question\n"
            "2. Hybrid retrieval\n"
            "3. LLM if context exists (OpenRouter via LangChain)\n"
            "4. Persist Answer snapshot\n"
            "5. Return answer + sources + confidence\n\n"
            "Empty retrieval → no LLM call → "
            "در اسناد ارائه‌شده پاسخی یافت نشد.\n\n"
            "LLM failures return 503; Question history is still kept."
        ),
        request=QuestionRequestSerializer,
        responses={
            200: QuestionResponseSerializer,
            400: APIErrorSerializer,
            503: APIErrorSerializer,
            500: APIErrorSerializer,
        },
        examples=[
            OpenApiExample(
                "Simple Persian question",
                value={
                    "question": "این سند درباره چیست؟",
                    "top_k": 3,
                },
                request_only=True,
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        serializer = QuestionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            question_row, result = ask_and_persist_question(
                data["question"],
                top_k=data.get("top_k"),
                document_ids=data.get("document_ids"),
            )
        except (DocumentRetrievalError, DocumentIngestionError, RAGError) as exc:
            code = getattr(exc, "code", "qa_error")
            status_code = status.HTTP_400_BAD_REQUEST
            if code in {
                "llm_not_configured",
                "llm_init_failed",
                "llm_request_failed",
                "llm_empty_response",
            }:
                status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return Response(
                {
                    "error": {
                        "code": code,
                        "message": getattr(exc, "message", str(exc)),
                    }
                },
                status=status_code,
            )
        except Exception:
            logger.exception("Unexpected QA failure")
            return Response(
                {
                    "error": {
                        "code": "qa_failed",
                        "message": "پاسخ‌گویی با خطا مواجه شد.",
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        payload = {
            "id": question_row.id,
            "question": result.question,
            "answer": result.answer,
            "sources": [
                {
                    "document_id": src.document_id,
                    "document_title": src.document_title,
                    "chunk_index": src.chunk_index,
                    "excerpt": src.excerpt,
                }
                for src in result.sources
            ],
            "confidence": result.confidence,
            "latency_ms": result.latency_ms,
        }
        return Response(payload, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["questions"],
        summary="List question history",
        description=(
            "Paginated Q&A history (newest first). "
            "Lightweight: no raw_llm_output. Page size 20."
        ),
        responses={200: QuestionListSerializer},
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = QuestionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = QuestionListSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["questions"],
        summary="Get question history detail",
        description=(
            "Full history entry including answer text, sources snapshot, "
            "raw_llm_output, confidence, model_name, latency, error."
        ),
        responses={
            200: QuestionDetailSerializer,
            404: APIErrorSerializer,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_queryset().get(pk=kwargs.get("pk"))
        except Question.DoesNotExist:
            return Response(
                {
                    "error": {
                        "code": "question_not_found",
                        "message": "سؤال موردنظر یافت نشد.",
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = QuestionDetailSerializer(instance)
        return Response(serializer.data)

