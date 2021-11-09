# -*- coding: utf-8 -*-
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from .db import User, Settings
from app import app


class BotKeyboard(object):
	"""docstring for BotKeyboard"""
	def __init__(self, arg):
		super(BotKeyboard, self).__init__()
		self.arg = arg

	@staticmethod
	def main(user_query, user_id):

		config_query = Settings.select().where(Settings.key == "is_ctf_started").get()

		keyboard = VkKeyboard(one_time=True)

		if config_query.value == "0":
			if user_query.participants_count == 0:
				keyboard.add_button('🚀 Зарегистрироваться', color=VkKeyboardColor.DEFAULT)
			else:
				keyboard.add_button('💡 Информация о команде', color=VkKeyboardColor.DEFAULT)
		
			keyboard.add_line()
		elif user_query.participants_count > 0:
			keyboard.add_button("🚩 Отправить flag", color=VkKeyboardColor.DEFAULT)
			keyboard.add_button("📊 Статистика", color=VkKeyboardColor.DEFAULT)
			keyboard.add_line()


		keyboard.add_button('📖 Правила', color=VkKeyboardColor.DEFAULT)
		keyboard.add_button('📖 Подробнее о CTF', color=VkKeyboardColor.DEFAULT)

		if user_id in app.config['VK_ADMINS']:
			keyboard.add_line()
			keyboard.add_button('Рассылка', color=VkKeyboardColor.DEFAULT)
			keyboard.add_button('Модерация', color=VkKeyboardColor.DEFAULT)
			keyboard.add_button('Статистика', color=VkKeyboardColor.DEFAULT)

			if config_query.value == "0":
				keyboard.add_line()
				keyboard.add_button("Start CTF", color=VkKeyboardColor.DEFAULT)
			else:
				keyboard.add_line()
				keyboard.add_button("Stop CTF", color=VkKeyboardColor.DEFAULT)
				
			# keyboard.add_line()
			# keyboard.add_button('Team info', color=VkKeyboardColor.DEFAULT)
			# keyboard.add_button('Ban/unban user', color=VkKeyboardColor.DEFAULT) 
			# keyboard.add_button('Unreg team', color=VkKeyboardColor.DEFAULT)
			# keyboard.add_line()
			# keyboard.add_button('Download excel dump', color=VkKeyboardColor.DEFAULT)

		return keyboard.get_keyboard()

	@staticmethod
	def mailing_menu(user_query, user_id):
		keyboard = VkKeyboard(one_time=True)

		keyboard.add_button('Основная', color=VkKeyboardColor.DEFAULT)
		keyboard.add_button('Тестовая', color=VkKeyboardColor.DEFAULT)
		keyboard.add_line()
		keyboard.add_button('Отмена', color=VkKeyboardColor.NEGATIVE)

		return keyboard.get_keyboard()

	@staticmethod
	def get_city(user_query, user_id):
		keyboard = VkKeyboard(one_time=True)

		keyboard.add_location_button()
		keyboard.add_line()
		keyboard.add_button('Отмена', color=VkKeyboardColor.NEGATIVE)

		return keyboard.get_keyboard()

	@staticmethod
	def get_participants_count(user_query, user_id):
		keyboard = VkKeyboard(one_time=True)	

		keyboard.add_button('1', color=VkKeyboardColor.DEFAULT)
		keyboard.add_button('2', color=VkKeyboardColor.DEFAULT)
		keyboard.add_line()
		keyboard.add_button('3', color=VkKeyboardColor.DEFAULT)
		keyboard.add_button('4', color=VkKeyboardColor.DEFAULT)
		keyboard.add_button('5', color=VkKeyboardColor.DEFAULT)
		keyboard.add_line()
		keyboard.add_button('Отмена', color=VkKeyboardColor.NEGATIVE)

		return keyboard.get_keyboard()

	@staticmethod
	def moder(user_query, user_id):
		keyboard = VkKeyboard(one_time=True)

		keyboard.add_button('Подтвердить', color=VkKeyboardColor.POSITIVE)
		keyboard.add_button('Отклонить', color=VkKeyboardColor.NEGATIVE)
		keyboard.add_line()
		keyboard.add_button('Отмена', color=VkKeyboardColor.NEGATIVE)

		return keyboard.get_keyboard()

	@staticmethod
	def exit_only(user_query, user_id):
		keyboard = VkKeyboard(one_time=True)
		keyboard.add_button('Отмена', color=VkKeyboardColor.NEGATIVE)

		return keyboard.get_keyboard()