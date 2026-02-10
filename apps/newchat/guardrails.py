from presidio_analyzer import AnalyzerEngine

analyzer = AnalyzerEngine()

# Only detect serious personal info
ALLOWED_ENTITIES = [
    "PHONE_NUMBER",
    "EMAIL_ADDRESS",
    "CREDIT_CARD",
    "IBAN_CODE",
    "US_SSN"
]

TOXIC_WORDS = [
    "kill", "bomb", "hack", "suicide", "murder",
    "kidnap", "rape", "terrorist"
]

def check_guardrails(text):
    if not text.strip():
        return True

    # Only check selected PII types
    results = analyzer.analyze(
        text=text,
        language="en",
        entities=ALLOWED_ENTITIES
    )

    pii_found = len(results) > 0
    toxic_found = any(word in text.lower() for word in TOXIC_WORDS)

    return not (pii_found or toxic_found)
