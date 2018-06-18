#!/usr/bin/env python

try:
	import tkinter as tk
	from tkinter import ttk
	from tkinter.filedialog import askdirectory
except:
	import Tkinter as tk
	import ttk
	from tkFileDialog import askdirectory
from PIL import Image, ImageTk
from queue import Queue
from threading import Thread

import popupmsg
import image_process as ip

def run_the_code(preview=False):
	args = (
		e1.get(),
		e2.get(),
		checkVar1.get(),
		int(contour.get()),
		int(dialate.get()),
		int(blurred1.get()),
		int(blurred2.get()),
		int(edge_detect1a.get()),
		int(edge_detect1b.get()),
		int(edge_detect2a.get()),
		int(edge_detect2b.get()),
		int(padding_n.get()),
		int(padding_s.get()),
		int(padding_e.get()),
		int(padding_w.get()),
		queue,
		preview)
	t = Thread(target=ip.run_the_code, args=args)
	t.daemon = True
	t.start()

def run_the_code_once():
	run_the_code(preview=True)

def reset_sliders():
	for slider in Slider.sliders:
		slider.set(slider.default)

def input_directory():
	input_directory = askdirectory(initialdir = os.getcwd(),title = "Select file")
	e1.delete(0, tk.END)
	e1.insert(0, input_directory)

def output_directory():
	output_directory = askdirectory(initialdir = os.getcwd(),title = "Select file")
	e2.delete(0, tk.END)
	e2.insert(0, output_directory)

