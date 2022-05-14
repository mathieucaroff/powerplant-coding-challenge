from http.server import HTTPServer, SimpleHTTPRequestHandler
import contextlib
import json

from solver import solve

code_ok = 200
code_bad_request = 400
code_service_unavailable = 503

class HTTPRequestHandler(SimpleHTTPRequestHandler):
    def reply(self, code: int, content_type: str = "", content: str = ""):
        self.send_response(code)
        if content_type != "":
            self.send_header('Content-Type', content_type)
        encoded = content.encode('utf-8')
        self.send_header('Content-Length', len(encoded))
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self):
        if self.path != "/productionplan":
            self.reply(code_bad_request)
            return

        content_length = int(self.headers['Content-Length'])
        post_body = self.rfile.read(content_length).decode("utf-8")
        problem = json.loads(post_body)
        try:
            solution = solve(problem)
            self.reply(code_ok, 'application/json', json.dumps(solution))
        except Exception as exception:
            print("exception", exception)
            self.reply(code_service_unavailable)
            raise

if __name__ == "__main__":
    host = ""
    port = 8888
    server_address = (host, port)
    http_server = HTTPServer(server_address, HTTPRequestHandler)
    print(f"Starting http server on port {port}")
    with contextlib.suppress(KeyboardInterrupt):
        http_server.serve_forever()
    print()
    print("Stoping http server")
