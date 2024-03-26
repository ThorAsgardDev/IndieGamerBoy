
import os
import sys
import traceback
import configparser
import requests
import tkinter
import tkinter.ttk
import tkinter.font
import tkinter.filedialog
import tkinter.messagebox
import lib.sheets_client
import lib.utils
import time
import asyncio
import threading

from twitchio.ext import commands
from twitchio.ext import routines


class Bot(commands.Bot):

	def __init__(self, config):
		# Initialise our Bot with our access token, prefix and a list of channels to join on boot...
		super().__init__(token=config["TWITCH"]["ACCESS_TOKEN"], prefix='?', initial_channels=[config["TWITCH"]["CHANNEL"]])
		self.config = config

	async def event_ready(self):
		# We are logged in and ready to chat and use commands...
		print(f'Logged in as | {self.nick}')
		print(f'User id is | {self.user_id}')

	'''
	@commands.command()
	async def hello(self, ctx: commands.Context):
		# Send a hello back!
		await ctx.send(f'Hello {ctx.author.name}!')
	'''
		
	async def repeat_message_loop(self, message, period_in_seconds):
		while True:
			await self.get_channel(self.config["TWITCH"]["CHANNEL"]).send(message)
			await asyncio.sleep(period_in_seconds)
			
	def start_repeat_message_task(self, message, period_in_seconds):
		return self.loop.create_task(self.repeat_message_loop(message, period_in_seconds))
		
	def stop_repeat_message_task(self, task):
		task.cancel()
		
class BotThread(threading.Thread):
	def __init__(self, config):
		threading.Thread.__init__(self)
		self.daemon = True
		self.bot = Bot(config)

	def run(self):
		self.bot.run()
		
	def get_bot(self):
		return self.bot


