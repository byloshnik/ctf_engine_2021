# -*- coding: utf-8 -*-
from vk_api import *
import time
from vk_api.utils import get_random_id
import traceback
import json
import threading
import random
import os
import requests
import urllib
from multiprocessing.dummy import Pool as ThreadPool
import re
from configs.texts import MsgTexts

class Mailing(object):
	'''Рассылка VK API'''

	def __init__(self, tokens, upload_token, album_id, group_id, pack_length=4, pools=4):
		super(Mailing, self).__init__()
		self.pack_length = pack_length
		self.tokens = tokens
		self.upload = VkApi(token=upload_token).get_api()
		self.album_id = album_id
		self.group_id = group_id
		self.tokens_amount = tokens.__len__()
		self.pool = ThreadPool(pools)

	@staticmethod
	def get_biggest_size(data):
		biggest_size = max(data, key=lambda x: x['width'] * x['height'])
		return biggest_size

	@staticmethod
	def save_photo(name, url):
		listdir = os.listdir('temp/')
		f_name = f'{name}.jpg'
		if f_name in listdir:
			os.remove('temp/' + f_name)
		# p = requests.get(url)
		p = urllib.request.urlopen(str(url).replace('\\', ''))
		f_name = 'temp/' + f_name
		out = open(f_name, "wb")
		out.write(p.read())
		out.close()
		return f_name

	@staticmethod
	def save_document(name, url):
		listdir = os.listdir('temp/')
		if name in listdir:
			os.remove('temp/' + name)
		p = urllib.request.urlopen(str(url).replace('\\', ''))
		name = 'temp/' + name
		out = open(name, "wb")
		out.write(p.read())
		out.close()
		return name

	def upload_photo(self, f_name):
		if f_name != '':
			a = self.upload.photos.getUploadServer(album_id=self.album_id, group_id=self.group_id)
			b = requests.post(a['upload_url'], files={'photo': open(f_name, 'rb')}).json()
			c = self.upload.photos.save(album_id=self.album_id, group_id=self.group_id, server=b["server"],
										photos_list=b["photos_list"], hash=b["hash"])
			d = 'photo{}_{}'.format(c[0]['owner_id'], c[0]['id'])
			return d
		else:
			return ''

	def upload_document(self, f_name):
		if f_name != '':
			a = self.upload.docs.getUploadServer(group_id=self.group_id)
			b = requests.post(a['upload_url'], files={'file': open(f_name, 'rb')}).json()
			c = self.upload.docs.save(file=b['file'], title=f_name.replace('temp/', ''))
			d = 'doc{}_{}'.format(c['doc']['owner_id'], c['doc']['id'])
			return d
		else:
			return ''

	@staticmethod
	def send_execute(execute):
		return VkApi(token=execute['token']).get_api().execute(code=execute['code'])

	def generate_data(self, obj):
		text = self.get_text(obj)
		attachments = self.get_attachments(obj)
		data = ''
		if text != '':
			data = text
		if data != '' and attachments != '':
			data += ', '
		if attachments != '':
			data += attachments
		return data

	@staticmethod
	def get_text(obj):
		# Если разкоментировать то будет добавляться инструкция по отписке к сообщению рассылки 
		# in_text = obj['text'] + MsgTexts.to_unsub
		in_text = obj['text']
		text = in_text.replace('/mailing', '')
		if text != '':
			return '"message":"%s"' % text.replace('\n', '\\n') 
		else:
			return ''

	def get_attachments(self, obj):
		if 'attachments' in obj.keys():
			atts = []
			for attachment in obj['attachments']:

				if attachment['type'] == 'photo':
					download_url = self.get_biggest_size(attachment['photo']['sizes'])['url']
					file_name = self.save_photo(str(time.time()) + '_' + str(random.randint(0, 100)), download_url)
					atts.append(self.upload_photo(file_name))
					os.remove(file_name)

				elif attachment['type'] == 'wall':
					if not attachment['wall']['from']['is_closed']:
						atts.append('wall%s_%s' % (attachment['wall']['from_id'], attachment['wall']['id']))
					else:
						...

				elif attachment['type'] == 'audio_message':
					...

				elif attachment['type'] == 'doc':
					if attachment['doc']['ext'] not in ['exe', 'bat', 'py', 'php',
														'sh', 'chazhevski', 'cmd',
														'geo', 'exp', 'exm', 'pim',
														'xip', 'app', 'acc', 'com',
														'68k', '286', '186', 'vbs']:
						file_name = self.save_document(attachment['doc']['title'], attachment['doc']['url'])
						atts.append(self.upload_document(file_name))
						os.remove(file_name)

			return '"attachment":"' + ','.join(atts) + '"'

	def send(self, sending_list, data_json):

		packs, codes, results, packs_time = [], [], [], []
		count, token_number = 0, 0
		token_quantity = self.tokens_amount - 1
		result_dict = {'total': len(sending_list), 'good': 0, 'bad': 0, 'no_permission': 0, 'time': 0}
		start_time = time.time()

		while len(sending_list) >= self.pack_length:
			packs.append(','.join([str(i) for i in sending_list[:self.pack_length]]))
			sending_list = sending_list[self.pack_length + 1:]
		packs.append(','.join([str(i) for i in sending_list]))

		gen_code = 'var answ = [];\n'

		for pack in packs:
			gen_code += 'answ = answ + API.messages.send({peer_ids:"%s", %s, random_id:%s}); \n' % (
			pack, data_json, get_random_id())
			count += 1
			if count == 25:
				gen_code += 'return answ;'
				codes.append(gen_code)
				gen_code = 'var answ = [];\n'
				count = 0

		if not codes or gen_code != 'var answ = [];\n':
			gen_code += 'return answ;'
			codes.append(gen_code)

		executes = [{
			'token': self.tokens[token_number + 1 if token_number < token_quantity else 0],
			'code': code
		} for code in codes]

		results = self.pool.map(self.send_execute, executes)
		# print(results)
		for row in results:
			for cell in row:
				try:
					if 'message_id' in cell.keys():
						result_dict['good'] += 1
					elif 'error' in cell.keys():
						if cell['error']['code'] == 901:
							result_dict['no_permission'] += 1
						else:
							result_dict['bad'] += 1
				except AttributeError:
					...

		result_dict['time'] = round(time.time() - start_time, 2)

		return result_dict
