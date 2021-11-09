# -*- coding: utf-8 -*-
import os
from shutil import copyfile
import argparse
import sys
import json

usage_text = 'Use "manage.py config" to configure this application\n' \
             'Use "manage.py dbmigrate" to migrate database\n' \
			 'Use "manage.py dbsettings" to configurate Settings Model'

configs_path = 'configs'
manage_path = 'manage'
files_to_copy = ['config.py']


class MyParser(argparse.ArgumentParser):
	def error(self, message):
		sys.stderr.write(usage_text)
		sys.exit(2)


my_parser = MyParser()
my_parser.add_argument("pram")

args = my_parser.parse_args()

if args.pram == 'config':

	steps = 0

	sys.stderr.write('Start the configuration ...\n')
	sys.stderr.write('-' * 20 + '\n')
	if not os.path.exists(configs_path):
		os.makedirs(configs_path)
		sys.stderr.write('Created directory: ' + configs_path + '\n')
		steps += 1
		directory_created = True
	else:
		directory_created = False

	dir_configs = os.listdir(configs_path)

	for file in files_to_copy:
		if file not in dir_configs:
			copyfile(manage_path + '/' + file, configs_path + '/' + file)
			sys.stderr.write('Created file: ' + configs_path + '/' + file + '\n')
			steps += 1

	if steps >= 1:
		sys.stderr.write('-' * 20 + '\n')
	sys.stderr.write('Steps taken: %s' % steps + '\n')
	sys.stderr.write('Successfully completed')

elif args.pram == 'dbmigrate':
	from modules.db import *
	db.evolve()
elif args.pram == 'dbsettings':	
	from modules.db import *
	Settings(key = "is_ctf_started", value = "1").save()

else:
	sys.stderr.write(usage_text)
	sys.exit(2)
