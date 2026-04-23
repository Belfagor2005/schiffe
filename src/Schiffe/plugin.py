#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===============================================================================
# Battleship Plugin by DarkVolli 2011
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
# Adapted from Lululla for Py3 Enigma2 20220713 - SKIN by MMark
# Revised for PEP8, Python3, and added helper text 2026
# ===============================================================================

from Screens.Screen import Screen
from Components.Sources.CanvasSource import CanvasSource
from Components.Button import Button
from Components.Label import Label
from Components.ActionMap import ActionMap
from Tools.Directories import fileExists, resolveFilename, SCOPE_CURRENT_PLUGIN, SCOPE_CURRENT_SKIN
from enigma import eTimer, gFont, getDesktop, RT_HALIGN_CENTER, RT_VALIGN_CENTER
from xml.etree import ElementTree
from random import randint

from . import _, __version__

SAVE_FILE = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/Schiffe/schiffe.sav")

X_MAX = 10
Y_MAX = 10
XY_MAX = 100


def rgb(r, g, b):
	"""Convert RGB components to a 24-bit integer color."""
	return (r << 16) | (g << 8) | b


def get_desktop_size():
	"""Return (width, height) of the current desktop."""
	s = getDesktop(0).size()
	return s.width(), s.height()


def is_fhd():
	"""Return True if the screen resolution is at least 1920x1080."""
	return get_desktop_size()[0] >= 1920


def main(session, **kwargs):
	session.open(Schiffe)


def Plugins(**kwargs):
	from Plugins.Plugin import PluginDescriptor
	return [PluginDescriptor(
		name="Battleship",
		description=_("Battleship Game"),
		where=[PluginDescriptor.WHERE_PLUGINMENU],
		icon="schiffe.png",
		fnc=main
	)]


class GameCell:
	"""A single cell in the game grid."""

	def __init__(self, canvas, x, y, w, h):
		self.canvas = canvas
		self.x = x
		self.y = y
		self.w = w
		self.h = h
		self._value = 0
		self._focus = False
		self._hide = False

	def set_value(self, v):
		self._value = v

	def value(self):
		return self._value

	def set_focus(self, f):
		self._focus = f

	def focus(self):
		return self._focus

	def set_hide(self, f):
		self._hide = f

	def paint(self):
		fg = rgb(255, 255, 255)		  # foreground
		blue = rgb(0, 0, 255)		  # water background
		focus = rgb(192, 192, 0)	  # focus border
		green = rgb(0, 255, 0)		  # ship (unhit)
		red = rgb(255, 0, 0)		  # ship hit

		if self._value == 0:
			bg = blue
		elif self._value == 1:
			bg = blue
		elif self._value == 2:
			bg = blue
		elif self._value == 3:
			bg = green if not self._hide else blue
		elif self._value == 4:
			bg = red

		border = 0
		if self._focus:
			border = 2
			self.canvas.fill(self.x, self.y, self.w, self.h, focus)

		self.canvas.fill(self.x + border, self.y + border,
						 self.w - 2 * border, self.h - 2 * border, bg)

		if self._value == 2:
			font_size = 30 if is_fhd() else 24
			self.canvas.writeText(
				self.x, self.y, self.w, self.h, fg, bg,
				gFont("Regular", font_size), '*',
				RT_HALIGN_CENTER | RT_VALIGN_CENTER
			)

		self.canvas.flush()


