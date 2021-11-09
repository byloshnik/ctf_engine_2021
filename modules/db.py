# -*- coding: utf-8 -*-
import sys
from peewee import *
from app import app
import peeweedbevolve
from flask import request


db = MySQLDatabase(
	app.config['MYSQL']['db_name'], user=app.config['MYSQL']['user_name'],
	password=app.config['MYSQL']['password'],
	host=app.config['MYSQL']['host'], port=app.config['MYSQL']['port']
)

class User(Model):

	user_id = IntegerField()  						# VK id пользователя
	position = CharField(default='start')			# Позиция юзера
	area_num = IntegerField(default=0) 				# Номер площадки на которой будет участвовать пользователь
	phone = CharField(default='')					# Номер телефона пользователя 
	teamlead_name = CharField(default='') 			# ФИО тимлида команды
	team_name = CharField(default='')				# Название команды
	confirm_status = BooleanField(default=0) 		# Статус подверждения команды (1 - подтверждена)
	reg_time = IntegerField(default=0)				# Таймстемп регистрация команды
	participants_count = IntegerField(default=0)	# Колв. участников от 1 до 5
	activity = BooleanField(default=1)				# Состояние подписки на рассылку

	user_city = CharField(default='')

	points = IntegerField(default=0) 				# Очки участников
	tasks_solved_count = IntegerField(default=0) 	# Решено тасков

	class Meta:
		database = db

class Settings(Model):
	id = IntegerField(default=1) 	
	key = CharField()
	value = CharField()

	class Meta:
		database = db	

class Answers(Model):
	user = ForeignKeyField(User, backref='answers')
	text_flag = CharField(default='')
	ts = IntegerField(default=0)
	flag_is_true = BooleanField(default=0)
	task_name = CharField(default='')
	points = IntegerField(default=0)

	class Meta:
		database = db

db.create_tables([User, Answers, Settings])

@app.before_request
def _db_connect():
	if db.is_closed():
		db.connect()


@app.after_request
def after_request(response):
	if request.path == '/favicon.ico':
		...
	elif request.path.startswith('/static'):
		...

	if not db.is_closed():
		db.close()

	return response