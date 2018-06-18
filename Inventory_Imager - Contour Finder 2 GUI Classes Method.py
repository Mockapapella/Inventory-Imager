#!/usr/bin/env python

import cv2
import numpy as np
import math
import os
import glob
import time
try:
	import tkinter as tk
	from tkinter import ttk
	from tkinter.filedialog import askdirectory
except:
	import Tkinter as tk
	import ttk
	from tkFileDialog import askdirectory
from PIL import Image
from PIL import ImageTk
from operator import itemgetter

import popupmsg

#--End Source Code Info--#

def CannyEdge1(image, filename, blur_value, edge_detector_1_lower_bound, edge_detector_1_upper_bound):
	#--Bolt Image and convert to Gray--#
	img1 = cv2.imread(image)
	img2gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
	img1_resize = cv2.resize(img1, (960, 540))

	#--Edge Threshold--#
	blurred = cv2.GaussianBlur(img1_resize, (blur_value,blur_value), 0)
	canny = cv2.Canny(blurred, edge_detector_1_lower_bound, edge_detector_1_upper_bound) #100,180
	canny_inv = cv2.bitwise_not(canny)

	return canny_inv

def ImageItemCrop(image, filename, padding_N, padding_S, padding_E, padding_W):
	#--Get Only the pixels with a non-white value, append to listxy--#
	rgb_threshold = 255 #125
	listxy = []
	img = Image.fromarray(image)
	rgb = img.convert('RGB')
	for x in range(img.size[0]):
	    for y in range(img.size[1]):
		    r, g, b, = rgb.getpixel((x, y))
		    if r < rgb_threshold and g < rgb_threshold and b < rgb_threshold:
			    coords = (x,y)
			    listxy.append(coords)
	'''Get first and last X value'''
	sorted(listxy,key=itemgetter(0))
	x_low = listxy[0][0] - padding_E #20
	x_high = listxy[-1][0] + padding_W #20
	'''Get first and last Y value'''
	listxy.sort(key=lambda x: x[1])
	y_low = listxy[0][1] - padding_N #20
	y_high = listxy[-1][1] + padding_S #20

	#--Take the coordinates of the square and use them to get the ROI of the original image--#
	filename = cv2.imread(filename)
	filename_resize = cv2.resize(filename, (960, 540))
	crop = filename_resize[int(y_low):int(y_high), int(x_low):int(x_high)]

	return crop

def CannyEdge2(channel, edge_detector_2_lower_bound, edge_detector_2_upper_bound, dilation):

	canny = cv2.Canny(channel, edge_detector_2_lower_bound, edge_detector_2_upper_bound) #10, 20
	dilate = cv2.dilate(canny, np.ones((dilation,dilation), np.uint8)) #4,4

	return dilate;

