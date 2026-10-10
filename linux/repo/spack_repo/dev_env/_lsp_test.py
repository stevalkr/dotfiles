"""Exercise a language server's stdio initialization and clean shutdown."""

import json
import os
import select
import subprocess
import sys
import tempfile
import time


def test_language_server(executable):
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(
            [str(executable), "--stdio"], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=errors,
        )
        pending = bytearray()

        def send(message):
            body = json.dumps(dict(jsonrpc="2.0", **message)).encode()
            process.stdin.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
            process.stdin.flush()

        def response(request_id):
            deadline = time.monotonic() + 30

            def receive():
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not select.select([process.stdout], [], [], remaining)[0]:
                    raise RuntimeError("Language server response timed out")
                data = os.read(process.stdout.fileno(), 65536)
                if not data:
                    errors.seek(0)
                    raise RuntimeError("Language server closed stdout: " + errors.read().decode())
                pending.extend(data)

            while True:
                while b"\r\n\r\n" not in pending:
                    receive()
                header, body = pending.split(b"\r\n\r\n", 1)
                length = next(int(line.split(b":", 1)[1]) for line in header.split(b"\r\n")
                              if line.lower().startswith(b"content-length:"))
                while len(body) < length:
                    receive()
                    body = pending.split(b"\r\n\r\n", 1)[1]
                message = json.loads(body[:length])
                pending[:] = body[length:]
                if message.get("id") == request_id:
                    assert "error" not in message, message
                    return message["result"]

        try:
            send({"id": 1, "method": "initialize", "params": {
                "processId": None, "rootUri": None, "capabilities": {},
            }})
            assert "capabilities" in response(1)
            send({"method": "initialized", "params": {}})
            send({"id": 2, "method": "shutdown", "params": None})
            response(2)
            send({"method": "exit", "params": None})
            assert process.wait(timeout=10) == 0
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            process.stdin.close()
            process.stdout.close()
    print("Language server initialize/shutdown: PASS")


if __name__ == "__main__":
    test_language_server(sys.argv[1])
