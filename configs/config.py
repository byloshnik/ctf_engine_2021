# -*- coding: utf-8 -*-
import re

class Config:
	DEBUG = True
	CHECK_IS_CTF_STARTED_IN_TASKS_PAGE = True


	SOCKET_MSG = {
		'msg_module_secret': '',
		'host': '127.0.0.1',
		'port': 2000
	}

	VK_CONFIRMATION = ''
	VK_SECRET = ''
	VK_TOKEN = ''
	MAILING_TOKENS = ['']
	USER_TOKEN = ''
	GROUP_ID = 0
	VK_ADMINS = [0]

	MAILING = {
		'album_id': 0
	}

	MYSQL = {
		'db_name': 'ctf',
		'user_name': 'root',
		'password': 'QWErty1234',
		'host': '127.0.0.1',
		'port': 3306
	}

	HELP_URL = ''
	RULES_URL = ''

	SUB_PLS_URL = ''

	CIRY_JSON_LIST = {
		1: 'рязань'
	} 

	AREA_DESCRIPTIONS = {
		1: 'Рязанская обл.'
	}

	FIO_LEN = {
		'min': 4,
		'max': 30
	}

	TEAMNAME_LEN = {
		'min': 1,
		'max': 50
	}

	RE_NUMBER = re.compile(r"^\s*(\+?7|8)\(?\d{3}\)?\d{3}-?\d{2}-?\d{2}$")
	RE_FLAG = re.compile(r"^<flag_(ctf|rznctf):(.{1,100})>$")

	TASKS_DATA = []
	TASKS_DATA_FROM_NAME = []

	FOOTER_LINKS = {
		'kvant': '',
		'rrtu': '',
		'toup': '',
		'rostelecom': ''
	}
	 
	TASKS_FLAGS = {
		'<flag_ctf:(flag1)>': 'tryit',
		'<flag_ctf:(flag2)>': 'task'
	}

	FAKES_FLAGS = {
		'<flag_ctf:(fakeflag1)>': 'tryit',
		'<flag_ctf:(fakeflag2)>': 'task'
	}

	RU_CITIES = []
	SUPPORT_VK = '@pythonyashka'

	BAN_LIST = [1, 2] # ids vk int

