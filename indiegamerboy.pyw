
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
		
		self.create_label(self, "Saisons: ", 0, 0)
		self.combo_seasons = self.create_combo(self, self.on_combo_seasons_changed, 0, 1)
		self.create_label(self, "Jeux: ", 1, 0)
		self.combo_games = self.create_combo(self, self.on_combo_games_changed, 1, 1)
		self.create_label(self, "Suffixe: ", 1, 2)
		self.entry_name_suffix = self.create_entry(self, "", True, 1, 3)
		self.create_label(self, "Fichier texte: ", 1, 4)
		self.entry_name_text_file = self.create_entry(self, "name.txt", True, 1, 5, 2)
		
		self.entry_status, self.entry_status_suffix, self.entry_status_text_file = self.create_line_controls(2, "Status: ", "status.txt")
		self.entry_tested_version, self.entry_tested_version_suffix, self.entry_tested_version_text_file = self.create_line_controls(3, "Version testée: ", "tested-version.txt")
		self.entry_genre, self.entry_genre_suffix, self.entry_genre_text_file = self.create_line_controls(4, "Genre: ", "genre.txt")
		self.entry_developer, self.entry_developer_suffix, self.entry_developer_text_file = self.create_line_controls(5, "Développeur: ", "developer.txt")
		self.entry_publisher, self.entry_publisher_suffix, self.entry_publisher_text_file = self.create_line_controls(6, "Editeur: ", "publisher.txt")
		self.entry_twitter, self.entry_twitter_suffix, self.entry_twitter_text_file = self.create_line_controls(7, "Twitter: ", "twitter.txt")
		self.entry_country, self.entry_country_suffix, self.entry_country_text_file = self.create_line_controls(8, "Pays: ", "country.txt")
		self.entry_year, self.entry_year_suffix, self.entry_year_text_file = self.create_line_controls(9, "Année: ", "year.txt")
		self.entry_platforms, self.entry_platforms_suffix, self.entry_platforms_text_file = self.create_line_controls(10, "Plateformes: ", "platforms.txt")
		self.entry_price, self.entry_price_suffix, self.entry_price_text_file = self.create_line_controls(11, "Prix: ", "price.txt")
		self.entry_length, self.entry_length_suffix, self.entry_length_text_file = self.create_line_controls(12, "Durée de vie: ", "length.txt")
		self.entry_language, self.entry_language_suffix, self.entry_language_text_file = self.create_line_controls(13, "Langue: ", "language.txt")
		self.entry_misc, self.entry_misc_suffix, self.entry_misc_text_file = self.create_line_controls(14, "Divers: ", "misc.txt")
		self.entry_affiliate_link, self.entry_affiliate_link_suffix, self.entry_affiliate_link_text_file = self.create_line_controls(15, "Lien d'affiliation: ", "affiliate-link.txt")
		self.entry_affiliate_link_bot_button, self.entry_affiliate_link_bot_prefix_text, self.entry_affiliate_link_bot_period_text = self.add_bot_line_controls(16, self.on_bot_affiliate_link_click)
		
		self.create_button(self, "Recharger Gdoc", self.on_reload_sheet_click, 17, 0, 7)
		self.create_button(self, "Envoyer vers les fichiers textes", self.on_send_to_text_click, 18, 0, 7)
		
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
		text_file_to_text[self.entry_genre_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_genre_text_file.get(), []), self.entry_genre.get(), self.entry_genre_suffix.get())
		text_file_to_text[self.entry_developer_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_developer_text_file.get(), []), self.entry_developer.get(), self.entry_developer_suffix.get())
		text_file_to_text[self.entry_publisher_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_publisher_text_file.get(), []), self.entry_publisher.get(), self.entry_publisher_suffix.get())
		text_file_to_text[self.entry_twitter_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_twitter_text_file.get(), []), self.entry_twitter.get(), self.entry_twitter_suffix.get())
		text_file_to_text[self.entry_country_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_country_text_file.get(), []), self.entry_country.get(), self.entry_country_suffix.get())
		text_file_to_text[self.entry_year_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_year_text_file.get(), []), self.entry_year.get(), self.entry_year_suffix.get())
		text_file_to_text[self.entry_platforms_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_platforms_text_file.get(), []), self.entry_platforms.get(), self.entry_platforms_suffix.get())
		text_file_to_text[self.entry_price_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_price_text_file.get(), []), self.entry_price.get(), self.entry_price_suffix.get())
		text_file_to_text[self.entry_length_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_length_text_file.get(), []), self.entry_length.get(), self.entry_length_suffix.get())
		text_file_to_text[self.entry_language_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_language_text_file.get(), []), self.entry_language.get(), self.entry_language_suffix.get())
		text_file_to_text[self.entry_misc_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_misc_text_file.get(), []), self.entry_misc.get(), self.entry_misc_suffix.get())
		text_file_to_text[self.entry_affiliate_link_text_file.get()] = self.append_text_to_list(text_file_to_text.get(self.entry_affiliate_link_text_file.get(), []), self.entry_affiliate_link.get(), self.entry_affiliate_link_suffix.get())
		
		for k, v in text_file_to_text.items():
			if k != "":
				self.utils.write_file("wb", "text-files/" + k, "".join(v))
		
	def on_combo_seasons_changed(self, event):
		self.process_on_combo_seasons_changed(None)
		
	def fill_seasons(self, init_values):
		values = []
		
		for value in self.model["seasons"]:
			values.append(value)
			
		values.sort()
			
		self.combo_seasons.config(values = values)
		if len(values) > 0:
			self.combo_seasons.current(0)
		
		if init_values and ("season" in init_values):
			self.select_combo_value(self.combo_seasons, init_values["season"])
			
		self.process_on_combo_seasons_changed(init_values)
		
	def process_on_combo_seasons_changed(self, init_values):
		current_season = self.get_combo_value(self.combo_seasons)
		if current_season != self.model["current_season"]:
			self.model["current_season"] = current_season
			self.fill_games(init_values)
			
	def on_combo_games_changed(self, event):
		self.process_on_combo_games_changed(None)
		
	def fill_games(self, init_values):
		values = []
		
		for value in self.model["seasons"][self.model["current_season"]]["games"]:
			values.append(value["name"])
		
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
			current_game_index = self.combo_games.current()
			self.model["current_game_index"] = current_game_index
			model_games = self.model["seasons"][self.model["current_season"]]["games"]
			
			self.stop_bot_affiliate_link()
			
			self.set_entry_text(self.entry_status, model_games[current_game_index]["status"])
			self.set_entry_text(self.entry_tested_version, model_games[current_game_index]["tested_version"])
			self.set_entry_text(self.entry_genre, model_games[current_game_index]["genre"])
			self.set_entry_text(self.entry_developer, model_games[current_game_index]["developer"])
			self.set_entry_text(self.entry_publisher, model_games[current_game_index]["publisher"])
			self.set_entry_text(self.entry_twitter, model_games[current_game_index]["twitter"])
			self.set_entry_text(self.entry_country, model_games[current_game_index]["country"])
			self.set_entry_text(self.entry_year, model_games[current_game_index]["year"])
			self.set_entry_text(self.entry_platforms, self.build_platform_label(model_games[current_game_index]))
			self.set_entry_text(self.entry_price, model_games[current_game_index]["price"])
			self.set_entry_text(self.entry_length, model_games[current_game_index]["length"])
			self.set_entry_text(self.entry_language, model_games[current_game_index]["language"])
			self.set_entry_text(self.entry_misc, model_games[current_game_index]["misc"])
			self.set_entry_text(self.entry_affiliate_link, model_games[current_game_index]["affiliate_link"])
			
			self.on_send_to_text_click()
			
	def build_platform_label(self, model_game):
		l = []
		if model_game["switch"] == "TRUE":
			l.append("Switch")
		if model_game["ps4"] == "TRUE":
			l.append("PS4")
		if model_game["ps5"] == "TRUE":
			l.append("PS5")
		if model_game["xbox_one"] == "TRUE":
			l.append("Xbox One")
		if model_game["xbox_series"] == "TRUE":
			l.append("Xbox Series")
		if model_game["pc"] == "TRUE":
			l.append("PC")
		return "/".join(l)
			
	def set_sheet_data_simple_values_to_model(self, data, model_games, game_start_row, field_name):
		id = data["startRow"] - game_start_row
		
		if "rowData" not in data:
			return
			
		for row_data in data["rowData"]:
			if id >= 0 and id < len(model_games):
				if "values" in row_data and "formattedValue" in row_data["values"][0]:
					model_games[id][field_name] = row_data["values"][0]["formattedValue"].strip()
			id += 1
			
	def build_model(self):
		model = {
			"seasons": {},
			"current_season": "",
			"current_game": "",
			"current_game_index": -1,
		}
		
		config_sheet = self.config["SHEET"]
		
		response = self.sheets_client.get_sheets()
		
		if response["sheets"]:
			for sheet in response["sheets"]:
				if sheet["properties"] and "Saison" in sheet["properties"]["title"]:
					model["seasons"][sheet["properties"]["title"]] = {
						"games": [],
					}
					
		first_line = config_sheet["FIRST_GAME_LINE"]
		
		ranges = []
		
		for season in model["seasons"]:
			ranges.append(season + "!" + config_sheet["NAME_COLUMN"] + first_line + ":" + config_sheet["NAME_COLUMN"])
			ranges.append(season + "!" + config_sheet["STATUS_COLUMN"] + first_line + ":" + config_sheet["STATUS_COLUMN"])
			ranges.append(season + "!" + config_sheet["TESTED_VERSION_COLUMN"] + first_line + ":" + config_sheet["TESTED_VERSION_COLUMN"])
			ranges.append(season + "!" + config_sheet["GENRE_COLUMN"] + first_line + ":" + config_sheet["GENRE_COLUMN"])
			ranges.append(season + "!" + config_sheet["DEVELOPER_COLUMN"] + first_line + ":" + config_sheet["DEVELOPER_COLUMN"])
			ranges.append(season + "!" + config_sheet["PUBLISHER_COLUMN"] + first_line + ":" + config_sheet["PUBLISHER_COLUMN"])
			ranges.append(season + "!" + config_sheet["TWITTER_COLUMN"] + first_line + ":" + config_sheet["TWITTER_COLUMN"])
			ranges.append(season + "!" + config_sheet["COUNTRY_COLUMN"] + first_line + ":" + config_sheet["COUNTRY_COLUMN"])
			ranges.append(season + "!" + config_sheet["YEAR_COLUMN"] + first_line + ":" + config_sheet["YEAR_COLUMN"])
			ranges.append(season + "!" + config_sheet["SWITCH_COLUMN"] + first_line + ":" + config_sheet["SWITCH_COLUMN"])
			ranges.append(season + "!" + config_sheet["PS4_COLUMN"] + first_line + ":" + config_sheet["PS4_COLUMN"])
			ranges.append(season + "!" + config_sheet["PS5_COLUMN"] + first_line + ":" + config_sheet["PS5_COLUMN"])
			ranges.append(season + "!" + config_sheet["XBOX_ONE_COLUMN"] + first_line + ":" + config_sheet["XBOX_ONE_COLUMN"])
			ranges.append(season + "!" + config_sheet["XBOX_SERIES_COLUMN"] + first_line + ":" + config_sheet["XBOX_SERIES_COLUMN"])
			ranges.append(season + "!" + config_sheet["PC_COLUMN"] + first_line + ":" + config_sheet["PC_COLUMN"])
			ranges.append(season + "!" + config_sheet["PRICE_COLUMN"] + first_line + ":" + config_sheet["PRICE_COLUMN"])
			ranges.append(season + "!" + config_sheet["LENGTH_COLUMN"] + first_line + ":" + config_sheet["LENGTH_COLUMN"])
			ranges.append(season + "!" + config_sheet["LANGUAGE_COLUMN"] + first_line + ":" + config_sheet["LANGUAGE_COLUMN"])
			ranges.append(season + "!" + config_sheet["MISC_COLUMN"] + first_line + ":" + config_sheet["MISC_COLUMN"])
			ranges.append(season + "!" + config_sheet["AFFILIATE_LINK_COLUMN"] + first_line + ":" + config_sheet["AFFILIATE_LINK_COLUMN"])
			
		values = self.sheets_client.get_values(ranges)
		
		sheets = values["sheets"]
		
		for sheet in sheets:
			season = sheet["properties"]["title"]
			
			if "data" in sheet:
				data = sheet["data"]
				
				# Find game column
				game_data = None
				game_start_row = None
				for d in data:
					if "startColumn" in d \
					and d["startColumn"] == self.utils.sheet_a1_value_to_column_number(config_sheet["NAME_COLUMN"]):
						game_data = d
						game_start_row = d["startRow"]
						break
						
				for r in game_data["rowData"]:
					if "values" in r \
					and "formattedValue" in r["values"][0]:
						model["seasons"][season]["games"].append({
							"name": r["values"][0]["formattedValue"],
							"status": "",
							"tested_version": "",
							"genre": "",
							"developer": "",
							"publisher": "",
							"twitter": "",
							"country": "",
							"year": "",
							"switch": "",
							"ps4": "",
							"ps5": "",
							"xbox_one": "",
							"xbox_series": "",
							"pc": "",
							"price": "",
							"length": "",
							"language": "",
							"misc": "",
							"affiliate_link": "",
						})
						
				for d in data:
					if "startColumn" in d:
						column = d["startColumn"]
					else:
						column = 0
						
					if "startRow" in d:
						row = d["startRow"]
					else:
						row = 0
						
					if column == self.utils.sheet_a1_value_to_column_number(config_sheet["STATUS_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, model["seasons"][season]["games"], game_start_row, "status")
					elif column == self.utils.sheet_a1_value_to_column_number(config_sheet["TESTED_VERSION_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, model["seasons"][season]["games"], game_start_row, "tested_version")
					elif column == self.utils.sheet_a1_value_to_column_number(config_sheet["GENRE_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, model["seasons"][season]["games"], game_start_row, "genre")
					elif column == self.utils.sheet_a1_value_to_column_number(config_sheet["DEVELOPER_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, model["seasons"][season]["games"], game_start_row, "developer")
					elif column == self.utils.sheet_a1_value_to_column_number(config_sheet["PUBLISHER_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, model["seasons"][season]["games"], game_start_row, "publisher")
					elif column == self.utils.sheet_a1_value_to_column_number(config_sheet["TWITTER_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, model["seasons"][season]["games"], game_start_row, "twitter")
					elif column == self.utils.sheet_a1_value_to_column_number(config_sheet["COUNTRY_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, model["seasons"][season]["games"], game_start_row, "country")
					elif column == self.utils.sheet_a1_value_to_column_number(config_sheet["YEAR_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, model["seasons"][season]["games"], game_start_row, "year")
					elif column == self.utils.sheet_a1_value_to_column_number(config_sheet["SWITCH_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, model["seasons"][season]["games"], game_start_row, "switch")
					elif column == self.utils.sheet_a1_value_to_column_number(config_sheet["PS4_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, model["seasons"][season]["games"], game_start_row, "ps4")
					elif column == self.utils.sheet_a1_value_to_column_number(config_sheet["PS5_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, model["seasons"][season]["games"], game_start_row, "ps5")
					elif column == self.utils.sheet_a1_value_to_column_number(config_sheet["XBOX_ONE_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, model["seasons"][season]["games"], game_start_row, "xbox_one")
					elif column == self.utils.sheet_a1_value_to_column_number(config_sheet["XBOX_SERIES_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, model["seasons"][season]["games"], game_start_row, "xbox_series")
					elif column == self.utils.sheet_a1_value_to_column_number(config_sheet["PC_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, model["seasons"][season]["games"], game_start_row, "pc")
					elif column == self.utils.sheet_a1_value_to_column_number(config_sheet["PRICE_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, model["seasons"][season]["games"], game_start_row, "price")
					elif column == self.utils.sheet_a1_value_to_column_number(config_sheet["LENGTH_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, model["seasons"][season]["games"], game_start_row, "length")
					elif column == self.utils.sheet_a1_value_to_column_number(config_sheet["LANGUAGE_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, model["seasons"][season]["games"], game_start_row, "language")
					elif column == self.utils.sheet_a1_value_to_column_number(config_sheet["MISC_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, model["seasons"][season]["games"], game_start_row, "misc")
					elif column == self.utils.sheet_a1_value_to_column_number(config_sheet["AFFILIATE_LINK_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, model["seasons"][season]["games"], game_start_row, "affiliate_link")
						
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
		
		self.fill_seasons(init_values)
		st = time.time()
		print(time.time(), "load fill_seasons (ms): ", (time.time() - st) * 1000)
		
	def reload_sheet(self):
		init_values = {}
		init_values["season"] = self.model["current_season"]
		init_values["game"] = self.model["current_game"]
		
		self.model = self.build_model()
		self.fill_seasons(init_values)
		
	def load_context(self, file_name):
		init_values = {}
		if os.path.exists(file_name):
			config = configparser.ConfigParser()
			config.read(file_name)
			
			if "season" in config["CONTEXT"]:
				init_values["season"] = config["CONTEXT"]["season"].replace("<SPACE>", " ")
				
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
				
			if "twitter_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_twitter_suffix, config["CONTEXT"]["twitter_suffix"].replace("<SPACE>", " "))
			if "twitter_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_twitter_text_file, config["CONTEXT"]["twitter_text_file"].replace("<SPACE>", " "))
				
			if "country_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_country_suffix, config["CONTEXT"]["country_suffix"].replace("<SPACE>", " "))
			if "country_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_country_text_file, config["CONTEXT"]["country_text_file"].replace("<SPACE>", " "))
				
			if "year_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_year_suffix, config["CONTEXT"]["year_suffix"].replace("<SPACE>", " "))
			if "year_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_year_text_file, config["CONTEXT"]["year_text_file"].replace("<SPACE>", " "))
				
			if "platforms_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_platforms_suffix, config["CONTEXT"]["platforms_suffix"].replace("<SPACE>", " "))
			if "platforms_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_platforms_text_file, config["CONTEXT"]["platforms_text_file"].replace("<SPACE>", " "))
				
			if "price_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_price_suffix, config["CONTEXT"]["price_suffix"].replace("<SPACE>", " "))
			if "price_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_price_text_file, config["CONTEXT"]["price_text_file"].replace("<SPACE>", " "))
				
			if "length_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_length_suffix, config["CONTEXT"]["length_suffix"].replace("<SPACE>", " "))
			if "length_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_length_text_file, config["CONTEXT"]["length_text_file"].replace("<SPACE>", " "))
				
			if "language_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_language_suffix, config["CONTEXT"]["language_suffix"].replace("<SPACE>", " "))
			if "language_text_file" in config["CONTEXT"]:
				self.set_entry_text(self.entry_language_text_file, config["CONTEXT"]["language_text_file"].replace("<SPACE>", " "))
				
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
			"season": self.model["current_season"].replace(" ", "<SPACE>"),
			"game": self.model["current_game"].replace(" ", "<SPACE>"),
			"name_suffix": self.entry_name_suffix.get().replace(" ", "<SPACE>"),
			"name_text_file": self.entry_name_text_file.get().replace(" ", "<SPACE>"),
			"status_suffix": self.entry_status_suffix.get().replace(" ", "<SPACE>"),
			"status_text_file": self.entry_status_text_file.get().replace(" ", "<SPACE>"),
			"tested_version_suffix": self.entry_tested_version_suffix.get().replace(" ", "<SPACE>"),
			"tested_version_text_file": self.entry_tested_version_text_file.get().replace(" ", "<SPACE>"),
			"genre_suffix": self.entry_genre_suffix.get().replace(" ", "<SPACE>"),
			"genre_text_file": self.entry_genre_text_file.get().replace(" ", "<SPACE>"),
			"developer_suffix": self.entry_developer_suffix.get().replace(" ", "<SPACE>"),
			"developer_text_file": self.entry_developer_text_file.get().replace(" ", "<SPACE>"),
			"publisher_suffix": self.entry_publisher_suffix.get().replace(" ", "<SPACE>"),
			"publisher_text_file": self.entry_publisher_text_file.get().replace(" ", "<SPACE>"),
			"twitter_suffix": self.entry_twitter_suffix.get().replace(" ", "<SPACE>"),
			"twitter_text_file": self.entry_twitter_text_file.get().replace(" ", "<SPACE>"),
			"country_suffix": self.entry_country_suffix.get().replace(" ", "<SPACE>"),
			"country_text_file": self.entry_country_text_file.get().replace(" ", "<SPACE>"),
			"year_suffix": self.entry_year_suffix.get().replace(" ", "<SPACE>"),
			"year_text_file": self.entry_year_text_file.get().replace(" ", "<SPACE>"),
			"platforms_suffix": self.entry_platforms_suffix.get().replace(" ", "<SPACE>"),
			"platforms_text_file": self.entry_platforms_text_file.get().replace(" ", "<SPACE>"),
			"price_suffix": self.entry_price_suffix.get().replace(" ", "<SPACE>"),
			"price_text_file": self.entry_price_text_file.get().replace(" ", "<SPACE>"),
			"length_suffix": self.entry_length_suffix.get().replace(" ", "<SPACE>"),
			"length_text_file": self.entry_length_text_file.get().replace(" ", "<SPACE>"),
			"language_suffix": self.entry_language_suffix.get().replace(" ", "<SPACE>"),
			"language_text_file": self.entry_language_text_file.get().replace(" ", "<SPACE>"),
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
	