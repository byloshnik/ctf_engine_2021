# -*- coding: utf-8 -*-
from flask import Flask
from configs.config import Config
import sys
import os
import io

# @app.errorhandler(Exception)
# def exception_hook(e):
# 	return 'Internal Server Error'

tasks_list = os.listdir('res/tasks')
tasks_list.remove('.gitkeep')
# print(tasks_list)
tasks_data = []

if tasks_list:
	for folder in tasks_list:
		splited = folder.split('_')

		task_folder = os.listdir('res/tasks/' + folder)
		for rar in task_folder:
			splited_path = rar.split('.')
			if splited_path.__len__() >= 2:
				if 'rar' in splited_path or 'zip' in splited_path:
					path_to_send = rar
					break
				else:
					path_to_send = 'none'
			else:
				path_to_send = 'none'

		for md in task_folder:
			splited_path = md.split('.')
			if splited_path.__len__() >= 2:
				if 'md' in splited_path:
					path_to_md = md
					break
				else:
					path_to_md = 'none'
			else:
				path_to_md = 'none'

		if path_to_md != 'none':
			with io.open(f'res/tasks/{folder}/{path_to_md}', mode="r" , encoding="utf-8") as f:
				descp = f.read()
		else:
			descp = 'None'

		tasks_data.append({
			'id': int(splited[0]),
			'name': splited[1],
			'points': splited[2],
			'category': splited[3:],
			'path_name': folder,
			'to_send': path_to_send,
			'descp': descp.split('\n')
		})
else:
	tasks_list = 'none'

result_json = {}
for task_obj in tasks_data:
	result_json.update({task_obj['name']:task_obj})

with io.open(f'static_data/ru_cities.txt', mode="r", encoding="utf-8") as f:
	c_array = [row.strip() for row in f]

app = Flask(__name__)
app.config.from_object(Config)
app.config['TASKS_DATA'] = tasks_data
app.config['TASKS_DATA_FROM_NAME'] = result_json
app.config['RU_CITIES'] = c_array

print(app.config['TASKS_DATA'])




