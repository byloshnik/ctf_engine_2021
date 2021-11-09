# -*- coding: utf-8 -*-
from vk_api import *
from vk_api.utils import get_random_id
from app import app
from .nc import NetCat
import json
from configs.texts import MsgTexts
from configs.cmds import UserBotCmds, AdminBotCmds
import time
import shutil
from .db import User, Settings, Answers
from .keyboard import BotKeyboard
from .mailing import Mailing
import time
import re

vk_session = vk_api.VkApi(token=app.config['VK_TOKEN'])
vk = vk_session.get_api()

nc = NetCat(app.config['SOCKET_MSG']['host'], app.config['SOCKET_MSG']['port'])

mailing = Mailing(app.config['MAILING_TOKENS'], app.config['USER_TOKEN'],
					app.config['MAILING']['album_id'], app.config['GROUP_ID'])

city_mas = list(app.config['CIRY_JSON_LIST'].values())

vk_user_session = vk_api.VkApi(token=app.config['USER_TOKEN'])
vk_user = vk_user_session.get_api()

def online():
	try:
		vk.groups.enableOnline(group_id=VkPersonal.group_id)
	except Exception as error:
		...


def send_socket_msg(peer_id='', message='', attachment='', user_ids='', user_id='',
					forward_messages='', sticker_id='', keyboard='', peer_ids='', disable_mentions=''):

	partner = vk.groups.isMember(
					group_id=app.config['GROUP_ID'],
					user_id=peer_id
				)

	if partner != 1:
		message += '\n\n👉 Ты ещё не подписан ' + app.config['SUB_PLS_URL']

	to_send = {"type": "send_msg", "peer_id": peer_id, "message": message, "attachment": attachment,
				"forward_messages": forward_messages, "sticker_id": sticker_id, "keyboard": keyboard,
				"peer_ids": peer_ids, "user_id": user_id, "user_ids": user_ids, "disable_mentions": disable_mentions,
				"secret": app.config['SOCKET_MSG']['msg_module_secret']}

	nc.write(json.dumps(to_send).encode())
	nc.read()


def get_biggest_size(data):
	biggest_size = max(data, key=lambda x: x['width'] * x['height'])
	return biggest_size

def go_to_menu(user_query):
	user_query.position = 'start'
	user_query.save()

def moder_teams():
	team_query = User.select().where(User.confirm_status == 0, User.participants_count != 0)

	if team_query.exists():
		team_query = team_query.get()
	else:
		return {'status': 0, 'team_moder_info': ''}

	team_moder_info = MsgTexts.team_moder_info % (
		team_query.team_name,
		f'[id{team_query.user_id}|{team_query.teamlead_name}]',
		team_query.phone,
		team_query.user_city,
		team_query.participants_count,
		'подтверждена' if team_query.confirm_status else 'ожидание проверки'
	)

	return {'status': 1, 'team_moder_info': team_moder_info, 'user_id': team_query.user_id}

def part_chek_moder(peer_id, user_query):
	resp = moder_teams()

	to_send = MsgTexts.no_teams_to_moder if resp['status'] == 0 else resp['team_moder_info']

	if resp['status'] != 0:
		user_query.position = f'moder_{resp["user_id"]}'
		user_query.save()
	else:
		user_query.position = f'start'
		user_query.save()

	send_socket_msg(
		peer_id=peer_id,
		message=to_send,
		keyboard=BotKeyboard.moder(user_query, peer_id) if resp['status'] != 0 else BotKeyboard.main(user_query, peer_id)
	)

