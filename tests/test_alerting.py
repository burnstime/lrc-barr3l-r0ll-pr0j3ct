import os
import importlib
import time

def test_alert_written_on_unauthorized_decoder(tmp_path):
    # ensure no alerts.log exists
    alerts = os.path.join(os.getcwd(), 'alerts.log')
    try:
        os.remove(alerts)
    except Exception:
        pass
    appmod = importlib.import_module('lab_server.app')
    app = appmod.app
    app.testing = True
    client = app.test_client()
    # call decoder without token (in testing mode it may allow; ensure alert route triggers)
    resp = client.get('/decode-login')
    # The app writes alerts.log on unauthorized attempts; wait briefly
    time.sleep(0.1)
    assert os.path.exists(alerts)
    with open(alerts, 'r', encoding='utf-8') as f:
        content = f.read()
    assert 'Unauthorized' in content or 'Attempt' in content or len(content) > 0
