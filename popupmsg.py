#!/usr/bin/env python

try:
	import tkinter as tk
	from tkinter import ttk
	from tkinter.filedialog import askdirectory
except:
	import Tkinter as tk
	import ttk
	from tkFileDialog import askdirectory

class Popup(tk.Toplevel):
	def __init__(self, master=None, title='', msg='', **kwargs):
		tk.Toplevel.__init__(self, master, **kwargs)
		self.title(title)
		self.geometry("350x125")

		label = ttk.Label(self, text=msg, wrap=300)
		label.pack(side="top", pady=10, padx=10)
		B1 = ttk.Button(self, text="Okay", command=self.destroy)
		B1.pack(side=tk.BOTTOM, pady=10, padx=10)

class InfoPopup(Popup):
	def __init__(self, master=None, **kwargs):
		Popup.__init__(self, master, **kwargs)
		try: # only windows supports ico files
			self.iconbitmap("Icons/Logo.ico")
		except:
			pass

class WarningPopup(Popup):
	def __init__(self, master=None, **kwargs):
		Popup.__init__(self, master, **kwargs)
		try: # only windows supports ico files
			self.iconbitmap("Icons/Warning.ico")
		except:
			pass

#Functions
def Blur_1(master=None):
	InfoPopup(master,
		title="Blur 1 Information",
		msg="Change how much to blur the image before canny edge detection is applied.")

def Edge_Detector_1(master=None):
	InfoPopup(master,
		title="Edge Detector 1 Information",
		msg="Change how accurately the object is detected and cropped.")

def padding(master=None):
	InfoPopup(master,
		title="Padding Information",
		msg="Change how much white space is around the item in the final image.")

def Edge_Detector_2(master=None):
	InfoPopup(master,
		title="Edge Detector 2 Information",
		msg="Change how accurately the fine lines of the object are detected.")

def dilate(master=None):
	InfoPopup(master,
		title="Edge Detector 1 Information",
		msg="Change how many pixels to inflate each contour point by.")

def contour(master=None):
	InfoPopup(master,
		title="Edge Detector 1 Information",
		msg="Change how much area in relation to the total image size the contour must encompass to be considered a valid contour.")

def Blur_2(master=None):
	InfoPopup(master,
		title="Edge Detector 1 Information",
		msg="How much to blur the initial image.")

def input_filepath_error(master=None):
	WarningPopup(master,
		title="Error",
		msg="Specify Input Folder.")

def blur_error(master=None):
	WarningPopup(master,
		title="Error",
		msg= "One of your blur variables is even! Change it to an odd number to continue.")

def finished_processing(master=None):
	InfoPopup(master,
		title="Finish Message",
		msg="Image processing completed.")

def not_supported_yet(master=None):
	WarningPopup(master,
		title="Error",
		msg="This feature is not yet supported.")

def no_profile_name(master=None):
	WarningPopup(master,
		title="Error",
		msg="Please enter a name for the profile.")

def profile_already_exists(master=None):
	WarningPopup(master,
		title="Error",
		msg="Profile already exists. Overwrite?")


# root=tk.Tk()
# root.mainloop()