#!/usr/bin/env python

try:
	# try the python2 imports
	import tkinter as tk
	from tkinter import ttk
	from tkinter.filedialog import askdirectory
except ImportError:
	# try python3 imports
	import Tkinter as tk
	import ttk
	from tkFileDialog import askdirectory
import os
from PIL import Image, ImageTk
from queue import Queue
from threading import Thread

import popupmsg
import image_process as ip
import profiles

class DirInput(tk.Frame):
	def __init__(self, master=None, **kwargs):
		tk.Frame.__init__(self, master, **kwargs)
		self.columnconfigure(0, weight=1)

		#Input
		self.inputdir = tk.Entry(self)
		self.inputdir.grid(row=0, column=0, pady=4, padx=4, sticky="ew")
		self.inputdir.insert(0, "Input") # default value
		btn = ttk.Button(self, text="Input", command=lambda: self.get_dir(self.inputdir))
		btn.grid(row=0, column=1)

		#Output
		self.outputdir = tk.Entry(self)
		self.outputdir.grid(row=1, column=0, pady=4, padx=4, sticky="ew")
		self.outputdir.insert(0, "Output") # default value
		btn = ttk.Button(self, text="Output", command=lambda: self.get_dir(self.outputdir))
		btn.grid(row=1, column=1)

	def get_dir(self, widget):
		directory = askdirectory(initialdir=os.getcwd(), title = "Select file")
		widget.delete(0, tk.END)
		widget.insert(0, directory)


class StepScale(ttk.Scale):
	'''ttk.Scale increments by 1, and apparently there's no way to change that
	So this class lies to the user instead'''
	def __init__(self, master=None, step=1, force_int=True, **kwargs):
		self.from_ = kwargs.pop('from_', 0)
		self.to = kwargs.pop('to', 1)
		self.step = step
		self.range_ = self.to - self.from_
		self.value = kwargs.pop('value', 0)
		self.command = kwargs.pop('command', None)
		self.variable = kwargs.pop('variable', tk.IntVar()) # actual user value
		self.variable.set(self.value)
		self.force_int = force_int
		self.resolution = int(self.range_ / self.step)
		ttk.Scale.__init__(self, master, to=self.resolution, command=self.validate, **kwargs)
		self.get = self.variable.get
		self.set(self.value)

	def validate(self, args):
		percentage = ttk.Scale.get(self) / float(self.resolution)
		real_value = percentage * self.range_ + self.from_
		if self.force_int:
			diff = (real_value-self.value) % self.step
			if diff > self.step / 2.0:
				real_value = int(round(real_value+self.step-diff)) # round up
			else:
				real_value = int(round(real_value-diff)) # round down
		self.variable.set(real_value)
		if self.command is not None:
			self.command(real_value)

	def set(self, value):
		if value > self.to:
			value = self.to
		elif value < self.from_:
			value = self.from_
		ttk.Scale.set(self, float(value-self.from_) / self.step)
		self.variable.set(value)


class Slider(StepScale):
	sliders = []
	def __init__(self, master=None, row=None, **kwargs):
		btn = ttk.Button(master, text="-", width=2, command=self.subtract)
		btn.grid(row=row, column=0, sticky=tk.E)
		lbl = tk.Label(master, text=kwargs.get('from_',''))
		lbl.grid(row=row, column=1, sticky=tk.E)
		StepScale.__init__(self, master, orient=tk.HORIZONTAL, length=400, **kwargs)
		self.grid(row=row, column=2, sticky='ew')
		lbl = tk.Label(master, text=kwargs.get('to', ''))
		lbl.grid(row=row, column=3)
		btn = ttk.Button(master, text="+", width=2, command=self.add)
		btn.grid(row=row, column=4)
		lbl = tk.Label(master, textvariable=self.variable)
		lbl.grid(row=row, column=5)
		self.sliders.append(self)

	def subtract(self):
		self.set(self.get()-self.step)

	def add(self):
		self.set(self.get()+self.step)

	@classmethod
	def reset_all(cls):
		for slider in cls.sliders:
			slider.set(slider.value)


