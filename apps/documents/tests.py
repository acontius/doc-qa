import shutil
import tempfile
from io import BytesIO
from unittest.mock import Mock, patch

from django.core.files.uploadedfile import (
    SimpleUploadedFile,
)
from django.test import TestCase, override_settings
from docx import Document as DocxDocument
from rest_framework import status
from rest_framework.test import APIClient

from .models import Document, DocumentChunk
from .services import (
    DocumentIngestionError,
    create_document,
    extract_docx_text,
    split_document_text,
    validate_docx_upload,
)


class DocumentTestMixin:
    def make_docx(
        self,
        paragraphs: list[str],
        table_rows: list[list[str]] | None = None,
    ) -> bytes:
        document = DocxDocument()

        for paragraph in paragraphs:
            document.add_paragraph(paragraph)

        if table_rows:
            table = document.add_table(
                rows=1,
                cols=len(table_rows[0]),
            )

            for row_index, row in enumerate(
                table_rows,
            ):
                if row_index == 0:
                    cells = table.rows[0].cells
                else:
                    cells = table.add_row().cells

                for cell, value in zip(
                    cells,
                    row,
                    strict=True,
                ):
                    cell.text = value

        buffer = BytesIO()
        document.save(buffer)

        return buffer.getvalue()

    def make_upload(
        self,
        content: bytes,
        name: str = "sample.docx",
    ) -> SimpleUploadedFile:
        return SimpleUploadedFile(
            name,
            content,
            content_type=(
                "application/"
                "vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
        )


class DocumentExtractionTests(
    DocumentTestMixin,
    TestCase,
):
    def test_extracts_paragraphs_and_tables(self):
        content = self.make_docx(
            paragraphs=[
                "اولین پاراگراف",
                "پاراگراف دوم",
            ],
            table_rows=[
                ["نام", "مقدار"],
                ["A", "100"],
            ],
        )

        uploaded_file = self.make_upload(
            content,
        )

        text = extract_docx_text(
            uploaded_file,
        )

        self.assertIn(
            "اولین پاراگراف",
            text,
        )

        self.assertIn(
            "پاراگراف دوم",
            text,
        )

        self.assertIn(
            "نام | مقدار",
            text,
        )

        self.assertIn(
            "A | 100",
            text,
        )

    def test_rejects_non_docx(self):
        uploaded_file = self.make_upload(
            b"hello",
            name="sample.pdf",
        )

        with self.assertRaises(
            DocumentIngestionError,
        ):
            validate_docx_upload(
                uploaded_file,
            )

    def test_rejects_oversized_file(self):
        content = b"x" * (
            10 * 1024 * 1024 + 1
        )

        uploaded_file = self.make_upload(
            content,
        )

        with self.assertRaises(
            DocumentIngestionError,
        ):
            validate_docx_upload(
                uploaded_file,
            )

    def test_rejects_empty_document(self):
        document = DocxDocument()

        buffer = BytesIO()
        document.save(buffer)

        uploaded_file = self.make_upload(
            buffer.getvalue(),
        )

        with self.assertRaises(
            DocumentIngestionError,
        ):
            extract_docx_text(
                uploaded_file,
            )


class ChunkingTests(TestCase):
    def test_chunking_removes_empty_chunks(self):
        text = (
            "این یک متن آزمایشی است. " * 300
        )

        chunks = split_document_text(
            text,
        )

        self.assertTrue(chunks)
        self.assertTrue(
            all(
                chunk.strip()
                for chunk in chunks
            )
        )

    def test_chunking_respects_configured_size(self):
        text = "A" * 3500

        chunks = split_document_text(
            text,
        )

        self.assertTrue(
            all(
                len(chunk) <= 1000
                for chunk in chunks
            )
        )


@override_settings(
    MEDIA_ROOT=tempfile.mkdtemp(),
)
class DocumentServiceTests(
    DocumentTestMixin,
    TestCase,
):
    @classmethod
    def tearDownClass(cls):
        media_root = cls._overridden_settings["MEDIA_ROOT"]
        super().tearDownClass()

        shutil.rmtree(
            media_root,
            ignore_errors=True,
        )

    @patch("apps.documents.services.get_embedding_service")
    def test_create_document_creates_chunks(
        self,
        mock_get_embedding_service,
    ):
        embedding_service = Mock()

        embedding_service.model_name = (
            "test-model"
        )

        embedding_service.embed_documents.side_effect = (
            lambda texts: [
                [0.01] * 384
                for _ in texts
            ]
        )

        mock_get_embedding_service.return_value = (
            embedding_service
        )

        content = self.make_docx(
            paragraphs=[
                "متن اول " * 100,
                "متن دوم " * 100,
            ],
        )

        uploaded_file = self.make_upload(
            content,
        )

        document = create_document(
            title="Test Document",
            uploaded_file=uploaded_file,
        )

        self.assertEqual(
            document.title,
            "Test Document",
        )

        self.assertTrue(
            document.full_text,
        )

        self.assertGreater(
            document.chunk_count,
            0,
        )

        self.assertEqual(
            document.chunks.count(),
            document.chunk_count,
        )

        first_chunk = document.chunks.first()

        self.assertEqual(
            len(first_chunk.embedding),
            384,
        )

    @patch("apps.documents.services.get_embedding_service")
    def test_document_replacement_removes_old_chunks(
        self,
        mock_get_embedding_service,
    ):
        embedding_service = Mock()
        embedding_service.model_name = "test-model"
        embedding_service.embed_documents.side_effect = (
            lambda texts: [
                [0.01] * 384
                for _ in texts
            ]
        )

        mock_get_embedding_service.return_value = (
            embedding_service
        )

        content = self.make_docx(
            paragraphs=[
                "متن اولیه " * 100,
            ],
        )

        uploaded_file = self.make_upload(
            content,
        )

        document = create_document(
            title="Original",
            uploaded_file=uploaded_file,
        )

        old_count = document.chunks.count()

        self.assertGreater(
            old_count,
            0,
        )

        new_content = self.make_docx(
            paragraphs=[
                "متن جدید " * 200,
            ],
        )

        new_file = self.make_upload(
            new_content,
        )

        from .services import update_document

        updated = update_document(
            document,
            title="Updated",
            uploaded_file=new_file,
        )

        self.assertEqual(
            updated.title,
            "Updated",
        )

        self.assertTrue(
            updated.full_text.startswith(
                "متن جدید",
            )
        )

        self.assertEqual(
            updated.chunks.count(),
            updated.chunk_count,
        )


class DocumentAPITests(
    DocumentTestMixin,
    TestCase,
):
    def setUp(self):
        self.client = APIClient()

    @patch("apps.documents.services.get_embedding_service")
    def test_create_document_api(
        self,
        mock_get_embedding_service,
    ):
        embedding_service = Mock()
        embedding_service.model_name = "test-model"
        embedding_service.embed_documents.side_effect = (
            lambda texts: [
                [0.01] * 384
                for _ in texts
            ]
        )

        mock_get_embedding_service.return_value = (
            embedding_service
        )

        content = self.make_docx(
            paragraphs=[
                "محتوای سند آزمایشی " * 100,
            ],
        )

        response = self.client.post(
            "/api/documents/",
            {
                "title": "سند آزمایشی",
                "file": self.make_upload(content),
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            Document.objects.count(),
            1,
        )

        self.assertGreater(
            DocumentChunk.objects.count(),
            0,
        )

    def test_reject_invalid_file(self):
        response = self.client.post(
            "/api/documents/",
            {
                "title": "Invalid",
                "file": self.make_upload(
                    b"not a docx",
                    name="evil.exe",
                ),
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    @patch("apps.documents.services.get_embedding_service")
    def test_list_documents(
        self,
        mock_get_embedding_service,
    ):
        embedding_service = Mock()
        embedding_service.model_name = "test-model"
        embedding_service.embed_documents.side_effect = (
            lambda texts: [
                [0.01] * 384
                for _ in texts
            ]
        )

        mock_get_embedding_service.return_value = (
            embedding_service
        )

        content = self.make_docx(
            paragraphs=["hello " * 100],
        )

        self.client.post(
            "/api/documents/",
            {
                "title": "Document One",
                "file": self.make_upload(content),
            },
            format="multipart",
        )

        response = self.client.get(
            "/api/documents/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_document_not_found(self):
        response = self.client.get(
            "/api/documents/999999/",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertEqual(
            response.data["error"]["code"],
            "not_found",
        )