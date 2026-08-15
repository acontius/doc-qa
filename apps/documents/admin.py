import logging

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse

from .forms import DocumentAdminForm, QuestionAdminForm
from .models import Answer, Document, DocumentChunk, Question
from .services import (
    DocumentIngestionError,
    DocumentRetrievalError,
    RAGError,
    ask_and_persist_question,
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
        "id",
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
                messages.error(
                    request,
                    f"{document}: {exc.message}",
                )
            except Exception:
                failure_count += 1
                logger.exception(
                    "Unexpected reindex failure",
                    extra={
                        "document_id": document.pk,
                    },
                )
                messages.error(
                    request,
                    f"{document}: خطای غیرمنتظره در بازسازی.",
                )

        if success_count:
            messages.success(
                request,
                f"{success_count} سند با موفقیت بازسازی شد.",
            )

        if failure_count and not success_count:
            messages.warning(
                request,
                "هیچ سندی بازسازی نشد.",
            )


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "document",
        "chunk_index",
        "created_at",
    )

    list_filter = (
        "document",
    )

    search_fields = (
        "text",
        "document__title",
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


class AnswerInline(admin.StackedInline):
    """Read-only Answer on the Question *change* page only."""

    model = Answer
    extra = 0
    can_delete = False
    show_change_link = True
    fields = (
        "text",
        "confidence",
        "model_name",
        "latency_ms",
        "error",
        "sources_json",
        "raw_llm_output",
        "created_at",
    )
    readonly_fields = fields

    def has_add_permission(self, request, obj=None) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """
    Add Question = operator UI over ask_and_persist_question
    (same path as POST /api/questions/).

    Change page = immutable history + read-only Answer.
    """

    form = QuestionAdminForm

    list_display = (
        "id",
        "short_text",
        "top_k",
        "answer_preview",
        "confidence_display",
        "has_error_display",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("text", "answer__text", "answer__error")
    ordering = ("-created_at",)
    list_select_related = ("answer",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("answer")

    def get_inlines(self, request, obj=None):
        # Critical: no inline on ADD — Admin would require inline
        # management-form POST fields and never call save_model.
        if obj is None:
            return []
        return [AnswerInline]

    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return (
                "text",
                "top_k",
                "document_ids",
                "created_at",
            )
        return ()

    def get_fields(self, request, obj=None):
        if obj is None:
            return (
                "text",
                "top_k",
                "documents",
            )
        return (
            "text",
            "top_k",
            "document_ids",
            "created_at",
        )

    def save_form(self, request, form, change):
        if not change:
            # Persistence is owned by the service.
            return Question()
        return super().save_form(request, form, change)

    def save_model(self, request, obj, form, change):
        if change:
            messages.info(
                request,
                "سوابق سؤال پس از ایجاد قابل ویرایش نیستند.",
            )
            return

        text = form.cleaned_data["text"]
        top_k = form.cleaned_data.get("top_k")
        document_ids = form.get_document_ids()

        try:
            question_row, _result = ask_and_persist_question(
                text,
                top_k=top_k,
                document_ids=document_ids,
            )
        except DocumentRetrievalError as exc:
            messages.error(request, exc.message)
            raise
        except RAGError as exc:
            persisted = getattr(exc, "persisted_question", None)
            if persisted is not None:
                obj.pk = persisted.pk
                obj.refresh_from_db()
            messages.error(
                request,
                getattr(exc, "message", str(exc)),
            )
            # History already written; do not re-raise.
            return
        except Exception:
            logger.exception("Unexpected admin question save failure")
            messages.error(
                request,
                "پردازش سؤال با خطای غیرمنتظره مواجه شد.",
            )
            raise

        obj.pk = question_row.pk
        obj.refresh_from_db()
        messages.success(
            request,
            "سؤال با موفقیت پردازش شد.",
        )

    def save_related(self, request, form, formsets, change):
        """
        On add we do not call form.save(), so Django never attaches form.save_m2m.
        'documents' is a non-model form field (mapped to document_ids in the service).
        Skip the default form.save_m2m() call on add.
        """
        if not change:
            for formset in formsets:
                self.save_formset(request, form, formset, change=change)
            return

        if hasattr(form, "save_m2m"):
            super().save_related(request, form, formsets, change)
            return

        for formset in formsets:
            self.save_formset(request, form, formset, change=change)

    def response_add(self, request, obj, post_url_continue=None):
        if obj.pk:
            return HttpResponseRedirect(
                reverse(
                    "admin:documents_question_change",
                    args=[obj.pk],
                )
            )
        return super().response_add(request, obj, post_url_continue)

    @admin.display(description="question")
    def short_text(self, obj: Question) -> str:
        if len(obj.text) <= 80:
            return obj.text
        return obj.text[:77] + "…"

    @admin.display(description="answer")
    def answer_preview(self, obj: Question) -> str:
        answer = getattr(obj, "answer", None)
        if answer is None:
            return "—"
        if answer.error and not answer.text:
            return "(error)"
        text = answer.text or ""
        if len(text) <= 60:
            return text or "—"
        return text[:57] + "…"

    @admin.display(description="confidence")
    def confidence_display(self, obj: Question) -> str:
        answer = getattr(obj, "answer", None)
        return answer.confidence if answer else "—"

    @admin.display(boolean=True, description="error")
    def has_error_display(self, obj: Question) -> bool:
        answer = getattr(obj, "answer", None)
        return bool(answer and answer.error)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "question_id",
        "question_preview",
        "answer_preview",
        "confidence",
        "model_name",
        "latency_ms",
        "has_error",
        "created_at",
    )
    list_filter = ("confidence", "created_at")
    search_fields = ("text", "error", "model_name", "question__text")
    ordering = ("-created_at",)
    list_select_related = ("question",)
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

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    @admin.display(boolean=True, description="error")
    def has_error(self, obj: Answer) -> bool:
        return bool(obj.error)

    @admin.display(description="question")
    def question_preview(self, obj: Answer) -> str:
        text = obj.question.text if obj.question_id else ""
        if len(text) <= 50:
            return text
        return text[:47] + "…"

    @admin.display(description="answer")
    def answer_preview(self, obj: Answer) -> str:
        if obj.error and not obj.text:
            return "(error)"
        text = obj.text or ""
        if len(text) <= 50:
            return text or "—"
        return text[:47] + "…"
