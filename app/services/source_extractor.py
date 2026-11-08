from io import BytesIO
from urllib.parse import urlparse
import ipaddress
import socket
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

MAX_TEXT_CHARS = 18000
HEADERS = {"User-Agent": "ApplySprint/1.0 (+application requirement research)"}

def _is_public_host(host: str) -> bool:
    try:
        for info in socket.getaddrinfo(host, None):
            ip = ipaddress.ip_address(info[4][0])
            if not ip.is_global:
                return False
        return True
    except Exception:
        return False

def extract_url(url: str | None) -> tuple[str, str | None]:
    if not url:
        return "", None
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or not _is_public_host(parsed.hostname):
        return "", f"Skipped unsafe or invalid URL: {url}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=18, allow_redirects=True)
        response.raise_for_status()
        final = urlparse(response.url)
        if not final.hostname or not _is_public_host(final.hostname):
            return "", f"Redirected to a non-public host: {url}"
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type and "text/plain" not in content_type:
            return "", f"URL did not return readable HTML/text: {url}"
        soup = BeautifulSoup(response.text, "html.parser")
        for node in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
            node.decompose()
        text = " ".join(soup.stripped_strings)
        return text[:MAX_TEXT_CHARS], None
    except Exception as exc:
        return "", f"Could not retrieve {url}: {str(exc)[:180]}"

def extract_pdf(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    chunks = []
    for page in reader.pages[:35]:
        chunks.append(page.extract_text() or "")
    return "\n".join(chunks)[:MAX_TEXT_CHARS]