class MainFrame(tkinter.Frame):
	TOKENS_FILENAME = "tokens.ini"
	
	def __init__(self, config, bot, window, **kwargs):
		tkinter.Frame.__init__(self, window, **kwargs)
		
		self.window = window
		
		default_font = tkinter.font.nametofont("TkDefaultFont")
		default_font.configure(size=12)
		self.window.option_add("*Font", default_font)
		
		self.model = None
		
		self.bot = bot
		self.config = config
		
		self.utils = lib.utils.Utils()
		
		self.pack(expand = tkinter.YES, fill = tkinter.BOTH)
		
		self.create_label(self, "Jeux: ", 0, 0)
		self.combo_games = self.create_combo(self, self.on_combo_games_changed, 0, 1)
		self.create_label(self, "Suffixe: ", 0, 2)
		self.entry_name_suffix = self.create_entry(self, "", True, 0, 3)
		self.create_label(self, "Fichier texte: ", 0, 4)
		self.entry_name_text_file = self.create_entry(self, "name.txt", True, 0, 5, 2)
		
		self.entry_status, self.entry_status_suffix, self.entry_status_text_file = self.create_line_controls(1, "Status: ", "status.txt")
		self.entry_tested_version, self.entry_tested_version_suffix, self.entry_tested_version_text_file = self.create_line_controls(2, "Version testée: ", "tested-version.txt")
		self.entry_release_date, self.entry_release_date_suffix, self.entry_release_date_text_file = self.create_line_controls(3, "Date de sortie: ", "release-date.txt")
		self.entry_genre, self.entry_genre_suffix, self.entry_genre_text_file = self.create_line_controls(4, "Genre: ", "genre.txt")
		self.entry_developer, self.entry_developer_suffix, self.entry_developer_text_file = self.create_line_controls(5, "Développeur: ", "developer.txt")
		self.entry_publisher, self.entry_publisher_suffix, self.entry_publisher_text_file = self.create_line_controls(6, "Editeur: ", "publisher.txt")
		self.entry_country, self.entry_country_suffix, self.entry_country_text_file = self.create_line_controls(7, "Pays: ", "country.txt")
		self.entry_platforms, self.entry_platforms_suffix, self.entry_platforms_text_file = self.create_line_controls(8, "Plateformes: ", "platforms.txt")
		self.entry_price, self.entry_price_suffix, self.entry_price_text_file = self.create_line_controls(9, "Prix: ", "price.txt")
		self.entry_fr_language, self.entry_fr_language_suffix, self.entry_fr_language_text_file = self.create_line_controls(10, "Langue fr: ", "fr-language.txt")
		self.entry_length, self.entry_length_suffix, self.entry_length_text_file = self.create_line_controls(11, "Durée de vie: ", "length.txt")
		self.entry_misc, self.entry_misc_suffix, self.entry_misc_text_file = self.create_line_controls(12, "Divers: ", "misc.txt")
		self.entry_affiliate_link, self.entry_affiliate_link_suffix, self.entry_affiliate_link_text_file = self.create_line_controls(13, "Lien d'affiliation: ", "affiliate-link.txt")
		self.entry_affiliate_link_bot_button, self.entry_affiliate_link_bot_prefix_text, self.entry_affiliate_link_bot_period_text = self.add_bot_line_controls(14, self.on_bot_affiliate_link_click)
		
		self.create_button(self, "Recharger Gdoc", self.on_reload_sheet_click, 16, 0, 7)
		self.create_button(self, "Envoyer vers les fichiers textes", self.on_send_to_text_click, 17, 0, 7)
		
	def create_line_controls(self, line, label, text_file_name):
		self.create_label(self, label, line, 0)
		entry = self.create_entry(self, "", False, line, 1)
		self.create_label(self, "Suffixe: ", line, 2)
		suffix = self.create_entry(self, "", True, line, 3)
		self.create_label(self, "Fichier texte: ", line, 4)
		text_file = self.create_entry(self, text_file_name, True, line, 5, 2)
		return entry, suffix, text_file
		
	def add_bot_line_controls(self, line, on_click_cb):
		self.create_label(self, "Préfixe: ", line, 2)
		prefix_text = self.create_entry(self, "", True, line, 3)
		self.create_label(self, "Période (sec): ", line, 4)
		period_text = self.create_entry(self, "300", True, line, 5, 1, 5)
		button = self.create_button(self, "Start repeat in chat", on_click_cb, line, 6, 1)
		return button, prefix_text, period_text
		
	def on_bot_affiliate_link_click(self):
		if not hasattr(self, "bot_affiliate_link_task") or self.bot_affiliate_link_task is None:
			period_text = self.entry_affiliate_link_bot_period_text.get()
			bot_text = self.entry_affiliate_link_bot_prefix_text.get() + self.entry_affiliate_link.get()
			if period_text != "" and bot_text != "":
				period = int(self.entry_affiliate_link_bot_period_text.get())
				self.bot_affiliate_link_task = self.bot.start_repeat_message_task(bot_text, period)
				self.entry_affiliate_link_bot_button.config(text="Stop repeat in chat")
		else:
			self.stop_bot_affiliate_link()
			
	def stop_bot_affiliate_link(self):
		if hasattr(self, "bot_affiliate_link_task") and self.bot_affiliate_link_task is not None:
			self.bot.stop_repeat_message_task(self.bot_affiliate_link_task)
			self.bot_affiliate_link_task = None
			self.entry_affiliate_link_bot_button.config(text="Start repeat in chat")
			
	def create_label(self, frame, text, row, column, columnspan=1):
		label = tkinter.Label(frame, text = text, anchor = tkinter.W)
		label.grid(sticky=tkinter.W, padx=2, pady=2, row=row, column=column, columnspan=columnspan)
		return label
		
	def create_combo(self, frame, on_changed_cb, row, column):
		combo = tkinter.ttk.Combobox(frame, state = "readonly")
		combo.grid(sticky=tkinter.W, padx=2, pady=2, row=row, column=column)
		combo.bind("<<ComboboxSelected>>", on_changed_cb)
		return combo
		
	def create_entry(self, frame, text, enabled, row, column, columnspan=1, width=23):
		if enabled:
			entry = tkinter.Entry(frame, width=width)
		else:
			entry = tkinter.Entry(frame, state="readonly", width=width)
		entry.grid(sticky=tkinter.W, padx=2, pady=2, row=row, column=column, columnspan=columnspan)
		self.set_entry_text(entry, text)
		return entry
		
	def create_button(self, frame, text, on_click_cb, row, column, columnspan):
		button = tkinter.Button(frame, relief = tkinter.GROOVE, text = text, command = on_click_cb)
		button.grid(sticky="EW", padx=2, pady=2, row=row, column=column, columnspan=columnspan)
		return button
		
	def set_entry_text(self, entry, text):
		disabled = entry["state"] == "readonly"
		
		if disabled:
			entry.configure(state=tkinter.NORMAL)
			
		entry.delete(0, tkinter.END)
		entry.insert(0, text)
		
		if disabled:
			entry.configure(state="readonly")
		
	def get_combo_value(self, combo):
		current_index = combo.current()
		values = combo.cget("values")
		if current_index >= 0 and current_index < len(values):
			return values[current_index]
		return ""
		
	def select_combo_value(self, combo, value):
		values = combo.cget("values")
		
		i = 0
		for v in values:
			if v == value:
				combo.current(i)
				return True
			i += 1
			
		return False
		
	def on_reload_sheet_click(self):
		self.reload_sheet()
		
	def append_text_to_list(self, l, text, suffix):
		if text != "":
			l.append(text + suffix)
		return l
		
	def on_send_to_text_click(self):
		text_file_to_text = {}
		
		text_file_to_text[self.entry_name_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_name_text_file.get(), []), self.combo_games.cget("values")[self.combo_games.current()], self.entry_name_suffix.get())
		text_file_to_text[self.entry_status_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_status_text_file.get(), []), self.entry_status.get(), self.entry_status_suffix.get())
		text_file_to_text[self.entry_tested_version_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_tested_version_text_file.get(), []), self.entry_tested_version.get(), self.entry_tested_version_suffix.get())
		text_file_to_text[self.entry_release_date_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_release_date_text_file.get(), []), self.entry_release_date.get(), self.entry_release_date_suffix.get())
		text_file_to_text[self.entry_genre_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_genre_text_file.get(), []), self.entry_genre.get(), self.entry_genre_suffix.get())
		text_file_to_text[self.entry_developer_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_developer_text_file.get(), []), self.entry_developer.get(), self.entry_developer_suffix.get())
		text_file_to_text[self.entry_publisher_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_publisher_text_file.get(), []), self.entry_publisher.get(), self.entry_publisher_suffix.get())
		text_file_to_text[self.entry_country_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_country_text_file.get(), []), self.entry_country.get(), self.entry_country_suffix.get())
		text_file_to_text[self.entry_platforms_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_platforms_text_file.get(), []), self.entry_platforms.get(), self.entry_platforms_suffix.get())
		text_file_to_text[self.entry_price_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_price_text_file.get(), []), self.entry_price.get(), self.entry_price_suffix.get())
		text_file_to_text[self.entry_fr_language_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_fr_language_text_file.get(), []), self.entry_fr_language.get(), self.entry_fr_language_suffix.get())
		text_file_to_text[self.entry_length_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_length_text_file.get(), []), self.entry_length.get(), self.entry_length_suffix.get())
		text_file_to_text[self.entry_misc_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_misc_text_file.get(), []), self.entry_misc.get(), self.entry_misc_suffix.get())
		text_file_to_text[self.entry_affiliate_link_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_affiliate_link_text_file.get(), []), self.entry_affiliate_link.get(), self.entry_affiliate_link_suffix.get())
		
		for k, v in text_file_to_text.items():
			if k != "":
				self.utils.write_file("wb", "text-files/" + k, "".join(v))
		
	def on_combo_games_changed(self, event):
		self.process_on_combo_games_changed(None)
		
	def fill_games(self, init_values):
		values = []
		
		for value in self.model["games"]:
			values.append(value)
		
		self.combo_games.config(values = values)
		if len(values) > 0:
			self.combo_games.current(0)
		
		if init_values and ("game" in init_values):
			self.select_combo_value(self.combo_games, init_values["game"])
			
		self.process_on_combo_games_changed(init_values)
		
	def process_on_combo_games_changed(self, init_values):
		current_game = self.get_combo_value(self.combo_games)
		
		if current_game != self.model["current_game"]:
			self.model["current_game"] = current_game
			
			model_game = self.model["games"][current_game]
			
			self.stop_bot_affiliate_link()
			
			self.set_entry_text(self.entry_status, model_game["status"])
			self.set_entry_text(self.entry_tested_version, model_game["tested_version"])
			self.set_entry_text(self.entry_release_date, model_game["release_date"])
			self.set_entry_text(self.entry_genre, model_game["genre"])
			self.set_entry_text(self.entry_developer, model_game["developer"])
			self.set_entry_text(self.entry_publisher, model_game["publisher"])
			self.set_entry_text(self.entry_country, model_game["country"])
			self.set_entry_text(self.entry_platforms, self.build_platform_label(model_game))
			self.set_entry_text(self.entry_price, model_game["price"])
			self.set_entry_text(self.entry_fr_language, "Oui" if model_game["fr_language"] == "TRUE" else "Non")
			self.set_entry_text(self.entry_length, model_game["length"])
			self.set_entry_text(self.entry_misc, model_game["misc"])
			self.set_entry_text(self.entry_affiliate_link, model_game["affiliate_link"])
			
			self.on_send_to_text_click()
			
	def build_platform_label(self, model_game):
		l = []
		if model_game["nintendo"] == "TRUE":
			l.append("Nintendo")
		if model_game["playstation"] == "TRUE":
			l.append("Playstation")
		if model_game["xbox"] == "TRUE":
			l.append("Xbox")
		if model_game["pc"] == "TRUE":
			l.append("PC")
		return "/".join(l)
			
	def set_sheet_data_simple_values_to_model(self, data, start_row, row_id_to_game, model, field_name):
		row_id = start_row
		
		if "rowData" not in data:
			return
			
		for row_data in data["rowData"]:
			if row_id in row_id_to_game:
				if "values" in row_data and "formattedValue" in row_data["values"][0]:
					model["games"][row_id_to_game[row_id]][field_name] = row_data["values"][0]["formattedValue"].strip()
			row_id += 1
			
	def build_model(self):
		model = {
			"current_game": "",
			"games": {},
		}
		
		config_sheet = self.config["SHEET"]
		
		# response = self.sheets_client.get_sheets()
		
		first_line = config_sheet["FIRST_GAME_LINE"]
		
		ranges = []
		
		worksheet_name = "Saison en cours"
		
		ranges.append(worksheet_name + "!" + config_sheet["NAME_COLUMN"] + first_line + ":" + config_sheet["NAME_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["STATUS_COLUMN"] + first_line + ":" + config_sheet["STATUS_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["TESTED_VERSION_COLUMN"] + first_line + ":" + config_sheet["TESTED_VERSION_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["AFFILIATE_LINK_COLUMN"] + first_line + ":" + config_sheet["AFFILIATE_LINK_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["RELEASE_DATE_COLUMN"] + first_line + ":" + config_sheet["RELEASE_DATE_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["GENRE_COLUMN"] + first_line + ":" + config_sheet["GENRE_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["DEVELOPER_COLUMN"] + first_line + ":" + config_sheet["DEVELOPER_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["PUBLISHER_COLUMN"] + first_line + ":" + config_sheet["PUBLISHER_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["COUNTRY_COLUMN"] + first_line + ":" + config_sheet["COUNTRY_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["NINTENDO_COLUMN"] + first_line + ":" + config_sheet["NINTENDO_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["PLAYSTATION_COLUMN"] + first_line + ":" + config_sheet["PLAYSTATION_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["XBOX_COLUMN"] + first_line + ":" + config_sheet["XBOX_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["PC_COLUMN"] + first_line + ":" + config_sheet["PC_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["PRICE_COLUMN"] + first_line + ":" + config_sheet["PRICE_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["FR_LANGUAGE_COLUMN"] + first_line + ":" + config_sheet["FR_LANGUAGE_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["LENGTH_COLUMN"] + first_line + ":" + config_sheet["LENGTH_COLUMN"])
		ranges.append(worksheet_name + "!" + config_sheet["MISC_COLUMN"] + first_line + ":" + config_sheet["MISC_COLUMN"])
			
		values = self.sheets_client.get_values(ranges)
		
		sheets = values["sheets"]
		
		for sheet in sheets:
			if "data" in sheet:
				data = sheet["data"]
				
				row_id_to_game = {}
				
				# Game column
				for d in data:
					column_id = d.get("startColumn", 0)
					if column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["NAME_COLUMN"]):
						row_id = d.get("startRow", 0)
						
						for r in d["rowData"]:
							if "values" in r and "formattedValue" in r["values"][0]:
								game_name = r["values"][0]["formattedValue"]
								
								model["games"][game_name] = {
									"status": "",
									"tested_version": "",
									"affiliate_link": "",
									"release_date": "",
									"genre": "",
									"developer": "",
									"publisher": "",
									"country": "",
									"nintendo": "",
									"playstation": "",
									"xbox": "",
									"pc": "",
									"price": "",
									"fr_language": "",
									"length": "",
									"misc": "",
								}
								row_id_to_game[row_id] = game_name
								
							row_id += 1
							
						break
						
				for d in data:
					column_id = d.get("startColumn", 0)
					start_row = d.get("startRow", 0)
						
					if column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["STATUS_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "status")
					elif column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["TESTED_VERSION_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "tested_version")
					elif column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["AFFILIATE_LINK_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "affiliate_link")
					elif column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["RELEASE_DATE_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "release_date")
					elif column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["GENRE_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "genre")
					elif column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["DEVELOPER_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "developer")
					elif column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["PUBLISHER_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "publisher")
					elif column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["COUNTRY_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "country")
					elif column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["NINTENDO_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "nintendo")
					elif column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["PLAYSTATION_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "playstation")
					elif column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["XBOX_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "xbox")
					elif column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["PC_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "pc")
					elif column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["PRICE_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "price")
					elif column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["FR_LANGUAGE_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "fr_language")
					elif column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["LENGTH_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "length")
					elif column_id == self.utils.sheet_a1_value_to_column_number(config_sheet["MISC_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, start_row, row_id_to_game, model, "misc")
						
		return model
		
	def load(self):
		if not os.path.isfile(MainFrame.TOKENS_FILENAME):
			tkinter.messagebox.showerror("Error", " File "+ MainFrame.TOKENS_FILENAME +" not found. Please run grant_permissions.bat.")
			sys.exit()
			
		st = time.time()
		self.sheets_client = lib.sheets_client.SheetsClient(self.config["SHEET"]["GDOC_API_KEY"], self.config["SHEET"]["OAUTH_CLIENT_ID"], self.config["SHEET"]["OAUTH_CLIENT_SECRET"], self.config["SHEET"]["SPREAD_SHEET_ID"], MainFrame.TOKENS_FILENAME)
		print(time.time(), "load sheets_client init (ms): ", (time.time() - st) * 1000)
		
		st = time.time()
		self.model = self.build_model()
		print(time.time(), "load build_model (ms): ", (time.time() - st) * 1000)
		
		st = time.time()
		init_values = self.load_context("context.sav")
		print(time.time(), "load load_context (ms): ", (time.time() - st) * 1000)
		
		self.fill_games(init_values)
		st = time.time()
		print(time.time(), "load fill_games (ms): ", (time.time() - st) * 1000)
		
	def reload_sheet(self):
		init_values = {}
		init_values["game"] = self.model["current_game"]
		
		self.model = self.build_model()
		self.fill_games(init_values)
		
	def load_context(self, file_name):
		init_values = {}
		if os.path.exists(file_name):
			config = configparser.ConfigParser()
			config.read(file_name)
			
			if "game" in config["CONTEXT"]:
				init_values["game"] = config["CONTEXT"]["game"].replace("<SPACE>", " ")
				
			if "name_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_name_suffix, config["CONTEXT"]["name_suffix"].replace("<SPACE>", " "))
			if "name_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_name_text_file, config["CONTEXT"]["name_text_file"].replace("<SPACE>", " "))
				
			if "status_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_status_suffix, config["CONTEXT"]["status_suffix"].replace("<SPACE>", " "))
			if "status_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_status_text_file, config["CONTEXT"]["status_text_file"].replace("<SPACE>", " "))
				
			if "tested_version_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_tested_version_suffix, config["CONTEXT"]["tested_version_suffix"].replace("<SPACE>", " "))
			if "tested_version_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_tested_version_text_file, config["CONTEXT"]["tested_version_text_file"].replace("<SPACE>", " "))
				
			if "release_date_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_release_date_suffix, config["CONTEXT"]["release_date_suffix"].replace("<SPACE>", " "))
			if "release_date_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_release_date_text_file, config["CONTEXT"]["release_date_text_file"].replace("<SPACE>", " "))
				
			if "genre_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_genre_suffix, config["CONTEXT"]["genre_suffix"].replace("<SPACE>", " "))
			if "genre_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_genre_text_file, config["CONTEXT"]["genre_text_file"].replace("<SPACE>", " "))
				
			if "developer_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_developer_suffix, config["CONTEXT"]["developer_suffix"].replace("<SPACE>", " "))
			if "developer_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_developer_text_file, config["CONTEXT"]["developer_text_file"].replace("<SPACE>", " "))
				
			if "publisher_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_publisher_suffix, config["CONTEXT"]["publisher_suffix"].replace("<SPACE>", " "))
			if "publisher_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_publisher_text_file, config["CONTEXT"]["publisher_text_file"].replace("<SPACE>", " "))
				
			if "country_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_country_suffix, config["CONTEXT"]["country_suffix"].replace("<SPACE>", " "))
			if "country_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_country_text_file, config["CONTEXT"]["country_text_file"].replace("<SPACE>", " "))
				
			if "platforms_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_platforms_suffix, config["CONTEXT"]["platforms_suffix"].replace("<SPACE>", " "))
			if "platforms_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_platforms_text_file, config["CONTEXT"]["platforms_text_file"].replace("<SPACE>", " "))
				
			if "price_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_price_suffix, config["CONTEXT"]["price_suffix"].replace("<SPACE>", " "))
			if "price_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_price_text_file, config["CONTEXT"]["price_text_file"].replace("<SPACE>", " "))
				
			if "fr_language_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_fr_language_suffix, config["CONTEXT"]["fr_language_suffix"].replace("<SPACE>", " "))
			if "fr_language_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_fr_language_text_file, config["CONTEXT"]["fr_language_text_file"].replace("<SPACE>", " "))
				
			if "length_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_length_suffix, config["CONTEXT"]["length_suffix"].replace("<SPACE>", " "))
			if "length_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_length_text_file, config["CONTEXT"]["length_text_file"].replace("<SPACE>", " "))
				
			if "misc_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_misc_suffix, config["CONTEXT"]["misc_suffix"].replace("<SPACE>", " "))
			if "misc_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_misc_text_file, config["CONTEXT"]["misc_text_file"].replace("<SPACE>", " "))
			
			if "affiliate_link_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_affiliate_link_suffix, config["CONTEXT"]["affiliate_link_suffix"].replace("<SPACE>", " "))
			if "affiliate_link_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_affiliate_link_text_file, config["CONTEXT"]["affiliate_link_text_file"].replace("<SPACE>", " "))
			if "affiliate_link_bot_prefix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_affiliate_link_bot_prefix_text, config["CONTEXT"]["affiliate_link_bot_prefix"].replace("<SPACE>", " "))
			if "affiliate_link_bot_period" in config["CONTEXT"]:
				self.set_entry_text(self.entry_affiliate_link_bot_period_text, config["CONTEXT"]["affiliate_link_bot_period"].replace("<SPACE>", " "))
				
		return init_values
		
	def save_context(self, file_name):
		config = configparser.ConfigParser()
		
		config["CONTEXT"] = {
			"game": self.model["current_game"].replace(" ", "<SPACE>"),
			"name_suffix": self.entry_name_suffix.get().replace(" ", "<SPACE>"),
			"name_text_file": self.entry_name_text_file.get().replace(" ", "<SPACE>"),
			"status_suffix": self.entry_status_suffix.get().replace(" ", "<SPACE>"),
			"status_text_file": self.entry_status_text_file.get().replace(" ", "<SPACE>"),
			"tested_version_suffix": self.entry_tested_version_suffix.get().replace(" ", "<SPACE>"),
			"tested_version_text_file": self.entry_tested_version_text_file.get().replace(" ", "<SPACE>"),
			"release_date_suffix": self.entry_release_date_suffix.get().replace(" ", "<SPACE>"),
			"release_date_text_file": self.entry_release_date_text_file.get().replace(" ", "<SPACE>"),
			"genre_suffix": self.entry_genre_suffix.get().replace(" ", "<SPACE>"),
			"genre_text_file": self.entry_genre_text_file.get().replace(" ", "<SPACE>"),
			"developer_suffix": self.entry_developer_suffix.get().replace(" ", "<SPACE>"),
			"developer_text_file": self.entry_developer_text_file.get().replace(" ", "<SPACE>"),
			"publisher_suffix": self.entry_publisher_suffix.get().replace(" ", "<SPACE>"),
			"publisher_text_file": self.entry_publisher_text_file.get().replace(" ", "<SPACE>"),
			"country_suffix": self.entry_country_suffix.get().replace(" ", "<SPACE>"),
			"country_text_file": self.entry_country_text_file.get().replace(" ", "<SPACE>"),
			"platforms_suffix": self.entry_platforms_suffix.get().replace(" ", "<SPACE>"),
			"platforms_text_file": self.entry_platforms_text_file.get().replace(" ", "<SPACE>"),
			"price_suffix": self.entry_price_suffix.get().replace(" ", "<SPACE>"),
			"price_text_file": self.entry_price_text_file.get().replace(" ", "<SPACE>"),
			"fr_language_suffix": self.entry_fr_language_suffix.get().replace(" ", "<SPACE>"),
			"fr_language_text_file": self.entry_fr_language_text_file.get().replace(" ", "<SPACE>"),
			"length_suffix": self.entry_length_suffix.get().replace(" ", "<SPACE>"),
			"length_text_file": self.entry_length_text_file.get().replace(" ", "<SPACE>"),
			"misc_suffix": self.entry_misc_suffix.get().replace(" ", "<SPACE>"),
			"misc_text_file": self.entry_misc_text_file.get().replace(" ", "<SPACE>"),
			"affiliate_link_suffix": self.entry_affiliate_link_suffix.get().replace(" ", "<SPACE>"),
			"affiliate_link_text_file": self.entry_affiliate_link_text_file.get().replace(" ", "<SPACE>"),
			"affiliate_link_bot_prefix": self.entry_affiliate_link_bot_prefix_text.get().replace(" ", "<SPACE>"),
			"affiliate_link_bot_period": self.entry_affiliate_link_bot_period_text.get().replace(" ", "<SPACE>"),
		}
		
		with open(file_name, "w") as f:
			config.write(f)
		
	def on_close(self):
		self.save_context("context.sav")
		try:
			self.window.destroy()
		except:
			pass
			
def main():
	config = configparser.ConfigParser()
	config.read("config.ini")
	
	bot_thread = BotThread(config)
	bot_thread.start()
	
	window = tkinter.Tk()
	window.title("IndieGameBoy")
	window.resizable(False, False)
	f = MainFrame(config, bot_thread.get_bot(), window)
	window.protocol("WM_DELETE_WINDOW", f.on_close)
	window.after(1, f.load)
	window.mainloop()
	

class Logger(object):
	def __init__(self, filename = "logs.txt"):
		self.terminal = sys.stdout
		self.log = open(filename, "w")
		
	def write(self, message):
		self.terminal.write(message)
		self.log.write(message)
		self.log.flush()
		
	def flush(self):
		self.terminal.flush()
		self.log.flush()
		
if __name__ == "__main__":
	logger = Logger()
	sys.stdout = logger
	sys.stderr = logger
	main()
	