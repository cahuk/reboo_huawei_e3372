import re
import json
import requests
import os
import time
import socket

SECRET_KEY = "s1lent"
SERVER_PORT = 8080
MODE = "ipv4"  # ipv4 or ipv6

from http.server import BaseHTTPRequestHandler, HTTPServer


class HTTPServerV6(HTTPServer):
    if MODE == "ipv6":
        address_family = socket.AF_INET6


class ServerKernel(BaseHTTPRequestHandler):
    response_text = ""

    def _set_response(self):
        self.response_text = ""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_response()
        request_path = str(self.path)

        m = re.search(r'/([^/]+)/([^/]+)/?', request_path)
        if m:
            find_secret = m.group(1)
            find_modem_ip = m.group(2)

            if find_secret != SECRET_KEY:
                self.wfile.write("Wrong secret key".encode('utf-8'))
                return

            if self.reboot_modem(find_modem_ip):
                self.wfile.write(
                    ("The modem " + find_modem_ip + " is rebooting, it may take a few minutes.").encode('utf-8'))
            else:
                self.wfile.write(("Modem reboot error.\n" + self.response_text).encode('utf-8'))
        else:
            self.wfile.write("Wrong request".encode('utf-8'))

    @staticmethod
    def get_default_user_agent():
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            'Accept': "*/*",
            'Accept-Language': "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            'Connection': "keep-alive",
            'X-Requested-With': "XMLHttpRequest",
        }
        return headers

    def get_auth_user_agent(self, session, modem_ip):
        session_id, token = self.get_sessId_token(session, modem_ip)
        #token = self.get_token(session, modem_ip)
        # чомусь при одноразовому запиті на токен запит
        # на ребут віддає 125003 - не авторизований
        headers = {
            "__RequestVerificationToken": token,
            "Cookie": f"{session_id}",
            **self.get_default_user_agent(),
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        }
        return headers

    def get_sessId_token(self, session, modem_ip):
        headers = self.get_default_user_agent()
        compose_url = f'http://{modem_ip}/api/webserver/SesTokInfo'
        response = session.get(compose_url, headers=headers, allow_redirects=False, timeout=10)
        response_code = response.status_code
        self.response_text = html = response.text

        tok = re.search('<TokInfo>([^<]+)<', html)
        token = tok.group(1)
        sess_id = re.search('<SesInfo>([^<]+)<', html)
        session_id = sess_id.group(1)
        #session.cookies.set('__RequestVerificationToken', token, domain=modem_ip)
        return session_id, token

    def do_reboot(self, session, modem_ip):
        headers = self.get_auth_user_agent(session, modem_ip)
        compose_url = f'http://{modem_ip}/api/device/control'
        # compose_url = f'http://{modem_ip}/api/dialup/mobile-dataswitch'
        xml_data = '<?xml version="1.0" encoding="UTF-8"?><request><Control>1</Control></request>'
        # xml_data = '<?xml version: "1.0" encoding="UTF-8"?><request><dataswitch>0</dataswitch></request>'
        response = session.post(compose_url, headers=headers, data=xml_data, allow_redirects=False, timeout=10)

        headers = self.get_auth_user_agent(session, modem_ip)
        # xml_data = '<?xml version: "1.0" encoding="UTF-8"?><request><dataswitch>1</dataswitch></request>'
        # response = session.post(compose_url, headers=headers, data=xml_data, allow_redirects=False, timeout=5)

        response_code = response.status_code
        self.response_text = html = response.text
        m = re.search('<response>([^<]+)<', html)
        res = m.group(1)
        return res

    def send_request_to_modem(self, session, modem_ip):
        try:
            res = self.do_reboot(session, modem_ip)
            return res == 'OK'
        except Exception as e:
            print(f"Сталася помилка: {e}")

    def reboot_modem(self, modem_ip):
        reload_result = self.send_request_to_modem(requests.Session(), modem_ip)
        return reload_result


def run(server_class=HTTPServerV6, handler_class=ServerKernel, port=SERVER_PORT):
    server = ""
    if MODE == "ipv6":
        server = "::"
    server_address = (server, port)
    httpd = server_class(server_address, handler_class)
    print('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt as e:
        print("KeyboardInterrupt occurred:", e)
    httpd.server_close()
    print('Stopping httpd...\n')


run()

# c:\Python38\python c:\modem\server.py
