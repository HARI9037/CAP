import logging


def configure_logging(level: str) -> None:
    normalized_level = level.upper()
    log_level = getattr(logging, normalized_level, logging.INFO)
    if logging.getLogger().handlers:
        logging.getLogger().setLevel(log_level)
        return
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