def findSignificantContours(img, sobel_8u, largest_contour_allowed):
	image, contours, heirarchy = cv2.findContours(sobel_8u, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

	# Find level 1 contours
	level1 = []
	for i, tupl in enumerate(heirarchy[0]):
		# Each array is in format (Next, Prev, First child, Parent)
		# Filter the ones without parent
		if tupl[3] == -1:
			tupl = np.insert(tupl, 0, [i])
			level1.append(tupl)

	# From among them, find the contours with large surface area.
	significant = []
	# If contour isn't covering 5% of total area of image then it probably is too small
	tooSmall = sobel_8u.size * largest_contour_allowed / 100
	for tupl in level1:
		contour = contours[tupl[0]];
		area = cv2.contourArea(contour)
		if area > tooSmall:
			cv2.drawContours(img, [contour], 0, (0,0,0),-1, cv2.LINE_AA, maxLevel=1) #0, -1
			significant.append([contour, area])

	significant.sort(key=lambda x: x[1])
	return [x[0] for x in significant];

def segment(path, blur2, largest_contour_allowed, edge_detector_2_lower_bound, edge_detector_2_upper_bound, dilation):
	#Taken from https://gist.github.com/Munawwar/0efcacfb43827ba3a6bac3356315c419
	#And here http://www.codepasta.com/site/vision/segmentation/

	img = path

	blurred = cv2.GaussianBlur(img, (blur2, blur2), 0) # Remove noise, 7,7

	# Edge operator
	canny = np.max(np.array([CannyEdge2(blurred[:,:, 0], edge_detector_2_lower_bound, edge_detector_2_upper_bound, dilation),
						CannyEdge2(blurred[:,:, 1], edge_detector_2_lower_bound, edge_detector_2_upper_bound, dilation),
						CannyEdge2(blurred[:,:, 2], edge_detector_2_lower_bound, edge_detector_2_upper_bound, dilation)]), axis=0)

	# Noise reduction trick, from http://sourceforge.net/p/octave/image/ci/default/tree/inst/edge.m#l182
	mean = np.mean(canny)

	# Zero any values less than mean. This reduces a lot of noise.
	canny[canny <= mean] = 0;
	canny[canny > 255] = 255;

	sobel_8u = np.asarray(canny, np.uint8)

	# Find contours
	significant = findSignificantContours(img,
										  sobel_8u,
										  largest_contour_allowed)

	# Mask
	mask = canny.copy()
	mask[mask > 0] = 0
	cv2.fillPoly(mask, significant, 255)
	# Invert mask
	mask = np.logical_not(mask)

	#Finally remove the background
	img[mask] = 255;

	return img

def Combination(mask, crop):
	mask_inv = cv2.bitwise_not(mask)
	result = cv2.bitwise_or(crop, mask)
	return result


def SquareImage(image, filename, output_filepath):
	#--Figure out which side of the image is longer--#
	img1 = image
	height = np.size(img1,0)
	width = np.size(img1,1)

	if height > width:
		desired_size = height
	elif width > height:
		desired_size = width
	else:
		pass

	#--Making the image a square--#
	old_size = img1.shape[:2]
	ratio = float(desired_size)/max(old_size)
	new_size = tuple([int(x*ratio) for x in old_size])

	img1 = cv2.resize(img1, (new_size[1], new_size[0]))

	delta_w = desired_size - new_size[1]
	delta_h = desired_size - new_size[0]
	top, bottom = delta_h//2, delta_h-(delta_h//2)
	left, right = delta_w//2, delta_w-(delta_w//2)

	color = [255,255,255]
	new_img1 = cv2.copyMakeBorder(img1, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)

	return new_img1

def run_the_code(input_filepath,
				 output_filepath,
				 square_checkbox,
				 largest_contour_allowed,
				 dilation,
				 blur1,
				 blur2,
				 edge_detector_1_lower_bound,
				 edge_detector_1_upper_bound,
				 edge_detector_2_lower_bound,
				 edge_detector_2_upper_bound,
				 padding_N,
				 padding_S,
				 padding_W,
				 padding_E):

	if input_filepath == "":
		input_filepath_error()
		return
	if blur1 %2 == 0 or blur2 %2 == 0:
		blur_error()
		return
	i=1
	for filename in glob.glob(os.path.join(input_filepath, "*.jpg")):
		try:
			print("Finding, cropping, and optimizing image number {}".format(i))
			i+=1
			#Apply canny edge detection
			canny_inv = CannyEdge1(filename,
											   filename,
											   blur1,
											   edge_detector_1_lower_bound,
											   edge_detector_1_upper_bound)
			#Crop image to item size
			img_crop = ImageItemCrop(canny_inv,
												 filename,
												 padding_N,
												 padding_S,
												 padding_E,
												 padding_W)
			img_crop_copy = img_crop.copy()
			mask = segment(img_crop,
									   blur2,
									   largest_contour_allowed,
									   edge_detector_2_lower_bound,
									   edge_detector_2_upper_bound,
									   dilation)
			unsquare_image = Combination(mask,
													 img_crop_copy)
			if square_checkbox == 1:
				square_image = SquareImage(unsquare_image,
														   filename,
														   output_filepath)

				#--Save Processed Image--#
				filename_array = filename
				filename_array = filename.split('\\')
				filename_array_item = filename_array[1]

				#--Write File--#
				'''
				If no output directory is specified, make one in the current directory
				'''
				if output_filepath == "":
					if not os.path.exists("Output/"):
						os.mkdir("Output/")
					dirname = "Output"
					cv2.imwrite(os.path.join(dirname, filename_array_item), square_image)
				else:
					cv2.imwrite(os.path.join(output_filepath, filename_array_item), square_image)

				#--Update the images on display in the window--#
				lbl1.load(Image.open(filename))

				b,g,r = cv2.split(square_image)
				square_image = cv2.merge((r,g,b))
				square_image = Image.fromarray(square_image)
				lbl2.load(square_image)

			elif square_checkbox == 0:
				#--Save Processed Image--#
				filename_array = filename
				filename_array = filename.split('\\')
				filename_array_item = filename_array[1]

				#--Write File--#
				'''
				If no output directory is specified, make one in the current directory
				'''
				if output_filepath == "":
					if not os.path.exists("Output/"):
						os.mkdir("Output/")
					dirname = "Output"
					cv2.imwrite(os.path.join(dirname, filename_array_item), unsquare_image)
				else:
					cv2.imwrite(os.path.join(output_filepath, filename_array_item), unsquare_image)


				#--Update the images on display in the window--#
				lbl1.load(Image.open(filename))

				b,g,r = cv2.split(unsquare_image)
				unsquare_image = cv2.merge((r,g,b))
				unsquare_image = Image.fromarray(unsquare_image)
				lbl2.load(unsquare_image)

		except Exception as e:
			print(e)
	finished_processing()

def run_the_code_once(input_filepath,
				 	  output_filepath,
				 	  square_checkbox,
				 	  largest_contour_allowed,
				 	  dilation,
				 	  blur1,
				 	  blur2,
				 	  edge_detector_1_lower_bound,
				 	  edge_detector_1_upper_bound,
				 	  edge_detector_2_lower_bound,
				 	  edge_detector_2_upper_bound,
				 	  padding_N,
				 	  padding_S,
				 	  padding_W,
				 	  padding_E):

	if input_filepath == "":
		popupmsg.input_filepath_error()
		return
	if blur1 %2 == 0 or blur2 %2 == 0:
		popupmsg.blur_error()
		return
	i=1
	for filename in glob.glob(os.path.join(input_filepath, "*.jpg")):
		try:
			print("Finding, cropping, and optimizing image number {}".format(i))
			i+=1
			#Apply canny edge detection
			canny_inv = CannyEdge1(filename,
											   filename,
											   blur1,
											   edge_detector_1_lower_bound,
											   edge_detector_1_upper_bound)
			#Crop image to item size
			img_crop = ImageItemCrop(canny_inv,
												 filename,
												 padding_N,
												 padding_S,
												 padding_E,
												 padding_W)
			img_crop_copy = img_crop.copy()
			mask = segment(img_crop,
									   blur2,
									   largest_contour_allowed,
									   edge_detector_2_lower_bound,
									   edge_detector_2_upper_bound,
									   dilation)
			unsquare_image = Combination(mask,
													 img_crop_copy)
			if square_checkbox == 1:
				square_image = SquareImage(unsquare_image,
														   filename,
														   output_filepath)

				#--Save Processed Image--#
				filename_array = filename
				filename_array = filename.split('\\')
				filename_array_item = filename_array[1]

				#--Write File--#
				'''
				If no output directory is specified, make one in the current directory
				'''
				if output_filepath == "":
					if not os.path.exists("Output/"):
						os.mkdir("Output/")
					dirname = "Output"
					cv2.imwrite(os.path.join(dirname, filename_array_item), square_image)
				else:
					cv2.imwrite(os.path.join(output_filepath, filename_array_item), square_image)

				#--Update the images on display in the window--#
				lbl1.load(Image.open(filename))

				b,g,r = cv2.split(square_image)
				square_image = cv2.merge((r,g,b))
				square_image = Image.fromarray(square_image)
				lbl2.load(square_image)

			elif square_checkbox == 0:
				#--Save Processed Image--#
				filename_array = filename
				filename_array = filename.split('\\')
				filename_array_item = filename_array[1]

				#--Write File--#
				'''
				If no output directory is specified, make one in the current directory
				'''
				if output_filepath == "":
					if not os.path.exists("Output/"):
						os.mkdir("Output/")
					dirname = "Output"
					cv2.imwrite(os.path.join(dirname, filename_array_item), unsquare_image)
				else:
					cv2.imwrite(os.path.join(output_filepath, filename_array_item), unsquare_image)


				#--Update the images on display in the window--#
				lbl1.load(Image.open(filename))

				b,g,r = cv2.split(unsquare_image)
				unsquare_image = cv2.merge((r,g,b))
				unsquare_image = Image.fromarray(unsquare_image)
				lbl2.load(unsquare_image)
			break
		except Exception as e:
			print(e)
			raise
	popupmsg.finished_processing()

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
ttk.Button(master, text='Activate', command=lambda: run_the_code(e1.get(),
																 e2.get(),
																 checkVar1.get(),
																 int(scaleVar1.get()),
																 int(scaleVar2.get()),
																 int(scaleVar3.get()),
																 int(scaleVar4.get()),
																 int(scaleVar5.get()),
																 int(scaleVar6.get()),
																 int(scaleVar7.get()),
																 int(scaleVar8.get()),
																 int(scaleVar9.get()),
																 int(scaleVar10.get()),
																 int(scaleVar11.get()),
																 int(scaleVar12.get()))).grid(row=24, column=2, sticky=tk.E, pady=4, padx=4)
btn = ttk.Button(master, text='Preview', command=lambda: run_the_code_once(
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
	int(padding_w.get())))
btn.grid(row=24, column=3, sticky='ew', pady=4, columnspan=2)

#Images
master.grid_columnconfigure(7, weight=1)

ttk.Separator(master, orient=tk.VERTICAL).grid(row=2, column=6, rowspan=23, sticky='ns')
ttk.Separator(master, orient=tk.HORIZONTAL).grid(row=11, column=6, columnspan=24, sticky='ew')

class Mockapapella(tk.Label):
	''' a Label that resizes the contained image'''
	def __init__(self, master=None, **kwargs):
		tk.Label.__init__(self, master, **kwargs)
		self.original_image = None
		self.photoimage = None
		self.bind('<Configure>', self.resize_and_display)

	def load(self, image):
		''' load an image
		image: is a PIL Image instance'''
		self.original_image = image # this replaces any reference to the previous image, to allow garbage collection
		image_width, image_height = self.original_image.size
		self.resize_and_display()

	def resize_and_display(self, event=None):
		if self.original_image is None:
			return # nothing to do

		# easy resize code lets PIL do the work with the thumbnail method
		new_img = self.original_image.copy()
		new_img.thumbnail((self.winfo_width(), self.winfo_height()))
		self.photoimage = ImageTk.PhotoImage(new_img) # allows garbage collection of the old photoimage
		self.config(image=self.photoimage)

lbl1 = Mockapapella(master)
lbl1.grid(row=3, column=7, sticky='nsew', pady=4, padx=4, rowspan=8, columnspan=23)

lbl2 = Mockapapella(master)
lbl2.grid(row=13, column=7, sticky='nsew', pady=4, padx=4, rowspan=10, columnspan=23)

master.geometry("960x600")
master.mainloop()
