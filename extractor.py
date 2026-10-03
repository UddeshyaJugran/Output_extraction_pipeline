import json
import logging
import time

from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from schemas import Invoice

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)
logging.getLogger("google_genai").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)

client = genai.Client()  # GEMINI_API_KEY environment variable se key leta hai
MODEL = "gemini-3.5-flash"

SYSTEM_PROMPT = (
    "You extract invoice data from messy text. "
    "Return ONLY one JSON object matching this JSON schema:\n"
    f"{json.dumps(Invoice.model_json_schema())}\n"
    "Rules: dates must be ISO format YYYY-MM-DD; currency must be an ISO 4217 "
    "code (Rs / rupees -> INR); amounts must be plain numbers without commas. "
    "Slash dates like 12/08/2026 are DD/MM/YYYY (day first). "
    "Never invent or guess values. If the text contains no invoice, "
    'return exactly {"error": "no invoice data"}.'
)


def _clean(raw: str) -> str:
    """Kabhi kabhi model ```json fences laga deta hai, unhe hata do."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw
        raw = raw.rsplit("```", 1)[0]
    return raw.strip()


def _call_model(prompt: str, tries: int = 5) -> str:
    """Server busy (503/429/500) ho to ruk ke dobara try karo."""
    for i in range(tries):
        try:
            resp = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0,
                ),
            )
            return resp.text or ""
        except errors.APIError as e:
            if e.code in (429, 500, 503) and i < tries - 1:
                wait = 2 ** (i + 1)  # 2, 4, 8, 16 seconds
                log.warning("API busy (%s), %ds baad retry...", e.code, wait)
                time.sleep(wait)
            else:
                raise
    return ""


def extract(text: str, max_retries: int = 3) -> Invoice:
    prompt = f"Extract the invoice data from this text:\n\n{text}"

    for attempt in range(1, max_retries + 1):
        raw = _clean(_call_model(prompt))

        try:
            invoice = Invoice.model_validate_json(raw)
            log.info("Extracted successfully on attempt %d", attempt)
            return invoice
        except ValidationError as e:
            log.warning("Attempt %d failed validation: %s", attempt, e.error_count())
            # Error wapas model ko bhejo taaki wo khud fix kare
            prompt = (
                f"Extract the invoice data from this text:\n\n{text}\n\n"
                f"Your previous answer was:\n{raw}\n\n"
                f"It failed validation with this error:\n{e}\n"
                "Return the corrected JSON only."
            )

    raise ValueError(f"Extraction failed after {max_retries} attempts")