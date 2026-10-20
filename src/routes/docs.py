from src.utils.http import handler, response
from src.utils.openapi import build_spec

SCALAR_VERSION = "1.72.4"

_HTML = f"""<!doctype html>
<html>
  <head>
    <title>Cuy Farm API</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
  </head>
  <body>
    <div id="app"></div>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference@{SCALAR_VERSION}"></script>
    <script>
      Scalar.createApiReference("#app", {{ url: "/openapi.json" }});
    </script>
  </body>
</html>
"""


@handler
def openapi(event, context):
    return response(200, build_spec())


@handler
def ui(event, context):
    return {"statusCode": 200, "headers": {"Content-Type": "text/html; charset=utf-8"}, "body": _HTML}
