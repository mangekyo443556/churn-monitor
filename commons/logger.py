"""Logger compartido. En Lambda, todo lo que se loguea aparece en CloudWatch Logs."""
import logging

logger = logging.getLogger("churn_monitor")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    logger.addHandler(_handler)
logger.setLevel(logging.INFO)
logger.propagate = False
