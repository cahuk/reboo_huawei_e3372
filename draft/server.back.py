import re
import json
import requests
import os
import time
import socket

secret_key = "s1lent"
server_port = 8080
mode = "ipv4" #ipv4 or ipv6

from http.server import BaseHTTPRequestHandler, HTTPServer

class HTTPServerV6(HTTPServer):
	if mode == "ipv6":
		address_family = socket.AF_INET6


class S(BaseHTTPRequestHandler):
	def _set_response(self):
		self.send_response(200)
		self.send_header('Content-type', 'text/html')
		self.end_headers()

	def do_GET(self):
		self._set_response()
		request_path = str(self.path)

		m = re.search(r'\/([^\/]+)\/([^\/]+)\/?', request_path)
		if m:
			find_secret = m.group(1)
			find_modem_ip = m.group(2)

			if find_secret != secret_key:
				self.wfile.write("Wrong secret key".encode('utf-8'))
				return

			if self.reboot_modem(find_modem_ip):
				self.wfile.write(("Modem " + find_modem_ip + " has been rebooted").encode('utf-8'))
			else:
				self.wfile.write("Modem reboot error".encode('utf-8'))
		else:
			self.wfile.write("Wrong request".encode('utf-8'))
	def send_request_to_modem(self, modem_ip, val):
		try:
			headers = {
				'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0",
				'Accept': "*/*",
				'Accept-Language': "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
				'Connection': "keep-alive",
				'X-Requested-With': "XMLHttpRequest",
			}

			session = requests.Session()
			#compose_url = 'http://' + modem_ip + '/api/webserver/token'
			compose_url = 'http://' + modem_ip + '/api/webserver/SesTokInfo'
			response = session.get(compose_url,
									headers=headers,
									allow_redirects=False,
									timeout=10)

			response_code = response.status_code
			html = response.text

			#m = re.search('<token>([^<]+)<', html)
			m = re.search('<SesInfo>([^<]+)<', html)
			token = m.group(1)

			xml_data = '<?xml version: "1.0" encoding="UTF-8"?><request><dataswitch>' + str(val) + '</dataswitch></request>'

			headers = {
				'__RequestVerificationToken': token,
				'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:53.0) Gecko/20100101 Firefox/53.0",
				'Accept': "*/*",
				'Accept-Language': "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
				'Connection': "keep-alive",
				'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
				'X-Requested-With': "XMLHttpRequest",
			}



			session = requests.Session()
			compose_url = 'http://' + modem_ip + '/api/dialup/mobile-dataswitch'
			response = session.post(compose_url,
									headers=headers,
									data=xml_data,
									allow_redirects=False,
								   timeout=10)

			response_code = response.status_code
			html = response.text
			m = re.search('<response>([^<]+)<', html)
			res = m.group(1)
			if res == 'OK':
				return True

			return False

		except:
			return False

	def reboot_modem(self, modem_ip):
		result_off = self.send_request_to_modem(modem_ip, 0)
		# time.sleep(0.1)
		result_on = self.send_request_to_modem(modem_ip, 1)

		if result_off and result_on:
			return True
		else:
			return False


def run(server_class=HTTPServerV6, handler_class=S, port=server_port):
	server = ""
	if mode == "ipv6":
		server = "::"
	server_address = (server, port)
	httpd = server_class(server_address, handler_class)
	print('Starting httpd...\n')
	try:
		httpd.serve_forever()
	except KeyboardInterrupt:
		pass
	httpd.server_close()
	print('Stopping httpd...\n')

run()


#c:\Python38\python c:\modem\server.py