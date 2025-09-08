import os
import requests
import logging

logger = logging.getLogger(__name__)


def send_webhook_alert(msg: str):
    url = os.environ.get('ALERT_WEBHOOK')
    if not url:
        return False
    try:
        r = requests.post(url, json={'message': msg}, timeout=2)
        return r.status_code == 200
    except Exception as e:
        logger.debug(f'Failed to send webhook alert: {e}')
        return False
