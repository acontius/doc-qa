from django import forms

from .models import Document
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