class Schiffe(Screen):
	"""Main Battleship game screen."""

	def __init__(self, session):
		desk = getDesktop(0)
		wdesktop = int(desk.size().width())
		# cell size depends on framebuffer resolution
		if wdesktop == 720:
			cell_size = 20
		elif wdesktop == 1024:
			cell_size = 30
		elif wdesktop == 1280:
			cell_size = 40
		else:
			cell_size = 50

		cell_offset = 2
		cell_field = X_MAX * cell_size + (X_MAX - 1) * cell_offset
		canvas_w = 2 * cell_field + 150
		canvas_h = cell_field
		x0_offset = 0
		x1_offset = cell_field + 150
		window_w = canvas_w + 10
		window_h = canvas_h + 40
		wx = cell_field + 10
		w0y = 25
		w1y = cell_field - 116
		w2y = cell_field - 66
		w3y = cell_field - 16
		self.skin = """
			<screen name="Schiffe" position="center,center" size="1280,720" title="Battleship" backgroundColor="#101010" flags="wfNoBorder">
				<!-- Sfondo (usa un colore se l'immagine non c'è) -->
				<ePixmap position="0,0" size="1280,720" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Schiffe/pic/Schiffehd.jpg" scale="1" zPosition="0" />

				<!-- Widget informativo in alto a sinistra, su più righe -->
				<widget name="info" position="25,10" size="400,50" font="Regular;24" halign="left" valign="center" foregroundColor="#ffff00" backgroundColor="#000000" transparent="1" zPosition="2" />

				<!-- Messaggio di stato (vittoria/sconfitta/aiuto) -->
				<widget name="message" position="21,123" size="230,350" font="Regular;22" halign="left" valign="top" foregroundColor="#ffffff" backgroundColor="#000000" transparent="1" zPosition="2" />

				<!-- Canvas delle griglie (larghezza 1000, sufficiente per 986px) -->
				<widget source="Canvas" render="Canvas" position="265,100" size="1000,450" backgroundColor="#60ffffff" transparent="1" alphatest="blend" zPosition="2" />

				<!-- Nave decorativa tra le griglie (posizione approssimativa) -->
				<ePixmap position="700,140" size="100,300" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Schiffe/pic/ship.jpg" scale="1" zPosition="5" />

				<!-- Pannello statistiche (colpi e tempo) in alto a destra -->
				<ePixmap position="16,492" size="48,48" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Schiffe/pic/rocket.png" scale="1" alphatest="blend" zPosition="2" />
				<widget name="result" position="73,485" size="100,30" font="Regular;22" halign="left" foregroundColor="#ffff00" backgroundColor="#000000" transparent="1" zPosition="3" />
				<widget name="movex" position="75,520" size="100,30" font="Regular;22" halign="left" foregroundColor="#ffff00" backgroundColor="#000000" transparent="1" zPosition="3" />

				<!-- Pulsanti in basso a sinistra, ben separati -->
				<ePixmap position="20,585" pixmap="skin_default/buttons/green.png" size="80,40" alphatest="blend" zPosition="2" />
				<widget name="key_green" font="Regular;24" position="110,585" size="200,40" halign="left" valign="center" backgroundColor="#000000" transparent="1" foregroundColor="#ffffff" zPosition="1" />

				<ePixmap position="20,630" pixmap="skin_default/buttons/red.png" size="80,40" alphatest="blend" zPosition="2" />
				<widget name="key_red" font="Regular;24" position="110,630" size="200,40" halign="left" valign="center" backgroundColor="#000000" transparent="1" foregroundColor="#ffffff" zPosition="1" />

				<ePixmap position="20,675" pixmap="skin_default/buttons/blue.png" size="80,40" alphatest="blend" zPosition="2" />
				<widget name="key_blue" font="Regular;24" position="110,675" size="200,40" halign="left" valign="center" backgroundColor="#000000" transparent="1" foregroundColor="#ffffff" zPosition="1" />
			</screen>"""
		# Skin definition (HD)
		# self.skin = f"""
			# <screen position="center,center" size="{window_w},{window_h}" title="Schiffe v.{__version__}" >
				# <widget source="Canvas" render="Canvas" position="5,20" size="{canvas_w},{canvas_h}" />
				# <widget name="info" position="45,34" size="435,76" valign="center" halign="center" font="Regular; 34" foregroundColor="yellow" backgroundColor="#000000" transparent="1" zPosition="1" />
				# <widget name="message" position="{wx},{w0y}" size="140,40" valign="center" halign="center" font="Regular;21"/>
				# <ePixmap name="green"	   position="{wx},{w1y}"   zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				# <ePixmap name="blue" position="{wx},{w2y}" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
				# <ePixmap name="red"	position="{wx},{w3y}" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				# <widget name="key_green"	  position="{wx},{w1y}"	  zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				# <widget name="key_blue" position="{wx},{w2y}" zPosition="5" size="140,40" valign="center" halign="center"	 font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				# <widget name="key_red"   position="{wx},{w3y}" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			# </screen>"""

		if is_fhd():
			self.skin = """
				<screen name="Schiffe" position="center,center" size="1800,900" title="Schiffe" backgroundColor="#101010" flags="wfNoBorder">
					<ePixmap position="0,0" size="1800,900" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Schiffe/pic/Schiffe.jpg" scale="1" />
					<ePixmap position="1050,170" size="130,400" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Schiffe/pic/ship.jpg" scale="1" zPosition="5" />
					<widget name="info" position="30,19" size="435,76" valign="center" halign="center" font="Regular; 34" foregroundColor="yellow" backgroundColor="#000000" transparent="1" zPosition="1" />
					<widget name="message" position="40,430" size="453,430" valign="center" halign="center" font="Regular; 34" foregroundColor="yellow" backgroundColor="#000000" transparent="1" zPosition="1" />
					<widget source="Canvas" render="Canvas" position="520,150" size="1200,550" backgroundColor="#60ffffff" transparent="1" alphatest="blend" zPosition="2" />
					<ePixmap position="50,150" pixmap="skin_default/buttons/key_green.png" size="80,40" alphatest="blend" zPosition="2" />
					<widget name="key_green" font="Regular;30" position="130,150" size="350,40" halign="left" valign="center" backgroundColor="black" zPosition="1" transparent="1" />
					<ePixmap position="50,200" pixmap="skin_default/buttons/key_red.png" size="80,40" alphatest="blend" zPosition="2" />
					<widget name="key_red" font="Regular;30" position="130,200" size="350,40" halign="left" valign="center" backgroundColor="black" zPosition="1" transparent="1" />
					<ePixmap position="50,250" pixmap="skin_default/buttons/key_blue.png" size="80,40" alphatest="blend" zPosition="2" />
					<widget name="key_blue" font="Regular;30" position="135,250" size="350,40" halign="left" valign="center" backgroundColor="black" zPosition="1" transparent="1" />
					<eLabel position="50,300" size="300,3" backgroundColor="#202020" zPosition="1" />
					<ePixmap position="48,332" size="80,80" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Schiffe/pic/rocket.png" scale="1" alphatest="blend" zPosition="1" />
					<widget name="result" render="Label" position="131,335" size="200,34" font="Regular;30" halign="left" foregroundColor="yellow" backgroundColor="#000000" transparent="1" zPosition="3" />
					<widget name="movex" render="Label" position="130,375" size="200,34" font="Regular;30" halign="left" foregroundColor="yellow" backgroundColor="#000000" transparent="1" zPosition="3" />
				</screen>"""

		# Find background color from current skin
		filename = resolveFilename(SCOPE_CURRENT_SKIN, "skin.xml")
		actual_skin = ElementTree.parse(filename).getroot()

		color_names = {}
		for c in actual_skin.findall("colors"):
			for color in c.findall("color"):
				name = color.attrib.get("name")
				value = color.attrib.get("value")
				if name and value:
					color_names[name] = value

		bgcolor = None
		for windowstyle in actual_skin.findall("windowstyle"):
			if windowstyle.attrib.get("id") == "0":
				for color in windowstyle.findall("color"):
					color_type = color.attrib.get("name")
					color_value = color.attrib.get("color")
					if color_value and color_value[0] != '#':
						color_value = color_names.get(color_value, '#000000')
					if color_type == "Background" and color_value:
						bgcolor = int(color_value[1:], 16)
						break
				if bgcolor is not None:
					break

		if bgcolor is None:
			bgcolor = rgb(0, 0, 0)

		Screen.__init__(self, session)
		self.setTitle(f"Schiffe V.{__version__}")
		self["Canvas"] = CanvasSource()
		self["message"] = Label(_("Status"))
		self["info"] = Label(_(f"Schiffe v.{__version__}"))
		self["key_green"] = Button(_("New Game"))
		self["key_blue"] = Button(_("Solve Game"))
		self["key_red"] = Button(_("Quit Game"))
		self["result"] = Label()
		self["movex"] = Label()

		self.cnt = 0
		self.moves = 0
		self.gameover = False
		self.focus_index = 0

		self.timer = eTimer()
		self.timer.callback.append(self.timer_handler)
		self.timer.start(150, 1)

		self["actions"] = ActionMap(
			["WizardActions", "ColorActions", "SetupActions"],
			{
				"ok": self.ok_pressed,
				"up": self.up_pressed,
				"down": self.down_pressed,
				"left": self.left_pressed,
				"right": self.right_pressed,
				"red": self.quit_game,
				"green": self.new_game,
				"blue": self.solve_game,
				"cancel": self.quit_game
			}, -1
		)

		self["Canvas"].fill(0, 0, canvas_w, canvas_h, bgcolor)

		self.you = []
		self.box = []
		self.you_cells = []
		self.box_cells = []

		for j in range(Y_MAX):
			for i in range(X_MAX):
				cell = GameCell(
					self["Canvas"],
					i * (cell_size + cell_offset) + x0_offset,
					j * (cell_size + cell_offset),
					cell_size, cell_size
				)
				self.box_cells.append(cell)

		for j in range(Y_MAX):
			for i in range(X_MAX):
				cell = GameCell(
					self["Canvas"],
					i * (cell_size + cell_offset) + x1_offset,
					j * (cell_size + cell_offset),
					cell_size, cell_size
				)
				self.you_cells.append(cell)

		self.onLayoutFinish.append(self.load_game)

		# Display help text in the "result" widget at startup
		self.show_help()

	def show_help(self):
		"""Display game instructions in the result widget."""
		help_text = "\n".join([
			_("== How to play =="),
			_("Navigate with arrows"),
			_("Press OK to shoot."),
			_("Green: New game."),
			_("Blue: Solve (show ships)"),
			_("Red: Quit and save."),
			_("Hit ships appear red,"),
			_("Misses as '*'.")
		])

		if is_fhd() and "message" in self:
			self["message"].setText(help_text)
		else:
			self["message"].setText(help_text)

	def ok_pressed(self):
		if self.gameover:
			print("Game over, start new game!")
			return

		cell = self.box_cells[self.focus_index]
		if cell.value() in (2, 4):
			return

		if cell.value() == 0:
			cell.set_value(2)
		elif cell.value() == 3:
			cell.set_value(4)
		cell.paint()
		self.moves += 1

		# Check if player won
		hit_count = sum(1 for c in self.box_cells if c.value() == 4)
		if hit_count == 23:
			self.gameover = True
			self["message"].setText(_("You won!"))
			self.timer.stop()
			return

		# Computer's turn
		calc_new_field(self.you)
		for i, cell in enumerate(self.you_cells):
			cell.set_value(self.you[i])
			cell.paint()

		# Check if computer won
		hit_count = sum(1 for c in self.you_cells if c.value() == 4)
		if hit_count == 23:
			self.gameover = True
			self["message"].setText(_("You lose!"))
			self.timer.stop()
			# Reveal all computer ships
			for cell in self.box_cells:
				cell.set_hide(False)
				cell.paint()

	def up_pressed(self):
		if self.focus_index >= X_MAX:
			self.box_cells[self.focus_index].set_focus(False)
			self.box_cells[self.focus_index].paint()
			self.focus_index -= X_MAX
			self.box_cells[self.focus_index].set_focus(True)
			self.box_cells[self.focus_index].paint()

	def down_pressed(self):
		if self.focus_index < XY_MAX - X_MAX:
			self.box_cells[self.focus_index].set_focus(False)
			self.box_cells[self.focus_index].paint()
			self.focus_index += X_MAX
			self.box_cells[self.focus_index].set_focus(True)
			self.box_cells[self.focus_index].paint()

	def left_pressed(self):
		if self.focus_index > 0 and (self.focus_index % X_MAX) != 0:
			self.box_cells[self.focus_index].set_focus(False)
			self.box_cells[self.focus_index].paint()
			self.focus_index -= 1
			self.box_cells[self.focus_index].set_focus(True)
			self.box_cells[self.focus_index].paint()

	def right_pressed(self):
		if self.focus_index < XY_MAX - 1 and ((self.focus_index + 1) % X_MAX) != 0:
			self.box_cells[self.focus_index].set_focus(False)
			self.box_cells[self.focus_index].paint()
			self.focus_index += 1
			self.box_cells[self.focus_index].set_focus(True)
			self.box_cells[self.focus_index].paint()

	def timer_handler(self):
		if is_fhd():
			self["result"].setText(_("%10d shots") % self.moves)
			self["movex"].setText(_("%10d sec") % self.cnt)
		else:
			self.instance.setTitle(
				_("Battleship %s %10d shots %10d sec") % (__version__, self.moves, self.cnt)
			)
		self.cnt += 1

	def new_game(self, load_from_file=False):
		self["message"].setText("")
		self.gameover = False
		self.focus_index = 0
		self.show_help()   # Show help again on new game

		if not load_from_file:
			self.moves = 0
			self.cnt = 0
			self.you = [0] * XY_MAX
			ships(self.you)
			self.box = [0] * XY_MAX
			ships(self.box)

		for i, cell in enumerate(self.you_cells):
			cell.set_value(self.you[i])
			cell.paint()

		for i, cell in enumerate(self.box_cells):
			cell.set_value(self.box[i])
			cell.set_hide(True)
			cell.set_focus(i == self.focus_index)
			cell.paint()

		self.timer.start(1000)

	def solve_game(self):
		if not self.gameover:
			self.gameover = True
			self["message"].setText(_("You lost!"))
			self.timer.stop()
			for cell in self.box_cells:
				cell.set_hide(False)
				cell.paint()

	def save_game(self):
		try:
			with open(SAVE_FILE, "w", encoding="utf-8") as sav:
				sav.write(f"{self.moves} {self.cnt}\n")
				for i, cell in enumerate(self.box_cells):
					sav.write(f"{cell.value()} ")
					if (i + 1) % X_MAX == 0:
						sav.write("\n")
				for i, cell in enumerate(self.you_cells):
					sav.write(f"{cell.value()} ")
					if (i + 1) % X_MAX == 0:
						sav.write("\n")
		except OSError as e:
			print(f"Error saving game: {e}")

	def load_game(self):
		try:
			if fileExists(SAVE_FILE):
				with open(SAVE_FILE, "r", encoding="utf-8") as sav:
					line = sav.readline().strip()
					parts = line.split()
					if len(parts) >= 2:
						self.moves = int(parts[0])
						self.cnt = int(parts[1])

					self.box = []
					for xs in range(Y_MAX):
						line = sav.readline().strip()
						if not line:
							break
						self.box.extend(int(x) for x in line.split())

					self.you = []
					for xs in range(Y_MAX):
						line = sav.readline().strip()
						if not line:
							break
						self.you.extend(int(x) for x in line.split())

				self.new_game(load_from_file=True)
			else:
				self.new_game()
		except Exception as e:
			print(f"Error loading game: {e}")
			self.new_game()

	def quit_game(self):
		self.timer.stop()
		self.save_game()
		self.close()


