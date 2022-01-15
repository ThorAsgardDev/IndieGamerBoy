
import os
import sys
import traceback
import configparser
import requests
import tkinter
import tkinter.ttk
import tkinter.filedialog
import tkinter.messagebox
import lib.sheets_client
import lib.utils
import time


class MainFrame(tkinter.Frame):
	TOKENS_FILENAME = "tokens.ini"
	
	def __init__(self, window, **kwargs):
		tkinter.Frame.__init__(self, window, **kwargs)
		
		self.window = window
		
		self.model = None
		
		self.config = configparser.ConfigParser()
		self.config.read("config.ini")
		
		self.utils = lib.utils.Utils()
		
		self.pack(expand = tkinter.YES, fill = tkinter.BOTH)
		
		self.create_label(self, "Saisons: ", 0, 0)
		self.combo_seasons = self.create_combo(self, self.on_combo_seasons_changed, 0, 1)
		self.create_label(self, "Jeux: ", 1, 0)
		self.combo_games = self.create_combo(self, self.on_combo_games_changed, 1, 1)
		self.create_label(self, "Suffixe: ", 1, 2)
		self.entry_name_suffix = self.create_entry(self, "", True, 1, 3)
		self.create_label(self, "Status: ", 2, 0)
		self.entry_status = self.create_entry(self, "", False, 2, 1)
		self.create_label(self, "Suffixe: ", 2, 2)
		self.entry_status_suffix = self.create_entry(self, "", True, 2, 3)
		self.create_label(self, "Clé fournie par: ", 3, 0)
		self.entry_key_provider = self.create_entry(self, "", False, 3, 1)
		self.create_label(self, "Suffixe: ", 3, 2)
		self.entry_key_provider_suffix = self.create_entry(self, "", True, 3, 3)
		self.create_label(self, "Genre: ", 4, 0)
		self.entry_genre = self.create_entry(self, "", False, 4, 1)
		self.create_label(self, "Suffixe: ", 4, 2)
		self.entry_genre_suffix = self.create_entry(self, "", True, 4, 3)
		self.create_label(self, "Développeur: ", 5, 0)
		self.entry_developer = self.create_entry(self, "", False, 5, 1)
		self.create_label(self, "Suffixe: ", 5, 2)
		self.entry_developer_suffix = self.create_entry(self, "", True, 5, 3)
		self.create_label(self, "Editeur: ", 6, 0)
		self.entry_publisher = self.create_entry(self, "", False, 6, 1)
		self.create_label(self, "Suffixe: ", 6, 2)
		self.entry_publisher_suffix = self.create_entry(self, "", True, 6, 3)
		self.create_label(self, "Twitter: ", 7, 0)
		self.entry_twitter = self.create_entry(self, "", False, 7, 1)
		self.create_label(self, "Suffixe: ", 7, 2)
		self.entry_twitter_suffix = self.create_entry(self, "", True, 7, 3)
		self.create_label(self, "Pays: ", 8, 0)
		self.entry_country = self.create_entry(self, "", False, 8, 1)
		self.create_label(self, "Suffixe: ", 8, 2)
		self.entry_country_suffix = self.create_entry(self, "", True, 8, 3)
		self.create_label(self, "Année: ", 9, 0)
		self.entry_year = self.create_entry(self, "", False, 9, 1)
		self.create_label(self, "Suffixe: ", 9, 2)
		self.entry_year_suffix = self.create_entry(self, "", True, 9, 3)
		self.create_label(self, "Plateformes: ", 10, 0)
		self.entry_platforms = self.create_entry(self, "", False, 10, 1)
		self.create_label(self, "Suffixe: ", 10, 2)
		self.entry_platforms_suffix = self.create_entry(self, "", True, 10, 3)
		self.create_label(self, "Prix: ", 11, 0)
		self.entry_price = self.create_entry(self, "", False, 11, 1)
		self.create_label(self, "Suffixe: ", 11, 2)
		self.entry_price_suffix = self.create_entry(self, "", True, 11, 3)
		self.create_label(self, "Durée de vie: ", 12, 0)
		self.entry_length = self.create_entry(self, "", False, 12, 1)
		self.create_label(self, "Suffixe: ", 12, 2)
		self.entry_length_suffix = self.create_entry(self, "", True, 12, 3)
		self.create_label(self, "Langue: ", 13, 0)
		self.entry_language = self.create_entry(self, "", False, 13, 1)
		self.create_label(self, "Suffixe: ", 13, 2)
		self.entry_language_suffix = self.create_entry(self, "", True, 13, 3)
		self.create_label(self, "Divers: ", 14, 0)
		self.entry_misc = self.create_entry(self, "", False, 14, 1)
		self.create_label(self, "Suffixe: ", 14, 2)
		self.entry_misc_suffix = self.create_entry(self, "", True, 14, 3)
		
		self.create_button(self, "Recharger Gdoc", self.on_reload_sheet_click, 15, 0, 4)
		self.create_button(self, "Envoyer vers les fichiers textes", self.on_send_to_text_click, 16, 0, 4)
		
	def create_label(self, frame, text, row, column):
		label = tkinter.Label(frame, text = text, anchor = tkinter.W)
		label.grid(sticky=tkinter.W, padx=2, pady=2, row=row, column=column)
		return label
		
	def create_combo(self, frame, on_changed_cb, row, column):
		combo = tkinter.ttk.Combobox(frame, state = "readonly")
		combo.grid(sticky=tkinter.W, padx=2, pady=2, row=row, column=column)
		combo.bind("<<ComboboxSelected>>", on_changed_cb)
		return combo
		
	def create_entry(self, frame, text, enabled, row, column):
		if enabled:
			entry = tkinter.Entry(frame)
		else:
			entry = tkinter.Entry(frame, state="readonly")
		entry.grid(sticky=tkinter.W, padx=2, pady=2, row=row, column=column)
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
		
	def on_send_to_text_click(self):
		self.utils.write_file("w", "text-files/name.txt", self.combo_games.cget("values")[self.combo_games.current()] + self.entry_name_suffix.get())
		self.utils.write_file("w", "text-files/status.txt", self.entry_status.get() + self.entry_status_suffix.get())
		self.utils.write_file("w", "text-files/key-provider.txt", self.entry_key_provider.get() + self.entry_key_provider_suffix.get())
		self.utils.write_file("w", "text-files/genre.txt", self.entry_genre.get() + self.entry_genre_suffix.get())
		self.utils.write_file("w", "text-files/developer.txt", self.entry_developer.get() + self.entry_developer_suffix.get())
		self.utils.write_file("w", "text-files/publisher.txt", self.entry_publisher.get() + self.entry_publisher_suffix.get())
		self.utils.write_file("w", "text-files/twitter.txt", self.entry_twitter.get() + self.entry_twitter_suffix.get())
		self.utils.write_file("w", "text-files/country.txt", self.entry_country.get() + self.entry_country_suffix.get())
		self.utils.write_file("w", "text-files/year.txt", self.entry_year.get() + self.entry_year_suffix.get())
		self.utils.write_file("w", "text-files/platforms.txt", self.entry_platforms.get() + self.entry_platforms_suffix.get())
		self.utils.write_file("w", "text-files/price.txt", self.entry_price.get() + self.entry_price_suffix.get())
		self.utils.write_file("w", "text-files/length.txt", self.entry_length.get() + self.entry_length_suffix.get())
		self.utils.write_file("w", "text-files/language.txt", self.entry_language.get() + self.entry_language_suffix.get())
		self.utils.write_file("w", "text-files/misc.txt", self.entry_misc.get() + self.entry_misc_suffix.get())
		
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
			
			self.set_entry_text(self.entry_status, model_games[current_game_index]["status"])
			self.set_entry_text(self.entry_key_provider, model_games[current_game_index]["key_provider"])
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
			ranges.append(season + "!" + config_sheet["KEY_PROVIDER_COLUMN"] + first_line + ":" + config_sheet["KEY_PROVIDER_COLUMN"])
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
							"key_provider": "",
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
					elif column == self.utils.sheet_a1_value_to_column_number(config_sheet["KEY_PROVIDER_COLUMN"]):
						self.set_sheet_data_simple_values_to_model(d, model["seasons"][season]["games"], game_start_row, "key_provider")
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
				
			if "status_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_status_suffix, config["CONTEXT"]["status_suffix"].replace("<SPACE>", " "))
				
			if "key_provider_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_key_provider_suffix, config["CONTEXT"]["key_provider_suffix"].replace("<SPACE>", " "))
				
			if "genre_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_genre_suffix, config["CONTEXT"]["genre_suffix"].replace("<SPACE>", " "))
				
			if "developer_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_developer_suffix, config["CONTEXT"]["developer_suffix"].replace("<SPACE>", " "))
				
			if "publisher_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_publisher_suffix, config["CONTEXT"]["publisher_suffix"].replace("<SPACE>", " "))
				
			if "twitter_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_twitter_suffix, config["CONTEXT"]["twitter_suffix"].replace("<SPACE>", " "))
				
			if "country_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_country_suffix, config["CONTEXT"]["country_suffix"].replace("<SPACE>", " "))
				
			if "year_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_year_suffix, config["CONTEXT"]["year_suffix"].replace("<SPACE>", " "))
				
			if "platforms_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_platforms_suffix, config["CONTEXT"]["platforms_suffix"].replace("<SPACE>", " "))
				
			if "price_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_price_suffix, config["CONTEXT"]["price_suffix"].replace("<SPACE>", " "))
				
			if "length_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_length_suffix, config["CONTEXT"]["length_suffix"].replace("<SPACE>", " "))
				
			if "language_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_language_suffix, config["CONTEXT"]["language_suffix"].replace("<SPACE>", " "))
				
			if "misc_suffix" in config["CONTEXT"]:
				self.set_entry_text(self.entry_misc_suffix, config["CONTEXT"]["misc_suffix"].replace("<SPACE>", " "))
				
		return init_values
		
	def save_context(self, file_name):
		config = configparser.ConfigParser()
		
		config["CONTEXT"] = {
			"season": self.model["current_season"].replace(" ", "<SPACE>"),
			"game": self.model["current_game"].replace(" ", "<SPACE>"),
			"name_suffix": self.entry_name_suffix.get().replace(" ", "<SPACE>"),
			"status_suffix": self.entry_status_suffix.get().replace(" ", "<SPACE>"),
			"key_provider_suffix": self.entry_key_provider_suffix.get().replace(" ", "<SPACE>"),
			"genre_suffix": self.entry_genre_suffix.get().replace(" ", "<SPACE>"),
			"developer_suffix": self.entry_developer_suffix.get().replace(" ", "<SPACE>"),
			"publisher_suffix": self.entry_publisher_suffix.get().replace(" ", "<SPACE>"),
			"twitter_suffix": self.entry_twitter_suffix.get().replace(" ", "<SPACE>"),
			"country_suffix": self.entry_country_suffix.get().replace(" ", "<SPACE>"),
			"year_suffix": self.entry_year_suffix.get().replace(" ", "<SPACE>"),
			"platforms_suffix": self.entry_platforms_suffix.get().replace(" ", "<SPACE>"),
			"price_suffix": self.entry_price_suffix.get().replace(" ", "<SPACE>"),
			"length_suffix": self.entry_length_suffix.get().replace(" ", "<SPACE>"),
			"language_suffix": self.entry_language_suffix.get().replace(" ", "<SPACE>"),
			"misc_suffix": self.entry_misc_suffix.get().replace(" ", "<SPACE>"),
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
	window = tkinter.Tk()
	window.title("IndieGameBoy")
	window.resizable(False, False)
	f = MainFrame(window)
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
	