class Menubar(tk.Menu):
	def __init__(self, master=None, **kwargs):
		tk.Menu.__init__(self, master, **kwargs)

		# Info Menu
		Info = tk.Menu(self, tearoff=0)
		Info.add_command(label="Smallest Contour Allowed", command=popupmsg.contour)
		Info.add_command(label="Dilate", command=popupmsg.dilate)
		Info.add_command(label="Blur 1", command=popupmsg.Blur_1)
		Info.add_command(label="Blur 2", command=popupmsg.Blur_2)
		Info.add_command(label="Edge Detector 1", command=popupmsg.Edge_Detector_1)
		Info.add_command(label="Edge Detector 2", command=popupmsg.Edge_Detector_2)
		Info.add_command(label="Padding", command=popupmsg.padding)
		Info.add_separator()
		Info.add_command(label="Exit", command=quit)
		self.add_cascade(label="Info", menu=Info)

		# Profiles Menu
		Profiles = tk.Menu(self, tearoff=0)
		Profiles.add_command(label="Profile 1", command=popupmsg.not_supported_yet)
		Profiles.add_command(label="Profile 2", command=popupmsg.not_supported_yet)
		Profiles.add_command(label="Profile 3", command=popupmsg.not_supported_yet)
		Profiles.add_separator()
		Profiles.add_command(label="Add Profile", command=popupmsg.not_supported_yet)
		self.add_cascade(label="Profiles", menu=Profiles)


class Options(ttk.LabelFrame):
	def __init__(self, master=None, **kwargs):
		ttk.LabelFrame.__init__(self, master, text="Options", **kwargs)

		#Layer under input and output
		self.checkVar1 = tk.IntVar()
		self.checkVar1.set(1)
		checkVal1 = tk.Checkbutton(self, text="Make Square", variable=self.checkVar1)
		checkVal1.grid(row=1, column=0, columnspan=4, sticky='w')
		btn = ttk.Button(self, text="Reset All to Defaults", command=Slider.reset_all)
		btn.place(relx=1, rely=0, anchor='ne')

		#Smallest Contours Allowed
		tk.Label(self, text="Smallest Contour Allowed (Default: 5% of Total Image)").grid(row=5, column=2, sticky=tk.S)
		self.contour = Slider(self, row=6, from_=1, to=100, value=5)

		#Dilate
		tk.Label(self, text="Dilate (Default: 3)").grid(row=7, column=2, sticky=tk.S)
		self.dialate = Slider(self, row=8, from_=1, to=20, value=3)

		#Blurred 1
		tk.Label(self, text="Blur 1 (Default: 7)").grid(row=9, column=2, sticky=tk.S)
		self.blurred1 = Slider(self, row=10, from_=1, to=99, value=7, step=2)

		#Blurred 2
		tk.Label(self, text="Blur 2 (Default: 7)").grid(row=11, column=2, sticky=tk.S)
		self.blurred2 = Slider(self, row=12, from_=1, to=99, value=7, step=2)

		#Edge Detector 1
		tk.Label(self, text="Edge Detector 1 (Default: 100,180)").grid(row=13, column=2, sticky=tk.S)
		self.edge_detect1a = Slider(self, row=14, from_=1, to=300, value=100)
		self.edge_detect1b = Slider(self, row=15, from_=1, to=300, value=180)

		#Edge Detector 2
		tk.Label(self, text="Edge Detector 2 (Default: 20,40)").grid(row=16, column=2, sticky=tk.S)
		self.edge_detect2a = Slider(self, row=17, from_=1, to=100, value=20)
		self.edge_detect2b = Slider(self, row=18, from_=1, to=100, value=40)

		#Final Image Padding
		tk.Label(self, text="Padding (Default: N5,S5,E5,W5)").grid(row=19, column=2, sticky=tk.S)
		self.padding_n = Slider(self, row=20, from_=0, to=80, value=5)
		self.padding_s = Slider(self, row=21, from_=0, to=80, value=5)
		self.padding_e = Slider(self, row=22, from_=0, to=80, value=5)
		self.padding_w = Slider(self, row=23, from_=0, to=80, value=5)


class LowerButtons(tk.Frame):
	def __init__(self, master=None, **kwargs):
		tk.Frame.__init__(self, master, **kwargs)

		btn = ttk.Button(self, text='Quit', command=master.quit)
		btn.pack(side=tk.LEFT)

		btn=ttk.Button(self, text='Activate', command=master.run_the_code)
		btn.pack(side=tk.LEFT)

		btn = ttk.Button(self, text='Preview', command=master.run_the_code_once)
		btn.pack(side=tk.LEFT)