def message_new(data):
	text = data['object']['message']['text'].lower()
	text_not_lowet = data['object']['message']['text']
	peer_id = data['object']['message']['peer_id']

	if int(peer_id) in app.config['BAN_LIST']:
		send_socket_msg(
			peer_id=peer_id,
			message=MsgTexts.diskval
		)
		return

	user_query = User.select().where(User.user_id == int(peer_id))

	if not user_query.exists():
		User(user_id=peer_id).save()
		user_query = user_query.get()
		send_socket_msg(
			peer_id=peer_id,
			message=MsgTexts.new_user + MsgTexts.to_unsub,
			keyboard=BotKeyboard.main(user_query, peer_id)
		)
		return

	user_query = user_query.get()

	if user_query.position != 'start':
		if user_query.position == 'start_reg':
			if 'geo' in data['object']['message'] and data['object']['message']['geo'] \
				and 'place' in data['object']['message']['geo'] \
				and data['object']['message']['geo']['place'] \
				and 'city' in data['object']['message']['geo']['place'] \
				and data['object']['message']['geo']['place']['city'] \
				and data['object']['message']['geo']['place']['city'].lower() or text != '':
				# in city_mas or text in city_mas:

				if 'geo' in data['object']['message']:
					# user_area = city_mas.index(data['object']['message']['geo']['place']['city'].lower()) + 1
					user_city = data['object']['message']['geo']['place']['city'].lower()
				else:
					# user_area = city_mas.index(text) + 1
					user_city = text

				if user_city.lower() in app.config['RU_CITIES']:
					user_query.user_city = user_city
					user_query.position = 'get_fio'
					user_query.save()

					send_socket_msg(
						peer_id=peer_id,
						message=MsgTexts.yes_city % user_city.title(),
						keyboard=BotKeyboard.exit_only(user_query, peer_id)
					)
				elif text in UserBotCmds.exit:
					go_to_menu(user_query)

					send_socket_msg(
						peer_id=peer_id,
						message=MsgTexts.exit,
						keyboard=BotKeyboard.main(user_query, peer_id)
					)
				else:
					send_socket_msg(
						peer_id=peer_id,
						message=MsgTexts.error_city_data % app.config['SUPPORT_VK'],
						keyboard=BotKeyboard.get_city(user_query, peer_id)
					)
					

			elif text in UserBotCmds.exit:
				go_to_menu(user_query)

				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.exit,
					keyboard=BotKeyboard.main(user_query, peer_id)
				)
			else:
				# send_socket_msg(
				# 	peer_id=peer_id,
				# 	message=MsgTexts.no_city_img,
				# 	attachment='photo-192411129_457239021',
				# 	keyboard=BotKeyboard.get_city(user_query, peer_id)
				# )
				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.start_reg,
					keyboard=BotKeyboard.get_city(user_query, peer_id)
				)

		elif user_query.position == 'get_fio':
			if text.__len__() < app.config['FIO_LEN']['min']:
				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.small_fio % app.config['FIO_LEN']['min'],
					keyboard=BotKeyboard.exit_only(user_query, peer_id)
				)
			elif text.__len__() > app.config['FIO_LEN']['max']:
				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.big_fio % app.config['FIO_LEN']['max'],
					keyboard=BotKeyboard.exit_only(user_query, peer_id)
				)
			elif text in UserBotCmds.exit:
				go_to_menu(user_query)

				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.exit,
					keyboard=BotKeyboard.main(user_query, peer_id)
				)
			else:
				user_query.teamlead_name = text_not_lowet
				user_query.position = 'get_teamname'
				user_query.save()

				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.yes_fio % text_not_lowet,
					keyboard=BotKeyboard.exit_only(user_query, peer_id)
				)

		elif user_query.position == 'get_teamname':
			if app.config['TEAMNAME_LEN']['min'] < text.__len__() < app.config['TEAMNAME_LEN']['max']:
				check_query = User.select().where(User.team_name == text)
				if not check_query.exists():
					user_query.team_name = text_not_lowet
					user_query.position = 'get_phone'
					user_query.save()

					send_socket_msg(
						peer_id=peer_id,
						message=MsgTexts.yes_teamname % text_not_lowet,
						keyboard=BotKeyboard.exit_only(user_query, peer_id)
					)
				elif text in UserBotCmds.exit:
					go_to_menu(user_query)

					send_socket_msg(
						peer_id=peer_id,
						message=MsgTexts.exit,
						keyboard=BotKeyboard.main(user_query, peer_id)
					)
				else:
					send_socket_msg(
						peer_id=peer_id,
						message=MsgTexts.team_name_allready_exists,
						keyboard=BotKeyboard.exit_only(user_query, peer_id)
					)


			elif text in UserBotCmds.exit:
				go_to_menu(user_query)

				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.exit,
					keyboard=BotKeyboard.main(user_query, peer_id)
				)

			else:
				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.error_teamname,
					keyboard=BotKeyboard.main(user_query, peer_id)
				)


		elif user_query.position == 'get_phone':
			# if text[0] == '7' and text.__len__() == 11 and text.isdigit():
			if app.config['RE_NUMBER'].match(text.replace(" ", "")):
				user_query.phone = text
				user_query.position = 'get_participants_count'
				user_query.save()

				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.yes_tel % text,
					keyboard=BotKeyboard.get_participants_count(user_query, peer_id)
				)

			elif text in UserBotCmds.exit:
				go_to_menu(user_query)

				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.exit,
					keyboard=BotKeyboard.main(user_query, peer_id)
				)

			else:
				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.no_tel,
					keyboard=BotKeyboard.exit_only(user_query, peer_id)
				)

		elif user_query.position == 'get_participants_count':
			if text in ['1', '2', '3', '4', '5']:
				user_query.participants_count = int(text)
				user_query.position = 'start'
				user_query.save()

				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.end_reg,
					keyboard=BotKeyboard.main(user_query, peer_id)
				)

			elif text in UserBotCmds.exit:
				go_to_menu(user_query)

				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.exit,
					keyboard=BotKeyboard.main(user_query, peer_id)
				)

			else:
				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.no_team_count,
					keyboard=BotKeyboard.get_participants_count(user_query, peer_id)
				)

		elif user_query.position == 'give_flag':
			if app.config['RE_FLAG'].match(text.replace(" ", "")):

				if text_not_lowet not in list(app.config['FAKES_FLAGS'].keys()):

					need_keys = list(app.config['TASKS_FLAGS'].keys())

					if text_not_lowet in need_keys:

						task_name = app.config['TASKS_FLAGS'][text_not_lowet]
						points_to_add = app.config['TASKS_DATA_FROM_NAME'][task_name]['points']

						answers_check_query = Answers.select().where(
								Answers.user==user_query, 
								Answers.text_flag==text_not_lowet,
								Answers.flag_is_true==1
							)

						if not answers_check_query.exists():
							Answers(
								user=user_query,
								text_flag=text_not_lowet,
								ts=int(time.time()),
								flag_is_true=True,
								task_name=task_name,
								points=int(points_to_add)
							).save()

							user_query.points += int(points_to_add)
							user_query.tasks_solved_count += 1
							user_query.save()

							first_check_query = Answers.select().where(
								Answers.text_flag==text_not_lowet,
								Answers.flag_is_true==1
							).count()

							if first_check_query == 1:
								vk_user.wall.post(
									owner_id=-app.config['GROUP_ID'],
									message=MsgTexts.first_boold_text % (
										task_name,
										user_query.team_name
									),
									from_group=1
								)

							go_to_menu(user_query)

							send_socket_msg(
								peer_id=peer_id,
								message=MsgTexts.flag_ok % (
										task_name,
										points_to_add,
										user_query.points
									),
								keyboard=BotKeyboard.main(user_query, peer_id)
							)
						else:
							send_socket_msg(
								peer_id=peer_id,
								message=MsgTexts.flag_exists_error,
								keyboard=BotKeyboard.exit_only(user_query, peer_id)
							)

					else:

						Answers(
							user=user_query,
							text_flag=text_not_lowet,
							ts=int(time.time()),
							flag_is_true=False,
							task_name='null',
							points=0
						).save()

						send_socket_msg(
							peer_id=peer_id,
							message=MsgTexts.flag_error,
							keyboard=BotKeyboard.exit_only(user_query, peer_id)
						)
						
						

				else:

					fake_flag = text_not_lowet 
					task_detect = app.config['FAKES_FLAGS'][fake_flag]
					points_to_add = app.config['TASKS_DATA_FROM_NAME'][task_detect]['points']

					answers_check_query = Answers.select().where(
								Answers.user==user_query, 
								Answers.text_flag==fake_flag,
								Answers.flag_is_true==1
							)
					print(answers_check_query)
					if not answers_check_query.exists():

						Answers(
							user=user_query,
							text_flag=fake_flag,
							ts=int(time.time()),
							flag_is_true=True,
							task_name=task_detect,
							points=int(points_to_add)
						).save()

						user_query.points += int(points_to_add)
						user_query.tasks_solved_count += 1
						user_query.save()

						go_to_menu(user_query)

						send_socket_msg(
							peer_id=peer_id,
							message=MsgTexts.flag_ok % (
									task_detect,
									points_to_add,
									user_query.points
								),
							keyboard=BotKeyboard.main(user_query, peer_id)
						)

						for admin in app.config['VK_ADMINS']:
							send_socket_msg(
								peer_id=admin,
								message=MsgTexts.fake_detect % (
										f'[id{user_query.user_id}|{user_query.teamlead_name}]',
										task_detect,
										fake_flag
									),
								keyboard=BotKeyboard.exit_only(user_query, peer_id)
							)
					else:
						send_socket_msg(
							peer_id=peer_id,
							message=MsgTexts.flag_exists_error,
							keyboard=BotKeyboard.exit_only(user_query, peer_id)
						)


			elif text in UserBotCmds.exit:
				go_to_menu(user_query)

				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.exit,
					keyboard=BotKeyboard.main(user_query, peer_id)
				)
			else:
				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.give_flag_msg,
					keyboard=BotKeyboard.exit_only(user_query, peer_id)
				)

		elif user_query.position.startswith('moder_'):

			team_id = int(user_query.position.replace('moder_', ''))
			team_query = User.select().where(User.user_id == team_id).get()

			if text in AdminBotCmds.ok:
				team_query.confirm_status = 1
				team_query.reg_time = time.time()
				team_query.save()

				send_socket_msg(
					peer_id=team_query.user_id,
					message=MsgTexts.approved_team % team_query.team_name,
					keyboard=BotKeyboard.main(team_query, team_query.user_id)
				)

				part_chek_moder(peer_id, user_query)

			elif text in AdminBotCmds.no:
				t_name = user_query.team_name

				team_query.participants_count = 0
				team_query.area_num = 0
				team_query.city = ''
				team_query.phone = ''
				team_query.teamlead_name = ''
				team_query.confirm_status = 0
				team_query.reg_time = 0
				team_query.team_name = ''
				team_query.save()

				send_socket_msg(
					peer_id=team_query.user_id,
					message=MsgTexts.refused_team % t_name,
					keyboard=BotKeyboard.main(team_query, team_query.user_id)
				)
				part_chek_moder(peer_id, user_query)

			elif text in UserBotCmds.exit:
				go_to_menu(user_query)

				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.exit,
					keyboard=BotKeyboard.main(user_query, peer_id)
				)
			else:
				send_socket_msg(
						peer_id=peer_id,
						message='111111111',
						keyboard=BotKeyboard.moder(user_query, peer_id)
					)

		elif user_query.position == 'mailing_menu':

			if text in AdminBotCmds.global_mailing:
				user_query.position = 'global_mailing'
				user_query.save()

				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.global_mailing_wait,
					keyboard=BotKeyboard.exit_only(user_query, peer_id)
				)

			elif text in AdminBotCmds.test_mailing:
				user_query.position = 'test_mailing'
				user_query.save()

				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.test_mailing_wait,
					keyboard=BotKeyboard.exit_only(user_query, peer_id)
				)

			elif text in UserBotCmds.exit:
				go_to_menu(user_query)

				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.exit,
					keyboard=BotKeyboard.main(user_query, peer_id)
				)
			else:
				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.mailing_menu_error,
					keyboard=BotKeyboard.mailing_menu(user_query, peer_id)
				)

		elif user_query.position == 'global_mailing':
			if text not in UserBotCmds.exit:
				if 'reply_message' in data['object']['message'].keys():

					if data['object']['message']['reply_message']:
						mailing_obj = data['object']['message']['reply_message']
					else:
						mailing_obj = data['object']['message']

				elif data['object']['message']['fwd_messages']:
					mailing_obj = data['object']['message']['fwd_messages'][0]

				else:
					mailing_obj = data['object']['message']

				mailing_data = mailing.generate_data(mailing_obj)

				go_to_menu(user_query)

				send_socket_msg(
						peer_id=peer_id,
						message=MsgTexts.mailing_start,
						keyboard=BotKeyboard.main(user_query, peer_id)
					)

				to_send = {
					"type": "start_mailing", 
					"secret": app.config['SOCKET_MSG']['msg_module_secret'],
					"mailing_type": 'global_mailing',
					"mailing_data": mailing_data,
					"admin_id": peer_id
				}

				nc.write(json.dumps(to_send).encode())
				nc.read()

				return
			else:
				go_to_menu(user_query)

				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.exit,
					keyboard=BotKeyboard.main(user_query, peer_id)
				)

		elif user_query.position == 'test_mailing':
			if text not in UserBotCmds.exit:
				if 'reply_message' in data['object']['message'].keys():

					if data['object']['message']['reply_message']:
						mailing_obj = data['object']['message']['reply_message']
					else:
						mailing_obj = data['object']['message']

				elif data['object']['message']['fwd_messages']:
					mailing_obj = data['object']['message']['fwd_messages'][0]

				else:
					mailing_obj = data['object']['message']

				mailing_data = mailing.generate_data(mailing_obj)

				go_to_menu(user_query)

				send_socket_msg(
						peer_id=peer_id,
						message=MsgTexts.mailing_start,
						keyboard=BotKeyboard.main(user_query, peer_id)
					)

				to_send = {
					"type": "start_mailing", 
					"secret": app.config['SOCKET_MSG']['msg_module_secret'],
					"mailing_type": 'test_mailing',
					"mailing_data": mailing_data,
					"admin_id": peer_id
				}

				nc.write(json.dumps(to_send).encode())
				nc.read()

				return
			else:
				go_to_menu(user_query)

				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.exit,
					keyboard=BotKeyboard.main(user_query, peer_id)
				)
	else:

		if text in UserBotCmds.help_cmd:
			send_socket_msg(
				peer_id=peer_id,
				message=app.config['HELP_URL'],
				keyboard=BotKeyboard.main(user_query, peer_id)
			)

		elif text in UserBotCmds.rules_cmd:
			send_socket_msg(
				peer_id=peer_id,
				message=app.config['RULES_URL'],
				keyboard=BotKeyboard.main(user_query, peer_id)
			)

		elif text in UserBotCmds.give_flag:

			config_query = Settings.select().where(Settings.key == "is_ctf_started").get()

			if config_query.value == "1" and user_query.participants_count > 0:
				user_query.position = 'give_flag'
				user_query.save()

				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.give_flag_msg,
					keyboard=BotKeyboard.exit_only(user_query, peer_id)
				)
			else:
				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.ctf_allready_stoped,
					keyboard=BotKeyboard.exit_only(user_query, peer_id)
				)

		elif text in UserBotCmds.stats:

			config_query = Settings.select().where(Settings.key == "is_ctf_started").get()

			if config_query.value == "1" and user_query.participants_count > 0:
				select_a = iter(Answers.select().where(Answers.user == user_query, Answers.flag_is_true == 1))

				tasks = []
				pts = 0
				for i, select_a_user in enumerate(select_a, 1):
					tasks.append(select_a_user.task_name)

				tasktext = ''
				for t in tasks:
					tasktext += t + '\n'

				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.u_stats % (
							user_query.points,
							tasks.__len__(),
							tasktext
						),
					keyboard=BotKeyboard.main(user_query, peer_id)
				)

			else:
				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.ctf_allready_stoped,
					keyboard=BotKeyboard.main(user_query, peer_id)
				)

		elif text in UserBotCmds.to_reg:
			config_query = Settings.select().where(Settings.key == "is_ctf_started").get()

			if config_query.value == "0":
				if user_query.participants_count == 0:
					user_query.position = 'start_reg'
					user_query.save()

					send_socket_msg(
						peer_id=peer_id,
						message=MsgTexts.start_reg,
						keyboard=BotKeyboard.get_city(user_query, peer_id)
					)
				else:
					send_socket_msg(
						peer_id=peer_id,
						message=MsgTexts.already_reg,
						keyboard=BotKeyboard.main(user_query, peer_id)
					)
			else:
				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.ctf_registration_stoped,
					keyboard=BotKeyboard.main(user_query, peer_id)
				)

		elif text in UserBotCmds.team_info: 
			if user_query.participants_count != 0:
				team_info_msg = MsgTexts.team_info % (
						user_query.team_name,
						user_query.teamlead_name,
						user_query.phone,
						user_query.user_city,
						user_query.participants_count,
						'подтверждена' if user_query.confirm_status else 'ожидание проверки'
					)

				send_socket_msg(
					peer_id=peer_id,
					message=team_info_msg,
					keyboard=BotKeyboard.main(user_query, peer_id)
				)
			else:
				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.no_team_info,
					keyboard=BotKeyboard.main(user_query, peer_id)
				)

		elif text in UserBotCmds.sub:
			user_query.activity = 1
			user_query.save()

			send_socket_msg(
				peer_id=peer_id,
				message=MsgTexts.sub,
				keyboard=BotKeyboard.main(user_query, peer_id)
			)

		elif text in UserBotCmds.unsub:
			user_query.activity = 0
			user_query.save()

			send_socket_msg(
				peer_id=peer_id,
				message=MsgTexts.unsub,
				keyboard=BotKeyboard.main(user_query, peer_id)
			)

		elif text in AdminBotCmds.mailing and peer_id in app.config['VK_ADMINS']:
			user_query.position = 'mailing_menu'
			user_query.save()

			send_socket_msg(
				peer_id=peer_id,
				message=MsgTexts.mailing_menu \
				% User.select().where(User.activity == 1).count(),
				keyboard=BotKeyboard.mailing_menu(user_query, peer_id)
			)

		elif text in AdminBotCmds.moder and peer_id in app.config['VK_ADMINS']:
			part_chek_moder(peer_id, user_query)		

		elif text in AdminBotCmds.stats and peer_id in app.config['VK_ADMINS']:
			# Колв. всех пользователей 
			all_users_count = User.select().count() 

			# Колв. пользователей, которые прошли регу
			users_count_with_reg_count = User.select().where(User.participants_count != 0).count()

			# Колв. пользователей, которые ожидают модерации
			users_count_wait_moder_count = User.select().where(User.confirm_status == 0, User.participants_count != 0).count()

			# Колв пользователей, которые прошли модерацию
			users_count_with_moder_count = User.select().where(User.confirm_status == 1, User.participants_count != 0).count()

			# Колв. пользователей, которые подписаны на рассылку
			users_count_with_activity_count = User.select().where(User.activity == 1).count()

			# Колв. пользователей, которые не подписаны на рассылку
			users_count_with_no_activity_count = all_users_count - users_count_with_activity_count

			send_socket_msg(
				peer_id=peer_id,
				message=MsgTexts.stats % (
						all_users_count, 
						users_count_with_reg_count,
						users_count_wait_moder_count,
						users_count_with_moder_count,
						users_count_with_activity_count,
						users_count_with_no_activity_count
					),
				keyboard=BotKeyboard.main(user_query, peer_id)
			)

		elif text in AdminBotCmds.start_ctf and peer_id in app.config['VK_ADMINS']:
			config_query = Settings.select().where(Settings.key == "is_ctf_started").get()

			if config_query.value == "0":
				config_query.value = "1"
				config_query.save()

				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.ctf_started,
					keyboard=BotKeyboard.main(user_query, peer_id)
				)
			else:	
				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.ctf_allready_started,
					keyboard=BotKeyboard.main(user_query, peer_id)
				)

		elif text in AdminBotCmds.stop_ctf and peer_id in app.config['VK_ADMINS']:
			config_query = Settings.select().where(Settings.key == "is_ctf_started").get()

			if config_query.value == "1":
				config_query.value = "0"
				config_query.save()

				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.ctf_stoped,
					keyboard=BotKeyboard.main(user_query, peer_id)
				)
			else:
				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.ctf_allready_stoped,
					keyboard=BotKeyboard.main(user_query, peer_id)
				)


		# elif text in AdminBotCmds.dump and peer_id in app.config['VK_ADMINS']:
		# 	to_send = {
		# 		"type": "dump_to_excel", 
		# 		"secret": app.config['SOCKET_MSG']['msg_module_secret'],
		# 		"user_id": peer_id
		# 	}

		# 	nc.write(json.dumps(to_send).encode())
		# 	nc.read()

		else:
			config_query = Settings.select().where(Settings.key == "is_ctf_started").get()

			if config_query.value == "0":
				send_socket_msg(
					peer_id=peer_id,
					message=MsgTexts.old_user,
					keyboard=BotKeyboard.main(user_query, peer_id)
				)
			else:
				if user_query.participants_count == 0:
					send_socket_msg(
						peer_id=peer_id,
						message=MsgTexts.ctf_has_allready_started,
						keyboard=BotKeyboard.main(user_query, peer_id)
					)
				else:
					send_socket_msg(
						peer_id=peer_id,
						message=MsgTexts.flag_give_main_msg,
						keyboard=BotKeyboard.main(user_query, peer_id)
					)