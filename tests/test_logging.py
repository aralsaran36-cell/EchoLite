import logging

from app.config import Settings
from app.core.logging import get_logger


def test_logger_is_created():
    settings = Settings()
    logger = get_logger("echolite.test", settings)

    assert isinstance(logger, logging.Logger)
    assert logger.name == "echolite.test"


def test_logger_has_handler():
    settings = Settings()
    logger = get_logger("echolite.test.handler", settings)

    assert len(logger.handlers) > 0


def test_logger_level_is_info():
    settings = Settings()
    logger = get_logger("echolite.test.level", settings)

    assert logger.level == logging.INFO


def test_logger_reuse_same_instance():
    settings = Settings()

    logger1 = get_logger("echolite.test.reuse", settings)
    logger2 = get_logger("echolite.test.reuse", settings)

    assert logger1 is logger2