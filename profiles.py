#!/usr/bin/env python

try:
	import tkinter as tk
	from tkinter import ttk
	from tkinter.filedialog import askdirectory
except:
	import Tkinter as tk
	import ttk
	from tkFileDialog import askdirectory

import os

import Inventory_Imager as II
import popupmsg

# root=tk.Tk()
class ProfilePopup(tk.Toplevel):
	def __init__(self, master=None, **kwargs):
		tk.Toplevel.__init__(self, master, **kwargs)
		self.title("Add Profile")
		self.geometry("300x75")
		self.iconbitmap("Icons/Logo.ico")

		self.profiles = []
		self.columnconfigure(0, weight=1)
		self.columnconfigure(1, weight=1)

		self.profile_name = tk.Entry(self)
		self.profile_name.grid(row=0, column=0, padx=4, pady=4, sticky="ew", columnspan=2)

		btn = ttk.Button(self, text="Quit", command=self.destroy)
		btn.grid(row=1, column=0)
		btn2 = ttk.Button(self, text="Add Profile", command=lambda: ProfilePopup.add_profile(self))
		btn2.grid(row=1, column=1)
		btn3 = ttk.Button(self, text="Print", command=lambda: ProfilePopup.print_profiles(self))
		btn3.grid(row=1, column=2)

	def add_profile(self):
		# self.options = Options(self)
		'''
		Get Current Values of all the sliders, checkbox, the Input, and Output
		'''
		if self.profile_name.get() == "":
			popupmsg.no_profile_name()
			return
		self.options = II.Options(self)
		self.directories = II.DirInput(self)
		self.profiles.append([self.directories.inputdir.get(),
							  self.directories.outputdir.get(),
							  self.options.checkVar1.get(),
							  self.options.contour.get(),
							  self.options.dialate.get(),
							  self.options.blurred1.get(),
							  self.options.blurred2.get(),
						  self.options.edge_detect1a.get(),
							  self.options.edge_detect1b.get(),
							  self.options.edge_detect2a.get(),
							  self.options.edge_detect2b.get(),
							  self.options.padding_n.get(),
							  self.options.padding_s.get(),
							  self.options.padding_e.get(),
							  self.options.padding_w.get()])
		profile_file = open("Profiles/" + str(self.profile_name.get()) + ".txt", "w+")
		for options_lists in self.profiles:
			for option in options_lists:
				profile_file.write("{}\n".format(option))
		self.destroy()

	def print_profiles(self):
		print(self.profiles)

class setSliderValuesEqualToProfileValues():
	'''
	read in the text file
	parse out the numerical values and put them in a list
	for value in profile:
		set slider in slider equal to value
	'''
	pass

def create_profile(master=None):
	ProfilePopup(master)

def set_slider_values():
	pass

# ProfilePopup(root)
# root.mainloop()