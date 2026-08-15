from django import forms
from django.conf import settings

from .models import Document, Question
from .services import (
    DocumentIngestionError,
    extract_docx_text,
    validate_docx_upload,
)


class DocumentAdminForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = [
            "title",
            "file",
        ]

    def clean_title(self) -> str:
        value = self.cleaned_data["title"].strip()

        if not value:
            raise forms.ValidationError(
                "عنوان سند نمی‌تواند خالی باشد."
            )

        return value

    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")

        if uploaded_file is None:
            return uploaded_file

        try:
            validate_docx_upload(
                uploaded_file,
            )

            extract_docx_text(
                uploaded_file,
            )

        except DocumentIngestionError as exc:
            raise forms.ValidationError(
                exc.message,
            ) from exc

        return uploaded_file


class QuestionAdminForm(forms.ModelForm):
    """
    Admin form for asking a question.

    Selected Documents are converted to document_ids for
    ask_and_persist_question (None = search all documents).
    """

    text = forms.CharField(
        label="سؤال",
        required=True,
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "cols": 80,
                "style": "width: 90%;",
                "dir": "auto",
            },
        ),
        help_text="سؤال فارسی یا انگلیسی.",
    )

    top_k = forms.IntegerField(
        label="Top K",
        required=False,
        min_value=1,
        max_value=50,
        help_text=(
            f"تعداد نتایج بازیابی "
            f"(پیش‌فرض: {settings.RETRIEVER_TOP_K}، حداکثر: 50). "
            "خالی = پیش‌فرض تنظیمات."
        ),
    )

    documents = forms.ModelMultipleChoiceField(
        label="اسناد",
        queryset=Document.objects.all().order_by("-created_at"),
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "size": 12,
                "style": "min-width: 28rem;",
            },
        ),
        help_text="خالی بگذارید تا همه اسناد جستجو شوند.",
    )

    class Meta:
        model = Question
        fields = [
            "text",
            "top_k",
        ]

    def clean_text(self) -> str:
        value = (self.cleaned_data.get("text") or "").strip()

        if not value:
            raise forms.ValidationError(
                "سؤال نمی‌تواند خالی باشد."
            )

        return value

    def clean_top_k(self):
        value = self.cleaned_data.get("top_k")

        if value is None or value == "":
            return None

        return value

    def get_document_ids(self) -> list[int] | None:
        documents = self.cleaned_data.get("documents")

        if not documents:
            return None

        ids = list(documents.values_list("pk", flat=True))
        return ids or None