class Mockapapella(tk.Label):
	''' a Label that resizes the contained image'''
	def __init__(self, master=None, **kwargs):
		tk.Label.__init__(self, master, **kwargs)
		self.original_image = None
		self.photoimage = None

	def load(self, image):
		''' load an image
		image: is a PIL Image instance'''
		self.original_image = image # this replaces any reference to the previous image, to allow garbage collection
		image_width, image_height = self.original_image.size
		self.resize_and_display()

	def resize_and_display(self, event=None):
		if self.original_image is None:
			return # nothing to do
		self.unbind('<Configure>')
		# easy resize code lets PIL do the work with the thumbnail method
		new_img = self.original_image.copy()
		new_img.thumbnail((self.winfo_width()-10, self.winfo_height()-10))
		self.photoimage = ImageTk.PhotoImage(new_img) # allows garbage collection of the old photoimage
		self.config(image=self.photoimage)
		self.after(150, lambda: self.bind('<Configure>', self.resize_and_display))


class StatusBar(tk.Label):
	def __init__(self, master=None, queue=None, **kwargs):
		tk.Label.__init__(self, master, **kwargs)
		self.check_queue()

	def check_queue(self):
		if not self.master.status_q.empty():
			data = self.master.status_q.get()
			color = 'red' if data.lower().startswith('error') else 'black'
			self.config(text=data, fg=color)
		self.after(100, self.check_queue)


class Images(tk.Frame):
	def __init__(self, master=None, **kwargs):
		tk.Frame.__init__(self, master, **kwargs)

		self.rowconfigure(0, weight=1)
		self.columnconfigure(0, weight=1)
		self.rowconfigure(2, weight=1)

		self.lbl1 = Mockapapella(self)
		self.lbl1.grid(row=0, column=0, sticky='nsew', pady=4, padx=4)

		sep=ttk.Separator(self, orient=tk.HORIZONTAL)
		sep.grid(row=1, column=0, sticky='ew')

		self.lbl2 = Mockapapella(self)
		self.lbl2.grid(row=2, column=0, sticky='nsew', pady=4, padx=4)

		self.check_queue()

	def check_queue(self):
		'''checks the queue every 100 milliseconds to see if the image labels need to be updated'''
		if not self.master.queue.empty():
			item = self.master.queue.get()
			if item == "finished":
				popupmsg.finished_processing()
			else:
				img1, img2 = item
				self.lbl1.load(img1)
				self.lbl2.load(img2)

		self.after(100, self.check_queue)


class GUI(tk.Tk):
	def __init__(self, **kwargs):
		tk.Tk.__init__(self, **kwargs)

		try:
			self.iconbitmap("Icons/Logo.ico")
		except:
			print("Linux sucks")
		self.title("Inventory Imager")
		self.geometry("1200x700")

		self.columnconfigure(2, weight=1) # images column gets all leftover horizontal space
		self.rowconfigure(2, weight=1) # options row gets all leftover vertical space

		self.queue = Queue() # set up the Queue to use for the images
		self.status_q = Queue() # set up the Queue to use for status messages

		self.config(menu=Menubar(self))

		self.directories = DirInput(self)
		self.directories.grid(row=0, column=0, columnspan=3, sticky='ew')

		# I think these are ugly, but go ahead and uncomment them if you want
		# sep = ttk.Separator(self, orient=tk.HORIZONTAL)
		# sep.grid(row=1, column=0, columnspan=3, sticky='ew', pady=4)

		self.options = Options(self)
		self.options.grid(row=2, column=0, padx=4, pady=4, sticky='nsew')

		# sep = ttk.Separator(self, orient=tk.VERTICAL)
		# sep.grid(row=1, column=1, rowspan=3, sticky='ns')

		lower = LowerButtons(self)
		lower.grid(row=3, column=0, pady=4)

		images = Images(self)
		images.grid(row=2, column=2, rowspan=2, sticky='nsew')

		status = StatusBar(self, text='Ready', wrap=900)
		status.grid(row=4, column=0, columnspan=3, sticky='w')

	def run_the_code(self, preview=False):
		args = (
			self.directories.inputdir.get(),
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
			self.options.padding_w.get(),
			self.queue,
			self.status_q,
			preview)
		t = Thread(target=ip.run_the_code, args=args)
		t.daemon = True
		t.start()

	def run_the_code_once(self):
		'''a common way to reuse a chunk of code with one small difference is to
		use a variable "flag", in this case the preview variable'''
		self.run_the_code(preview=True)


def main():
	root = GUI()
	root.mainloop()


if __name__ == '__main__':
	main()
