#!/usr/bin/env python

try:
	import tkinter as tk
	from tkinter import ttk
	from tkinter.filedialog import askdirectory
except:
	import Tkinter as tk
	import ttk
	from tkFileDialog import askdirectory

import popupmsg

class InputField():
	def __init__(self, master=None, **kwargs):
		tk.Toplevel.__init__(self, master, **kwargs)
		pass
		'''
		Make profiles work tomorrow
		'''