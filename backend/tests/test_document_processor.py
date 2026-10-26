import pytest

from backend.main import DocumentProcessor


def test_clean_page_text_keeps_numeric_values():
    text = "Page 2 of 10\nMonthly allowance\n25\nINR 2000"
    cleaned = DocumentProcessor.clean_page_text(text)
    assert "25" in cleaned
    assert "INR 2000" in cleaned
    assert "Page 2 of 10" not in cleaned


def test_chunker_preserves_lines_and_page_provenance():
    chunks = DocumentProcessor.semantic_chunk(
        "Eligibility\nAll full-time employees are eligible.\n\nNo annual referral limit.",
        page_num=7,
        chunk_size=100,
        overlap=10,
    )
    assert len(chunks) == 1
    assert chunks[0]["page_number"] == 7
    assert "Eligibility\nAll full-time employees are eligible." in chunks[0]["content"]
    assert "No annual referral limit." in chunks[0]["content"]


def test_ocr_skips_decorative_title_slides():
    class Rect:
        width = 50
        height = 50

    class Page:
        rect = Rect()

        def get_images(self, full=False):
            return [(123,)]

        def get_image_rects(self, _xref):
            return [Rect()]

    assert not DocumentProcessor._page_needs_ocr(Page(), "Trip ID Creation")


@pytest.mark.asyncio
async def test_parse_pdf_ocr_adds_text_from_large_embedded_images(
    monkeypatch, tmp_path
):
    import pymupdf

    class Rect:
        width = 50
        height = 50

    class Page:
        rect = Rect()

        def get_text(self, _kind, textpage=None, sort=False):
            if textpage is None:
                return "Travel details shown in screenshot."
            return "Travel details shown in screenshot.\nPassport expiry date\nTrip end date"

        def get_images(self, full=False):
            return [(123,)]

        def get_image_rects(self, _xref):
            return [Rect()]

        def get_textpage_ocr(self, language, dpi, full):
            assert language == "eng"
            assert dpi == 300
            assert full is False
            return object()

    class Document:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def __iter__(self):
            return iter([Page()])

    monkeypatch.setattr(pymupdf, "open", lambda _path: Document())
    parsed = await DocumentProcessor.parse_pdf(str(tmp_path / "travel.pdf"))

    assert len(parsed) == 1
    assert parsed[0][1] == 1
    assert "Passport expiry date" in parsed[0][0]
    assert "Trip end date" in parsed[0][0]


def test_rapid_ocr_filters_low_confidence_and_orders_text(monkeypatch):
    import rapidocr_onnxruntime

    class FakeRapidOCR:
        def __call__(self, _image):
            return (
                [
                    ([[10, 30], [40, 30], [40, 40], [10, 40]], "second row", 0.95),
                    ([[10, 10], [40, 10], [40, 20], [10, 20]], "first row", 0.95),
                    ([[50, 10], [80, 10], [80, 20], [50, 20]], "noise", 0.40),
                ],
                None,
            )

    class Pixmap:
        samples = bytes([0, 0, 0])
        height = 1
        width = 1
        n = 3

    class Page:
        def get_pixmap(self, matrix, alpha):
            assert matrix == "2x"
            assert alpha is False
            return Pixmap()

    class PyMuPDF:
        @staticmethod
        def Matrix(x, y):
            return f"{x}x" if x == y else f"{x}x{y}"

    monkeypatch.setattr(rapidocr_onnxruntime, "RapidOCR", FakeRapidOCR)
    monkeypatch.setattr(DocumentProcessor, "_rapid_ocr_engine", None)

    text = DocumentProcessor._rapid_ocr_page(Page(), PyMuPDF)

    assert text == "first row\nsecond row"
