import logging

logger = logging.getLogger(__name__)


def send_verification_code_email(email: str, code: str) -> None:
    logger.info("Dev verification code for %s: %s", email, code)
