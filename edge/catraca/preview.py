"""Preview HTTP: último frame da câmera + última decisão, para demonstração.

Servidor leve (stdlib) na porta CATRACA_PREVIEW_PORT (0 desliga). Abrir
http://<ip-do-pi>:8088 em qualquer navegador da rede — a página se atualiza
sozinha. A câmera é exclusiva do serviço, então este é o jeito de "ver" o que
ela vê sem parar a catraca.
"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_PAGE = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Catraca ANPR — preview</title>
<style>
body{background:#111;color:#eee;font-family:system-ui,sans-serif;margin:0;text-align:center}
#st{font-size:1.3rem;padding:.6rem;background:#1c1c1c}
img{max-width:100%}
</style></head>
<body>
<div id="st">conectando…</div>
<img id="cam" src="/frame.jpg" alt="câmera">
<script>
setInterval(() => { document.getElementById("cam").src = "/frame.jpg?" + Date.now(); }, 500);
setInterval(async () => {
  try {
    const s = await (await fetch("/status")).json();
    document.getElementById("st").textContent = s.text;
  } catch (e) {}
}, 1000);
</script>
</body></html>
"""


class Preview:
    """Estado compartilhado entre o loop principal e o servidor HTTP."""

    def __init__(self, clock=time.time):
        self._lock = threading.Lock()
        self._clock = clock
        self._jpeg = b""
        self._status = "aguardando primeira leitura"
        self._ts = 0.0

    def update_frame(self, jpeg: bytes) -> None:
        with self._lock:
            self._jpeg = jpeg

    def set_status(self, text: str) -> None:
        with self._lock:
            self._status = text
            self._ts = self._clock()

    def frame(self) -> bytes:
        with self._lock:
            return self._jpeg

    def status(self) -> dict:
        with self._lock:
            return {"text": self._status, "ts": self._ts}


def start_server(preview: Preview, port: int) -> ThreadingHTTPServer:
    """Sobe o servidor em thread daemon e o retorna (porta 0 = efêmera)."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                self._send(200, "text/html; charset=utf-8", _PAGE.encode())
            elif self.path.startswith("/frame.jpg"):
                jpeg = preview.frame()
                if jpeg:
                    self._send(200, "image/jpeg", jpeg)
                else:
                    self._send(503, "text/plain", b"sem frame ainda")
            elif self.path == "/status":
                body = json.dumps(preview.status()).encode()
                self._send(200, "application/json", body)
            else:
                self._send(404, "text/plain", b"nao existe")

        def _send(self, code: int, ctype: str, body: bytes) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):  # não poluir o journal a cada frame
            pass

    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
