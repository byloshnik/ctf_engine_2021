# -*- coding: utf-8 -*-
import socketserver
import time
import threading
from datetime import datetime
from vk_api import *
import sys
import time
from termcolor import colored
import colorama
import json
import queue
from threading import Thread
from vk_api.utils import get_random_id
from modules.db import User
from modules.nc import NetCat
from modules.mailing import Mailing
from modules.keyboard import BotKeyboard
from app import app
from configs.texts import MsgTexts

colorama.init()

# {"type": "send_msg", "peer_id": "", "message": "", "attachment": "",
# "forward_messages": "", "sticker_id": "", "keyboard": "", "secret": ""}


fields_send_msg = ['peer_id', 'message', 'attachment', 'forward_messages',
				   'sticker_id', 'keyboard', 'peer_ids', 'user_id', 'user_ids', 'disable_mentions']

secret = app.config['SOCKET_MSG']['msg_module_secret']

vk_session_msg = VkApi(token=app.config['VK_TOKEN'])
vk_msg = vk_session_msg.get_api()

q = queue.Queue()

mailing = Mailing(app.config['MAILING_TOKENS'], app.config['USER_TOKEN'],
					app.config['MAILING']['album_id'], app.config['GROUP_ID'])

def print_log(string):
	print((f'[{colored("#", "green")}]{datetime.now().strftime("%d.%m.%Y %H:%M:%S")} - {str(string).encode("utf8")}'))


def send_msg(**kwargs):
	kwargs = {key: value for key, value in kwargs.items() if value is not None and key != 'type' and key != 'secret'}
	q.put(kwargs)


def pack_sender(q):
	while True:
		if q.qsize() != 0:
			a_lenght = min(q.qsize(), 25)
			gen_code = 'return {'
			for i in range(a_lenght):
				try:
					gen_code += f'"send{i}":API.messages.send(' + json.dumps(q.get_nowait(),
																			 ensure_ascii=False) + '),\n'
				except:
					pass

			gen_code += '};'
			response = vk_msg.execute(code=gen_code)

			print_log(response)
		time.sleep(0.1)

def start_mailing(mailing_data, admin_id, mailing_type):

	if mailing_type == 'global_mailing':
		users_list = [user.user_id for user in User.select().where(User.activity == 1, User.participants_count > 0)]
	elif mailing_type == 'test_mailing':
		users_list = app.config['VK_ADMINS']

	mailing_responce = mailing.send(users_list, mailing_data)

	user_query = User.select().where(User.user_id == admin_id).get()
	vk_msg.messages.send(
			peer_id=admin_id,
			message=MsgTexts.mailing_done % (
				mailing_responce['total'],
				mailing_responce['good'],
				mailing_responce['no_permission'],
				mailing_responce['bad'],
				mailing_responce['time']
			),
			keyboard=BotKeyboard.main(user_query, admin_id),
			random_id=get_random_id()
		)


class Service(socketserver.BaseRequestHandler):
	def handle(self):
		print_log('Someone connected')
		while True:
			try:
				entered = self.receive()
				try:
					json_entered = json.loads(entered)
				except json.decoder.JSONDecodeError:
					json_entered = {}
				# print_log(json_entered)
				if json_entered:
					if 'secret' in json_entered:
						if json_entered['secret'] == secret:
							if json_entered and 'type' in json_entered:
								if json_entered['type'] == 'send_msg':
									test = 'error'
									for field_msg in fields_send_msg:
										if field_msg not in json_entered:
											self.send('{"response": "Missing field: %s"}' % field_msg)
											test = 'error'
											break
										else:
											test = 'ok'
									if test == 'error':
										continue
									else:
										send_msg(**{k: v for k, v in json_entered.items() if v is not None},
												 random_id=get_random_id())
										self.send('{"response": "ok"}')

								elif json_entered['type'] == 'start_mailing':
									my_thread = threading.Thread(
											target=start_mailing, 
											args=(
												json_entered['mailing_data'], 
												json_entered['admin_id'],
												json_entered['mailing_type'],
											)
										)

									my_thread.start()
									# print(json_entered)
									self.send('{"response": "ok"}')

								# elif json_entered['type'] == 'dump_to_excel':
								# 	my_thread = threading.Thread(
								# 			target=dump, 
								# 			args=(
								# 				json_entered['user_id'], 
								# 			)
								# 		)

								# 	my_thread.start()

								# 	# print(json_entered)
								# 	self.send('{"response": "ok"}')

								else:
									self.send('{"response": "Error type"}')
							else:
								self.send('{"response": "Missing field: type"}')
						else:
							self.send('{"response": "Error type"}')
			except ConnectionResetError:
				print_log('Someone disconnected')
				break

	def receive(self, prompt=""):
		self.send(prompt, newline=False)
		return self.request.recv(4096).strip()

	def send(self, string, newline=True):
		if newline:
			string = string + "\n"
		self.request.sendall(string.encode())


class ThreadedService(socketserver.ThreadingMixIn,
					  socketserver.TCPServer,
					  socketserver.DatagramRequestHandler):
	pass


def main():
	port = app.config['SOCKET_MSG']['port']
	host = app.config['SOCKET_MSG']['host']

	service = Service

	server = ThreadedService((host, port), service)
	server.allow_reuse_address = True

	server_thread = threading.Thread(target=server.serve_forever)
	server_thread.daemon = True
	server_thread.start()

	print(f'Server started on:\n'
		  f'Host: {host}\n'
		  f'Port: {port}\n')

	while True:
		time.sleep(1)


thread_sender = Thread(target=pack_sender, args=(q,), daemon=True)
if __name__ == '__main__':
	thread_sender.start()
	main()
