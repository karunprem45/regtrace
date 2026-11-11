"""Download a 510(k) summary PDF and return its text page by page."""
import io
import requests


def summary_url(k_number: str) -> str:
    """FDA hosts most summaries at cdrh_docs/pdfYY/Kxxxxxx.pdf (YY without a leading zero).
    Check this against a few real K-numbers; older submissions use other paths."""
    yy = int(k_number[1:3])
    return f"https://www.accessdata.fda.gov/cdrh_docs/pdf{yy}/{k_number}.pdf"


def fetch_pages(k_number: str, session=None) -> list[str] | None:
    from pypdf import PdfReader

    s = session or requests.Session()
    r = s.get(summary_url(k_number), timeout=60)
    if r.status_code != 200:
        return None
    reader = PdfReader(io.BytesIO(r.content))
    return [(p.extract_text() or "") for p in reader.pages]
