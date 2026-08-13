import logging

from django.contrib import admin, messages

from .forms import DocumentAdminForm
from .models import Answer, Document, DocumentChunk, Question
from .services import (
    DocumentIngestionError,
    create_document,
    delete_document,
    reindex_document,
    update_document,
)

logger = logging.getLogger(__name__)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    form = DocumentAdminForm

    list_display = (
        "title",
        "chunk_count",
        "embedding_model",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "title",
        "full_text",
    )

    readonly_fields = (
        "full_text",
        "chunk_count",
        "embedding_model",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    actions = [
        "reindex_selected_documents",
    ]

    def save_model(
        self,
        request,
        obj,
        form,
        change,
    ):
        title = form.cleaned_data["title"]
        uploaded_file = form.cleaned_data.get("file")

        try:
            if not change:
                created = create_document(
                    title=title,
                    uploaded_file=uploaded_file,
                )

                obj.pk = created.pk
                obj.refresh_from_db()

                return

            current = Document.objects.get(
                pk=obj.pk,
            )

            if uploaded_file is not None:
                update_document(
                    current,
                    title=title,
                    uploaded_file=uploaded_file,
                )
            else:
                current.title = title

                current.save(
                    update_fields=[
                        "title",
                        "updated_at",
                    ]
                )

            obj.refresh_from_db()

        except DocumentIngestionError as exc:
            messages.error(
                request,
                exc.message,
            )
            raise

        except Exception:
            logger.exception(
                "Unexpected admin document save failure",
            )
            raise

    def delete_model(
        self,
        request,
        obj,
    ):
        delete_document(obj)

    def delete_queryset(
        self,
        request,
        queryset,
    ):
        for document in queryset:
            delete_document(document)

    @admin.action(
        description="Reindex selected documents",
    )
    def reindex_selected_documents(
        self,
        request,
        queryset,
    ):
        success_count = 0
        failure_count = 0

        for document in queryset:
            try:
                reindex_document(document)
                success_count += 1

            except DocumentIngestionError as exc:
                failure_count += 1

                self.message_user(
                    request,
                    (
                        f"{document.title}: "
                        f"{exc.message}"
                    ),
                    level=messages.ERROR,
                )

            except Exception:
                failure_count += 1

                logger.exception(
                    "Admin reindex failed for document %s",
                    document.pk,
                )

                self.message_user(
                    request,
                    (
                        f"{document.title}: "
                        "خطای داخلی هنگام reindex."
                    ),
                    level=messages.ERROR,
                )

        if success_count:
            self.message_user(
                request,
                (
                    f"{success_count} سند با موفقیت "
                    "reindex شد."
                ),
                level=messages.SUCCESS,
            )

        if failure_count:
            self.message_user(
                request,
                (
                    f"{failure_count} سند با خطا مواجه شد."
                ),
                level=messages.WARNING,
            )


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = (
        "document",
        "chunk_index",
        "created_at",
    )

    search_fields = (
        "document__title",
        "text",
    )

    readonly_fields = (
        "document",
        "chunk_index",
        "text",
        "embedding",
        "created_at",
    )

    ordering = (
        "document_id",
        "chunk_index",
    )

    def has_add_permission(
        self,
        request,
    ) -> bool:
        return False

    def has_change_permission(
        self,
        request,
        obj=None,
    ) -> bool:
        return False

    def has_delete_permission(
        self,
        request,
        obj=None,
    ) -> bool:
        return False

    def has_view_permission(
        self,
        request,
        obj=None,
    ) -> bool:
        return True


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "short_text",
        "top_k",
        "created_at",
    )
    search_fields = ("text",)
    ordering = ("-created_at",)
    readonly_fields = (
        "text",
        "top_k",
        "document_ids",
        "created_at",
    )

    @admin.display(description="question")
    def short_text(self, obj: Question) -> str:
        if len(obj.text) <= 80:
            return obj.text
        return obj.text[:77] + "…"


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "question_id",
        "confidence",
        "model_name",
        "latency_ms",
        "has_error",
        "created_at",
    )
    search_fields = ("text", "error", "model_name")
    ordering = ("-created_at",)
    readonly_fields = (
        "question",
        "text",
        "raw_llm_output",
        "confidence",
        "sources_json",
        "model_name",
        "latency_ms",
        "error",
        "created_at",
    )

    @admin.display(boolean=True, description="error")
    def has_error(self, obj: Answer) -> bool:
        return bool(obj.error)

