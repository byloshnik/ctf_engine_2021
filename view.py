# -*- coding: utf-8 -*-
from flask import request, json, render_template, make_response, jsonify, abort, send_file
from app import app
import time
from modules.msg import message_new
import hashlib
from modules.db import Settings, Answers, User
from collections import Counter


@app.errorhandler(404)
def notfound_handler(error):
	return render_template(
		'error.html', 
		data={
			'footer_links': app.config['FOOTER_LINKS'],
			'error': {
				'code': '404',
				'text': 'Страница не найдена.'
			},
			"btns": [
				{"text": "Главная", "link": "/"},
				{"text": "Задания", "link": "/tasks"},
				{"text": "Результаты", "link": "/scoreboard"}
			]
		}
	)

@app.errorhandler(500)
def kotlyarov_handler(error):
	return render_template(
		'error.html', 
		data={
			'footer_links': app.config['FOOTER_LINKS'],
			'error': {
				'code': '500',
				'text': 'Внутренняя ошибка сервера.'
			},
			"btns": [
				{"text": "Главная", "link": "/"},
				{"text": "Задания", "link": "/tasks"},
				{"text": "Результаты", "link": "/scoreboard"}
			]
		}
	)

@app.errorhandler(405)
def notfound_handler(error):
	return make_response(jsonify(error="Method is not allowed(POST or GET) %s", text=str(error)), 404)


# @app.errorhandler(500)
# def kotlyarov_handler(error):
# 	return make_response(jsonify(error="Internal Server Error"), 500)

@app.route('/', methods=['GET'])
def index():
	return render_template(
		'home.html',
		data={
			'footer_links': app.config['FOOTER_LINKS'],
			"btns": [
				{"text": "Главная", "link": "#"},
				{"text": "Задания", "link": "/tasks"},
				{"text": "Результаты", "link": "/scoreboard"}
			]
		}
	)


@app.route('/tasks', methods=['GET'])
def tasks_func():
	if app.config['TASKS_DATA'] != 'none':
		config_query = Settings.select().where(Settings.key == "is_ctf_started").get()
		answers_query = Answers.select().where(Answers.flag_is_true == 1)

		btns = [
			{"text": "Главная", "link": "/"},
			{"text": "Задания", "link": "#"},
			{"text": "Результаты", "link": "/scoreboard"}
		]

		tasks_solus_mas = []
		for answer in list(answers_query):
			tasks_solus_mas.append(answer.task_name)

		count_sols = Counter(tasks_solus_mas)

		new_tasks_data = []
		for task_d in app.config['TASKS_DATA']:
			if task_d['name'] in count_sols.keys():
				new_task_d = task_d
				new_task_d.update({'solutions': count_sols[task_d['name']]})
			else:
				new_task_d = task_d
				new_task_d.update({'solutions': 0})

			new_tasks_data.append(new_task_d)

		if app.config['CHECK_IS_CTF_STARTED_IN_TASKS_PAGE']:
			if config_query.value == "0":
				return render_template(
					'tasks.html',
					data={
						'tasks_data': new_tasks_data,
						'footer_links': app.config['FOOTER_LINKS'],
						"btns": btns
					}
				)
			else:
				return render_template(
					'error.html', 
					data={
						'footer_links': app.config['FOOTER_LINKS'],
						'error': {
							'code': '403',
							'text': 'Доступ к заданиям ограничен до начала CTF.'
						},
						"btns": [
							{"text": "Главная", "link": "/"},
							{"text": "Задания", "link": "/tasks"},
							{"text": "Результаты", "link": "/scoreboard"}
						]
					}
				)
		else:
			return render_template(
					'tasks.html',
					data={
						'tasks_data': new_tasks_data,
						'footer_links': app.config['FOOTER_LINKS'],
						"btns": btns
					}
				)

	else:
		abort(404)


@app.route('/cloud/<string:name>.zip', methods=['GET'])
def get_task(name):
	if app.config['TASKS_DATA'] != 'none':
		config_query = Settings.select().where(Settings.key == "is_ctf_started").get()
		print(config_query.value)
		if app.config['CHECK_IS_CTF_STARTED_IN_TASKS_PAGE']:
			if config_query.value == "1":
				for i in app.config['TASKS_DATA']:
					if i['name'] == name:
						return send_file(f'res/tasks/{i["path_name"]}/{i["to_send"]}', attachment_filename=i["to_send"])
				abort(404)
			else:
				abort(404)
		else:
			for i in app.config['TASKS_DATA']:
				if i['name'] == name:
					return send_file(f'res/tasks/{i["path_name"]}/{i["to_send"]}', attachment_filename=i["to_send"])
			abort(404)
	else:
		abort(404)


@app.route('/vk', methods=['POST'])
def processing():
	data = json.loads(request.data)
	if 'type' not in data.keys():
		return 'not vk'
	else:

		if ('secret' in data) and data['secret'] == app.config['VK_SECRET']:

			if data['type'] == 'confirmation':
				return app.config['VK_CONFIRMATION']
			elif data['type'] == 'message_new':
				print(data)
				message_new(data)
				return 'ok'

			else:
				return 'ok'
		else:
			return 'ok'


@app.route("/scoreboard", methods=["GET"])
def scoreboard():
	users_data = []

	btns = [
		{"text": "Главная", "link": "/"},
		{"text": "Задания", "link": "/tasks"}
	]

	acticvity = iter(Answers.select().where(
						Answers.ts > time.time() - 2*60*60
					))

	acticvity_users_list = []

	for i, acticvity_user in enumerate(acticvity, 1):
		acticvity_users_list.append(acticvity_user.user_id)

	count_activty_user_list_without_repetitions = \
		set(acticvity_users_list).__len__()

	if "city" in request.values and request.values["city"]:
		user_query = list(User.select()
						  .where(User.id > 0, User.user_city == request.values["city"], User.confirm_status == 1)
						  .order_by(User.points.desc()))

		btns.append({"text": "Все города", "link": "/scoreboard"})

	else:
		user_query = list(User.select()
						  .where(User.id > 0, User.confirm_status == 1)
						  .order_by(User.points.desc()))	
		btns.append({"text": "Результаты", "link": "#"})

	for index, user_object in zip(range(user_query.__len__()), user_query):
		users_data.append({
			'team_name': user_object.team_name,
			'points': user_object.points,
			'place': index + 1,
			'tasks_solved_count': user_object.tasks_solved_count,
			"city": user_object.user_city,
			"vk_user_id": user_object.user_id
		})

	return render_template(
		'scoreboard.html',
		data={
			'users_data': users_data,
			'footer_links': app.config['FOOTER_LINKS'],
			"btns": btns,
			"active_count": count_activty_user_list_without_repetitions
		}
	)

@app.route('/ctftime/scoreboard', methods=["GET"])
def scoreboard_ctftime():
	ans = {'tasks': list(app.config['TASKS_DATA_FROM_NAME'].keys()), 'standings': []}

	users = iter(User.select()
				 .where(User.id > 0, User.confirm_status == 1)
				 .order_by(User.points.desc()))
	for num, user in enumerate(users, 1):
		task_stats = {}
		for answer in iter(Answers.select().where(Answers.user==user, Answers.flag_is_true==True).order_by(Answers.ts.asc())):
			task_stats[answer.task_name] = {'points': answer.points, 'time': answer.ts}
		ans['standings'].append({
			'pos': num,
			'team': user.team_name,
			'score': user.points,
		})

		if task_stats:
			ans['standings'][-1]['taskStats'] = task_stats
			ans['standings'][-1]['lastAccept'] = answer.ts
	return jsonify(ans)