def random_shot():
	"""Return a pseudo‑random integer (compatible with old randint)."""
	return randint(0, 32767)


def ships(field):
	"""Place ships randomly on the given field (list of length XY_MAX)."""
	# Build a shadow grid with a 1‑cell border
	shadow = [[0] * (X_MAX + 3) for _ in range(Y_MAX + 3)]

	for ship_len in range(5, 1, -1):
		if ship_len == 2:
			max_ships = 4
		elif ship_len == 3:
			max_ships = 2
		else:
			max_ships = 1

		for xs in range(max_ships):
			placed = False
			for xs in range(100):  # try up to 100 times
				if random_shot() % 2 == 0:
					# horizontal
					x = random_shot() % (X_MAX - ship_len + 1)
					y = random_shot() % Y_MAX
					ok = True
					for j in range(ship_len + 2):
						if shadow[x + j][y] != 0 or shadow[x + j][y + 1] != 0 or shadow[x + j][y + 2] != 0:
							ok = False
							break
					if ok:
						for j in range(ship_len):
							field[x + y * X_MAX + j] = 3
							shadow[x + j + 1][y + 1] = 1
						placed = True
						break
				else:
					# vertical
					x = random_shot() % X_MAX
					y = random_shot() % (Y_MAX - ship_len + 1)
					ok = True
					for j in range(ship_len + 2):
						if shadow[x][y + j] != 0 or shadow[x + 1][y + j] != 0 or shadow[x + 2][y + j] != 0:
							ok = False
							break
					if ok:
						for j in range(ship_len):
							field[x + (y + j) * X_MAX] = 3
							shadow[x + 1][y + j + 1] = 1
						placed = True
						break
			if not placed:
				return False
	return True


