import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote

import pytest
from telegram.error import BadRequest

from rpi.launcher import InvalidLauncher, IftttLauncher, TelegramLauncher, NotifyRunLauncher


# noinspection PyPep8Naming
class MyServer(BaseHTTPRequestHandler):
    def parse_post_data(self):
        data_string = self.rfile.read(int(self.headers['Content-Length'])).decode()

        post = {}
        try:
            for pair in data_string.split('&'):
                if '=' not in pair:
                    continue
                key, value = pair.split('=')
                post[key] = unquote(value)
        except ValueError:
            pass

        return post

    def log_message(self, _format, *args):
        pass

    def log_error(self, _format, *args):
        pass

    def log_date_time_string(self):
        pass

    def log_request(self, code='-', size='-'):
        pass

    def do_POST(self):
        data = self.parse_post_data()
        code = 400

        for key, value in data.items():
            if value not in ('test_title', 'test_message'):
                code = 200
                break

        self.send_response(code)
        self.send_header('Content-type', 'text/plain')
        self.wfile.write('Done'.encode())
        self.end_headers()


def get_server():
    return HTTPServer(('0.0.0.0', 54321), MyServer)


class Memory:
    server: HTTPServer = None
    thread = None
    address = 'http://localhost:54321'

    @staticmethod
    def run_server():
        try:
            Memory.server.serve_forever()
        except OSError:
            pass


class TestLaunchers:
    @classmethod
    def setup_class(cls):
        Memory.server = get_server()
        Memory.thread = threading.Thread(target=Memory.run_server, daemon=True)
        Memory.thread.start()

    @classmethod
    def teardown_class(cls):
        Memory.server.server_close()

    def test_invalid_launcher(self):
        with pytest.raises(NotImplementedError):
            invalid_launcher = InvalidLauncher()
            invalid_launcher.fire('test_title', 'test_message')

    def test_ifttt_launcher(self):
        ifttt_launcher = IftttLauncher(Memory.address)
        ifttt_launcher.fire('test_title', 'test_message')

    def test_telegram_launcher(self):
        with pytest.raises(BadRequest, match='Chat not found'):
            telegram_launcher = TelegramLauncher(0)
            telegram_launcher.fire('test_title', 'test_message')

    def test_notify_run_launcher(self):
        notify_run_launcher = NotifyRunLauncher(Memory.address)
        notify_run_launcher.fire('test_title', 'test_message')


if __name__ == '__main__':
    pytest.main([os.path.basename(__file__), '-v'])
