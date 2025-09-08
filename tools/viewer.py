from flask import Flask, render_template_string, request
import csv
import os
import html

from tools.visual_diff import row_to_html

APP = Flask(__name__)

TEMPLATE = '''
<!doctype html>
<title>Spoof Corpus Viewer</title>
<style>table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:8px}code{white-space:pre-wrap}</style>
<h1>Spoof Corpus Viewer</h1>
<form method="post" enctype="multipart/form-data">
  <label>Upload CSV (original,spoofed): <input type="file" name="file"></label>
  <input type="submit" value="Upload">
</form>
{% if rows %}
<table>
<tr><th>Original</th><th>Spoofed</th></tr>
{{ rows|safe }}
</table>
{% endif %}
'''


@APP.route('/', methods=['GET', 'POST'])
def index():
    rows_html = ''
    if request.method == 'POST' and 'file' in request.files:
        f = request.files['file']
        text = f.read().decode('utf8', errors='ignore')
        # parse simple CSV
        for line in text.splitlines()[1:]:
            parts = list(csv.reader([line]))[0]
            if not parts:
                continue
            orig = parts[0] if len(parts) > 0 else ''
            spoof = parts[1] if len(parts) > 1 else ''
            rows_html += row_to_html(orig, spoof)
    return render_template_string(TEMPLATE, rows=rows_html)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    APP.run(host='127.0.0.1', port=port)