class Slider(ttk.Scale):
	sliders = []
	def __init__(self, master=None, row=None, step=1, **kwargs):
		self.step = step
		self.default = kwargs.get('value', 0)
		btn = ttk.Button(master, text="-", command=self.subtract)
		btn.grid(row=row, column=0, sticky=tk.E)
		lbl = tk.Label(master, text=kwargs['from_'])
		lbl.grid(row=row, column=1, sticky=tk.E)
		self.scaleVal = tk.IntVar(value=self.default)
		ttk.Scale.__init__(self, orient=tk.HORIZONTAL, variable=self.scaleVal, command=self.validate, **kwargs)
		self.grid(row=row, column=2, sticky='ew', ipadx=0, ipady=0)
		lbl = tk.Label(master, text="100")
		lbl.grid(row=row, column=3)
		btn = ttk.Button(master, text="+", command=self.add)
		btn.grid(row=row, column=4)
		lbl = tk.Label(master, textvariable=self.scaleVal)
		lbl.grid(row=row, column=5)
		master.grid_rowconfigure(row, weight=1)
		self.sliders.append(self)

	def validate(self, args):
		self.scaleVal.set((int(float(args))-self.default)//self.step*self.step+self.default)

	def subtract(self):
		self.set(self.get()-self.step)

	def add(self):
		self.set(self.get()+self.step)

#--Tkinter--#
master = tk.Tk()
try:
	master.iconbitmap("Logo.ico")
except:
	pass
master.wm_title("Inventory Imager")

#Menu
'''
Info Menu
'''
menubar = tk.Menu(master)
Info = tk.Menu(menubar, tearoff=0)
Info.add_command(label="Largest Contour Allowed", command=popupmsg.contour)
Info.add_command(label="Dilate", command=popupmsg.dilate)
Info.add_command(label="Blur 1", command=popupmsg.Blur_1)
Info.add_command(label="Blur 2", command=popupmsg.Blur_2)
Info.add_command(label="Edge Detector 1", command=popupmsg.Edge_Detector_1)
Info.add_command(label="Edge Detector 2", command=popupmsg.Edge_Detector_2)
Info.add_command(label="Padding", command=popupmsg.padding)
Info.add_separator()
Info.add_command(label="Exit", command=quit)
menubar.add_cascade(label="Info", menu=Info)

'''
Profiles Menu
'''
Profiles = tk.Menu(menubar, tearoff=0)
Profiles.add_command(label="Profile 1")
Profiles.add_command(label="Profile 2")
Profiles.add_command(label="Profile 3")
Profiles.add_separator()
Profiles.add_command(label="Add Profile")
menubar.add_cascade(label="Profiles", menu=Profiles)
master.config(menu=menubar)

'''
Each section of code below is separated by their row placement within the GUI
'''

#Input
ttk.Button(master, text="Input", command=input_directory).grid(row=0, column=29, sticky="nsew")
e1 = tk.Entry(master)
e1.grid(row=0, column=0, pady=4, padx=4, sticky='ew', columnspan=29)
e1.insert(0, "Input") # default

#Output
ttk.Button(master, text="Output", command=output_directory).grid(row=1, column=29, sticky="nsew")
e2 = tk.Entry(master)
e2.grid(row=1, column=0, pady=4, padx=4, sticky='ew', columnspan=29)
e2.insert(0, "Output") # default


#Layer under input and output
checkVar1 = tk.IntVar()
checkVar1.set(1)
checkVal1 = tk.Checkbutton(master, text="Make Square", variable=checkVar1)
checkVal1.grid(row=4, column=0, sticky='ew')
tk.Label(master, text="Options").grid(row=4, column=2)
tk.Label(master, text="Current").grid(row=4, column=5)
ttk.Button(master, text="Set Defaults", command=reset_sliders).grid(row=4, column=4)

master.grid_columnconfigure(2, weight=1)

#Largest Contours Allowed
master.grid_rowconfigure(5, weight=1)
tk.Label(master, text="Largest Contour Allowed (Default: 5)").grid(row=5, column=2, sticky=tk.S)
contour = Slider(master, row=6, from_=1, to=100, value=5)

#Dilate
master.grid_rowconfigure(7, weight=1)
tk.Label(master, text="Dilate (Default: 3)").grid(row=7, column=2, sticky=tk.S)
dialate = Slider(master, row=8, from_=1, to=20, value=3)

#Blurred 1
master.grid_rowconfigure(9, weight=1)
tk.Label(master, text="Blur 1 (Default: 7)").grid(row=9, column=2, sticky=tk.S)
blurred1 = Slider(master, row=10, from_=1, to=99, value=7, step=2)

#Blurred 2
master.grid_rowconfigure(11, weight=1)
tk.Label(master, text="Blur 2 (Default: 7)").grid(row=11, column=2, sticky=tk.S)
blurred2 = Slider(master, row=12, from_=1, to=99, value=7, step=2)

#Edge Detector 1
master.grid_rowconfigure(13, weight=1)
tk.Label(master, text="Edge Detector 1 (Default: 100,180)").grid(row=13, column=2, sticky=tk.S)
edge_detect1a = Slider(master, row=14, from_=1, to=300, value=100)
edge_detect1b = Slider(master, row=15, from_=1, to=300, value=180)

#Edge Detector 2
master.grid_rowconfigure(16, weight=1)
tk.Label(master, text="Edge Detector 2 (Default: 20,40)").grid(row=16, column=2, sticky=tk.S)
edge_detect2a = Slider(master, row=17, from_=1, to=100, value=20)
edge_detect2b = Slider(master, row=18, from_=1, to=100, value=40)

#Final Image Padding
master.grid_rowconfigure(19, weight=1)
tk.Label(master, text="Padding (Default: N5,S5,E5,W5)").grid(row=19, column=2, sticky=tk.S)
padding_n = Slider(master, row=20, from_=1, to=40, value=5)
padding_s = Slider(master, row=21, from_=1, to=40, value=5)
padding_e = Slider(master, row=22, from_=1, to=40, value=5)
padding_w = Slider(master, row=23, from_=1, to=40, value=5)

#Lower Buttons
ttk.Button(master, text='Quit', command=master.quit).grid(row=24, column=0, sticky='ew')

btn=ttk.Button(master, text='Activate', command=run_the_code)
btn.grid(row=24, column=2, sticky=tk.E, pady=4, padx=4)

btn = ttk.Button(master, text='Preview', command=run_the_code_once)
btn.grid(row=24, column=3, sticky='ew', pady=4, columnspan=2)

#Images
master.grid_columnconfigure(7, weight=1)

ttk.Separator(master, orient=tk.VERTICAL).grid(row=2, column=6, rowspan=23, sticky='ns')

class Mockapapella(tk.Label):
	''' a Label that resizes the contained image'''
	def __init__(self, master=None, **kwargs):
		tk.Label.__init__(self, master, **kwargs)
		self.original_image = None
		self.photoimage = None
		#~

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
		self.after(100, lambda: self.bind('<Configure>', self.resize_and_display))

image_frame = tk.Frame(master)
image_frame.grid(row=3, column=7, rowspan=50, columnspan=50, sticky='nsew')
image_frame.rowconfigure(0, weight=1)
image_frame.columnconfigure(0, weight=1)
image_frame.rowconfigure(2, weight=1)

lbl1 = Mockapapella(image_frame)
lbl1.grid(row=0, column=0, sticky='nsew', pady=4, padx=4)

sep=ttk.Separator(image_frame, orient=tk.HORIZONTAL)
sep.grid(row=1, column=0, sticky='ew')

lbl2 = Mockapapella(image_frame)
lbl2.grid(row=2, column=0, sticky='nsew', pady=4, padx=4)

# set up the Queue to use for the images
queue = Queue()
def check_queue():
	'''checks the queue every 100 milliseconds to see if the image labels need to be updated'''
	if not queue.empty():
		item = queue.get()
		if item == "finished":
			popupmsg.finished_processing()
		else:
			img1, img2 = item
			lbl1.load(img1)
			lbl2.load(img2)

	master.after(100, check_queue)
check_queue()

master.geometry("960x600")
master.mainloop()