def calc_new_field(field):
	"""Computer's turn: update the field with a shot."""
	# First, try to continue hitting around a previously hit ship
	for i in range(XY_MAX):
		if field[i] == 4:
			lx = i % X_MAX
			ly = i // X_MAX

			# Check adjacent cells (right, left, down, up)
			if lx > 0:
				idx = lx + ly * X_MAX - 1
				if field[idx] == 0:
					field[idx] = 2
					return
				if field[idx] == 3:
					field[idx] = 4
					# mark surroundings as "to be avoided" (value 1)
					for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
						nx, ny = lx - 1 + dx, ly + dy
						if 0 <= nx < X_MAX and 0 <= ny < Y_MAX and field[nx + ny * X_MAX] != 2:
							field[nx + ny * X_MAX] = 1
					return

			if lx < X_MAX - 1:
				idx = lx + ly * X_MAX + 1
				if field[idx] == 0:
					field[idx] = 2
					return
				if field[idx] == 3:
					field[idx] = 4
					for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
						nx, ny = lx + 1 + dx, ly + dy
						if 0 <= nx < X_MAX and 0 <= ny < Y_MAX and field[nx + ny * X_MAX] != 2:
							field[nx + ny * X_MAX] = 1
					return

			if ly > 0:
				idx = lx + (ly - 1) * X_MAX
				if field[idx] == 0:
					field[idx] = 2
					return
				if field[idx] == 3:
					field[idx] = 4
					for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
						nx, ny = lx + dx, ly - 1 + dy
						if 0 <= nx < X_MAX and 0 <= ny < Y_MAX and field[nx + ny * X_MAX] != 2:
							field[nx + ny * X_MAX] = 1
					return

			if ly < Y_MAX - 1:
				idx = lx + (ly + 1) * X_MAX
				if field[idx] == 0:
					field[idx] = 2
					return
				if field[idx] == 3:
					field[idx] = 4
					for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
						nx, ny = lx + dx, ly + 1 + dy
						if 0 <= nx < X_MAX and 0 <= ny < Y_MAX and field[nx + ny * X_MAX] != 2:
							field[nx + ny * X_MAX] = 1
					return

	# No immediate hit to continue: random search, preferring cells with value 0
	# but also try cells that are not marked as "avoid" (value 1)
	# We'll just pick a random cell among those not yet shot (0 or 3)
	# To avoid infinite loop, we keep a counter
	attempts = 0
	while attempts < 1000:
		x = random_shot() % X_MAX
		y = random_shot() % Y_MAX
		idx = x + y * X_MAX
		if field[idx] == 0:
			field[idx] = 2
			return
		if field[idx] == 3:
			field[idx] = 4
			# Mark surroundings as avoid
			for dx in (-1, 0, 1):
				for dy in (-1, 0, 1):
					nx, ny = x + dx, y + dy
					if 0 <= nx < X_MAX and 0 <= ny < Y_MAX and field[nx + ny * X_MAX] == 0:
						field[nx + ny * X_MAX] = 1
			return
		attempts += 1
	# Fallback: first water cell
	for i, val in enumerate(field):
		if val == 0:
			field[i] = 2
			return
		if val == 3:
			field[i] = 4
			return
