import cv2
import numpy as np
import math
import os
import glob
import time
import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter.filedialog import askdirectory
from PIL import Image
from PIL import ImageTk
from operator import itemgetter

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
			break
		except Exception as e:
			print(e)
	finished_processing()

#--Tkinter--#
master = tk.Tk()
master.iconbitmap("Logo.ico")
master.wm_title("Inventory Imager")

#Functions
def popupmsg_Blur_1():
	popup = tk.Tk()
	popup.iconbitmap("Logo.ico")
	msg = "Change how much to blur the image before canny edge detection is applied."
	popup.wm_title("Blur 1 Information")
	label = ttk.Label(popup, text=msg)
	label.pack(side="top", pady=10, padx=10)
	B1 = ttk.Button(popup, text="Okay", command=popup.destroy)
	B1.pack(pady=10, padx=10)
	popup.mainloop()

def popupmsg_Edge_Detector_1():
	popup = tk.Tk()
	popup.iconbitmap("Logo.ico")
	msg = "Change how accurately the object is detected and cropped."
	popup.wm_title("Edge Detector 1 Information")
	label = ttk.Label(popup, text=msg)
	label.pack(side="top", pady=10, padx=10)
	B1 = ttk.Button(popup, text="Okay", command=popup.destroy)
	B1.pack(pady=10, padx=10)
	popup.mainloop()
	
def popupmsg_padding():
	popup = tk.Tk()
	popup.iconbitmap("Logo.ico")
	msg = "Change how much white space is around the item in the final image."
	popup.wm_title("Padding Information")
	label = ttk.Label(popup, text=msg)
	label.pack(side="top", pady=10, padx=10)
	B1 = ttk.Button(popup, text="Okay", command=popup.destroy)
	B1.pack(pady=10, padx=10)
	popup.mainloop()
	
def popupmsg_Edge_Detector_2():
	popup = tk.Tk()
	popup.iconbitmap("Logo.ico")
	msg = "Change how accurately the fine lines of the object are detected."
	popup.wm_title("Edge Detector 2 Information")
	label = ttk.Label(popup, text=msg)
	label.pack(side="top", pady=10, padx=10)
	B1 = ttk.Button(popup, text="Okay", command=popup.destroy)
	B1.pack(pady=10, padx=10)
	popup.mainloop()
	
def popupmsg_dilate():
	popup = tk.Tk()
	popup.iconbitmap("Logo.ico")
	msg = "Change how many pixels to inflate each contour point by."
	popup.wm_title("Edge Detector 1 Information")
	label = ttk.Label(popup, text=msg)
	label.pack(side="top", pady=10, padx=10)
	B1 = ttk.Button(popup, text="Okay", command=popup.destroy)
	B1.pack(pady=10, padx=10)
	popup.mainloop()
	
def popupmsg_contour():
	popup = tk.Tk()
	popup.iconbitmap("Logo.ico")
	msg = "Change how much area in relation to the total image size the contour must encompass to be considered a valid contour."
	popup.wm_title("Edge Detector 1 Information")
	label = ttk.Label(popup, text=msg)
	label.pack(side="top", pady=10, padx=10)
	B1 = ttk.Button(popup, text="Okay", command=popup.destroy)
	B1.pack(pady=10, padx=10)
	popup.mainloop()
	
def popupmsg_Blur_2():
	popup = tk.Tk()
	popup.iconbitmap("Logo.ico")
	msg = "How much to blur the initial image."
	popup.wm_title("Edge Detector 1 Information")
	label = ttk.Label(popup, text=msg)
	label.pack(side="top", pady=10, padx=10)
	B1 = ttk.Button(popup, text="Okay", command=popup.destroy)
	B1.pack(pady=10, padx=10)
	popup.mainloop()

def input_filepath_error():
	popup = tk.Tk()
	popup.iconbitmap("Warning.ico")
	msg = "Specify Input Folder"
	popup.wm_title("Error")
	label = ttk.Label(popup, text=msg)
	label.pack(pady=10, padx=10)
	B1 = ttk.Button(popup, text="Okay", command=popup.destroy)
	B1.pack(pady=10, padx=10)
	popup.geometry("200x100")
	popup.mainloop()

def blur_error():
	popup = tk.Tk()
	popup.iconbitmap("Warning.ico")
	msg = "One of your blur variables is even! Change it to an odd number to continue."
	popup.wm_title("Error")
	label = ttk.Label(popup, text=msg)
	label.pack(pady=10, padx=10)
	B1 = ttk.Button(popup, text="Okay", command=popup.destroy)
	B1.pack(pady=10, padx=10)
	popup.mainloop()

def finished_processing():
	popup = tk.Tk()
	popup.iconbitmap("Logo.ico")
	msg = "Image processing completed"
	popup.wm_title("Finish Message")
	label = ttk.Label(popup, text=msg)
	label.pack(side=TOP, pady=10, padx=10)
	B1 = ttk.Button(popup, text="Okay", command=popup.destroy)
	B1.pack(pady=10, padx=10)
	popup.geometry("200x100")
	popup.mainloop()

#https://stackoverflow.com/questions/26598010/how-do-i-create-a-button-in-python-tkinter-to-increase-integer-variable-by-1-and
#Add 1 value to the scale every time a button is clicked
def onClick_Add1(event=None):
	scaleVar1.set(scaleVar1.get()+1)

def onClick_Add2(event=None):
	scaleVar2.set(scaleVar2.get()+1)

def onClick_Add3(event=None):
	scaleVar3.set(scaleVar3.get()+1)

def onClick_Add4(event=None):
	scaleVar4.set(scaleVar4.get()+1)

def onClick_Add5(event=None):
	scaleVar5.set(scaleVar5.get()+1)

def onClick_Add6(event=None):
	scaleVar6.set(scaleVar6.get()+1)

def onClick_Add7(event=None):
	scaleVar7.set(scaleVar7.get()+1)

def onClick_Add8(event=None):
	scaleVar8.set(scaleVar8.get()+1)

def onClick_Add9(event=None):
	scaleVar9.set(scaleVar9.get()+1)

def onClick_Add10(event=None):
	scaleVar10.set(scaleVar10.get()+1)

def onClick_Add11(event=None):
	scaleVar11.set(scaleVar11.get()+1)

def onClick_Add12(event=None):
	scaleVar12.set(scaleVar12.get()+1)

#Subtract 1 value from the scale every time a button is clicked
def onClick_Subtract1(event=None):
	scaleVar1.set(scaleVar1.get()-1)

def onClick_Subtract2(event=None):
	scaleVar2.set(scaleVar2.get()-1)

def onClick_Subtract3(event=None):
	scaleVar3.set(scaleVar3.get()-1)

def onClick_Subtract4(event=None):
	scaleVar4.set(scaleVar4.get()-1)

def onClick_Subtract5(event=None):
	scaleVar5.set(scaleVar5.get()-1)

def onClick_Subtract6(event=None):
	scaleVar6.set(scaleVar6.get()-1)

def onClick_Subtract7(event=None):
	scaleVar7.set(scaleVar7.get()-1)

def onClick_Subtract8(event=None):
	scaleVar8.set(scaleVar8.get()-1)

def onClick_Subtract9(event=None):
	scaleVar9.set(scaleVar9.get()-1)

def onClick_Subtract10(event=None):
	scaleVar10.set(scaleVar10.get()-1)

def onClick_Subtract11(event=None):
	scaleVar11.set(scaleVar11.get()-1)

def onClick_Subtract12(event=None):
	scaleVar12.set(scaleVar12.get()-1)

def reset_sliders():
	scaleVar1.set(5)
	scaleVar2.set(3)
	scaleVar3.set(7)
	scaleVar4.set(7)
	scaleVar5.set(100)
	scaleVar6.set(180)
	scaleVar7.set(20)
	scaleVar8.set(40)
	scaleVar9.set(5)
	scaleVar10.set(5)
	scaleVar11.set(5)
	scaleVar12.set(5)

def input_directory():
	input_directory = askdirectory(initialdir = os.getcwd(),title = "Select file")
	e1.delete(0, END)
	e1.insert(0, input_directory)

def output_directory():
	output_directory = askdirectory(initialdir = os.getcwd(),title = "Select file")
	e2.delete(0, END)
	e2.insert(0, output_directory)

#Rounds the "largest contour allowed" value to the nearest whole number
def round_number1():
	scaleVal1.set(round(scaleVal1.get(), 2))

#Rounds the dilate value to the nearest whole number
def round_number2():
	scaleVal2.set(round(scaleVal2.get(), 2))

#Rounds the blur1 value to the nearest odd number
def round_number3(previous):
	global previous_number1
	scaleVal3_int = scaleVal3.get()
	if previous < scaleVal3.get():
		scaleVal3.set(round(scaleVal3_int + 1))
	elif scaleVal3_int %2!= 1:
		scaleVal3.set(round(scaleVal3_int - 1))
	elif scaleVal3_int %2!= 0:
		scaleVal3.set(round(scaleVal3_int))
	previous_number1 = scaleVal3.get()


def define_scale1():
	return scaleVal3.get()

#Rounds the blur2 value to the nearest odd number
def round_number4(previous):
	global previous_number2
	scaleVal4_int = scaleVal4.get()
	if previous < scaleVal4.get():
		scaleVal4.set(round(scaleVal4_int + 1))
	elif scaleVal4_int %2!= 1:
		scaleVal4.set(round(scaleVal4_int - 1))
	elif scaleVal4_int %2!= 0:
		scaleVal4.set(round(scaleVal4_int))
	previous_number2 = scaleVal4.get()

def define_scale2():
	return scaleVal4.get()

#Rounds the "Edge Detector 1" values to the nearest whole number
def round_number5():
	scaleVal5.set(round(scaleVal5.get(), 2))
	
def round_number6():
	scaleVal6.set(round(scaleVal6.get(), 2))

#Rounds the "Edge Detector 2" values to the nearest whole number	
def round_number7():
	scaleVal7.set(round(scaleVal7.get(), 2))
	
def round_number8():
	scaleVal8.set(round(scaleVal8.get(), 2))

#Rounds the "Padding" values to the nearest whole number	
def round_number9():
	scaleVal9.set(round(scaleVal9.get(), 2))
	
def round_number10():
	scaleVal10.set(round(scaleVal10.get(), 2))
	
def round_number11():
	scaleVal11.set(round(scaleVal11.get(), 2))
	
def round_number12():
	scaleVal12.set(round(scaleVal12.get(), 2))

#Menu
'''
Info Menu
'''
menubar = Menu(master)
Info = tk.Menu(menubar, tearoff=0)
Info.add_command(label="Largest Contour Allowed", command=lambda: popupmsg_contour())
Info.add_command(label="Dilate", command=lambda: popupmsg_dilate())
Info.add_command(label="Blur 1", command=lambda: popupmsg_Blur_1())
Info.add_command(label="Blur 2", command=lambda: popupmsg_Blur_2())
Info.add_command(label="Edge Detector 1", command=lambda: popupmsg_Edge_Detector_1())
Info.add_command(label="Edge Detector 2", command=lambda: popupmsg_Edge_Detector_2())
Info.add_command(label="Padding", command=lambda: popupmsg_padding())
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
ttk.Button(master, text="Input", command=lambda: input_directory()).grid(row=0, column=29, sticky=NSEW)
e1 = Entry(master)
e1.grid(row=0, column=0, pady=4, padx=4, sticky=EW, columnspan=29)

#Output
ttk.Button(master, text="Output", command=lambda: output_directory()).grid(row=1, column=29, sticky=NSEW)
e2 = Entry(master)
e2.grid(row=1, column=0, pady=4, padx=4, sticky=EW, columnspan=29)

#Layer under input and output
checkVar1 = IntVar()
checkVar1.set(1)
checkVal1 = Checkbutton(master, text="Make Square", variable=checkVar1)
checkVal1.grid(row=4, column=0, sticky=EW)
Label(master, text="Options").grid(row=4, column=2)
Label(master, text="Current").grid(row=4, column=5)
ttk.Button(master, text="Set Defaults", command=lambda: reset_sliders()).grid(row=4, column=4)

master.grid_columnconfigure(2, weight=1)

#Largest Contours Allowed
master.grid_rowconfigure(5, weight=1)
Label(master, text="Largest Contour Allowed (Default: 5)").grid(row=5, column=2, sticky=S)
ttk.Button(master, text="-", command=lambda: onClick_Subtract1()).grid(row=6, column=0, sticky=E)
Label(master, text="1").grid(row=6, column=1, sticky=E)
scaleVal1 = tk.IntVar()
scaleVal1.set(5)
scaleVar1 = ttk.Scale(master, from_="1", to="100", orient=HORIZONTAL, variable=scaleVal1, command=lambda _: round_number1())
scaleVar1.grid(row=6, column=2, stick=EW, ipadx=0, ipady=0)
Label(master, text="100").grid(row=6, column=3)
ttk.Button(master, text="+", command=lambda: onClick_Add1()).grid(row=6, column=4)
Label(master, textvariable=scaleVal1).grid(row=6, column=5)

#Dilate
master.grid_rowconfigure(7, weight=1)
Label(master, text="Dilate (Default: 3)").grid(row=7, column=2, sticky=S)
ttk.Button(master, text="-", command=lambda: onClick_Subtract2()).grid(row=8, column=0, sticky=E)
Label(master, text="1").grid(row=8, column=1, sticky=E)
scaleVal2 = tk.IntVar()
scaleVal2.set(3)
scaleVar2 = ttk.Scale(master, from_="1", to="20", orient=HORIZONTAL, variable=scaleVal2, command=lambda _: round_number2())
scaleVar2.grid(row=8, column=2, stick=EW, ipadx=0, ipady=0)
Label(master, text="20").grid(row=8, column=3)
ttk.Button(master, text="+", command=lambda: onClick_Add2()).grid(row=8, column=4)
Label(master, textvariable=scaleVal2).grid(row=8, column=5)

#Blurred 1
master.grid_rowconfigure(9, weight=1)
Label(master, text="Blur 1 (Default: 7)").grid(row=9, column=2, sticky=S)
ttk.Button(master, text="-", command=lambda: onClick_Subtract3()).grid(row=10, column=0, stick=E)
Label(master, text="1").grid(row=10, column=1, sticky=E)
scaleVal3 = tk.IntVar()
scaleVal3.set(7)
'''
This variable must be global so the blur1 scale has some way of knowing what value it previously held
'''
global previous_number1
previous_number1 = define_scale1()
scaleVar3 = ttk.Scale(master, from_="1", to="99", orient=HORIZONTAL, variable=scaleVal3, command=lambda _: round_number3(previous_number1))
scaleVar3.grid(row=10, column=2, stick=EW, ipadx=0, ipady=0)
Label(master, text="99").grid(row=10, column=3)
ttk.Button(master, text="+", command=lambda: onClick_Add3()).grid(row=10, column=4)
Label(master, textvariable=scaleVal3).grid(row=10, column=5)

#Blurred 2
master.grid_rowconfigure(11, weight=1)
Label(master, text="Blur 2 (Default: 7)").grid(row=11, column=2, sticky=S)
ttk.Button(master, text="-", command=lambda: onClick_Subtract4()).grid(row=12, column=0, sticky=E)
Label(master, text="1").grid(row=12, column=1, sticky=E)
scaleVal4 = tk.IntVar()
scaleVal4.set(7)
'''
This variable must be global so the blur2 scale has some way of knowing what value it previously held
'''
global previous_number2
previous_number2 = define_scale2()
scaleVar4 = ttk.Scale(master, from_="1", to="99", orient=HORIZONTAL, variable=scaleVal4, command=lambda _: round_number4(previous_number2))
scaleVar4.grid(row=12, column=2, stick=EW, ipadx=0, ipady=0)
Label(master, text="99").grid(row=12, column=3)
ttk.Button(master, text="+", command=lambda: onClick_Add4()).grid(row=12, column=4)
Label(master, textvariable=scaleVal4).grid(row=12, column=5)

#Edge Detector 1
master.grid_rowconfigure(13, weight=1)
Label(master, text="Edge Detector 1 (Default: 100,180)").grid(row=13, column=2, sticky=S)
ttk.Button(master, text="-", command=lambda: onClick_Subtract5()).grid(row=14, column=0, sticky=E)
Label(master, text="1").grid(row=14, column=1, sticky=E)
scaleVal5 = tk.IntVar()
scaleVal5.set(100)
scaleVar5 = ttk.Scale(master, from_="1", to="300", orient=HORIZONTAL, variable=scaleVal5, command=lambda _: round_number5())
scaleVar5.grid(row=14, column=2, stick=EW, ipadx=0, ipady=0)
Label(master, text="300").grid(row=14, column=3)
ttk.Button(master, text="+", command=lambda: onClick_Add5()).grid(row=14, column=4)
Label(master, textvariable=scaleVal5).grid(row=14, column=5)

ttk.Button(master, text="-", command=lambda: onClick_Subtract6()).grid(row=15, column=0, sticky=E)
Label(master, text="1").grid(row=15, column=1, sticky=E)
scaleVal6 = tk.IntVar()
scaleVal6.set(180)
scaleVar6 = ttk.Scale(master, from_="1", to="300", orient=HORIZONTAL, variable=scaleVal6, command=lambda _: round_number6())
scaleVar6.grid(row=15, column=2, stick=EW, ipadx=0, ipady=0)
Label(master, text="300").grid(row=15, column=3)
ttk.Button(master, text="+", command=lambda: onClick_Add6()).grid(row=15, column=4)
Label(master, textvariable=scaleVal6).grid(row=15, column=5)

#Edge Detector 2
master.grid_rowconfigure(16, weight=1)
Label(master, text="Edge Detector 2 (Default: 20,40)").grid(row=16, column=2, sticky=S)
ttk.Button(master, text="-", command=lambda: onClick_Subtract7()).grid(row=17, column=0, sticky=E)
Label(master, text="1").grid(row=17, column=1, sticky=E)
scaleVal7 = tk.IntVar()
scaleVal7.set(20)
scaleVar7 = ttk.Scale(master, from_="1", to="100", orient=HORIZONTAL, variable=scaleVal7, command=lambda _: round_number7())
scaleVar7.grid(row=17, column=2, stick=EW, ipadx=0, ipady=0)
Label(master, text="100").grid(row=17, column=3)
ttk.Button(master, text="+", command=lambda: onClick_Add7()).grid(row=17, column=4)
Label(master, textvariable=scaleVal7).grid(row=17, column=5)

ttk.Button(master, text="-", command=lambda: onClick_Subtract8()).grid(row=18, column=0, sticky=E)
Label(master, text="1").grid(row=18, column=1, sticky=E)
scaleVal8 = tk.IntVar()
scaleVal8.set(40)
scaleVar8 = ttk.Scale(master, from_="1", to="100", orient=HORIZONTAL, variable=scaleVal8, command=lambda _: round_number8())
scaleVar8.grid(row=18, column=2, stick=EW, ipadx=0, ipady=0)
Label(master, text="100").grid(row=18, column=3)
ttk.Button(master, text="+", command=lambda: onClick_Add8()).grid(row=18, column=4)
Label(master, textvariable=scaleVal8).grid(row=18, column=5)

#Final Image Padding
master.grid_rowconfigure(19, weight=1)
Label(master, text="Padding (Default: N5,S5,E5,W5)").grid(row=19, column=2, sticky=S)
ttk.Button(master, text="-", command=lambda: onClick_Subtract9()).grid(row=20, column=0, sticky=E)
Label(master, text="0").grid(row=20, column=1, sticky=E)
scaleVal9 = tk.IntVar()
scaleVal9.set(5)
scaleVar9 = ttk.Scale(master, from_="0", to="40", orient=HORIZONTAL, variable=scaleVal9, command=lambda _: round_number9())
scaleVar9.grid(row=20, column=2, stick=EW, ipadx=0, ipady=0)
Label(master, text="40").grid(row=20, column=3)
ttk.Button(master, text="+", command=lambda: onClick_Add9()).grid(row=20, column=4)
Label(master, textvariable=scaleVal9).grid(row=20, column=5)

ttk.Button(master, text="-", command=lambda: onClick_Subtract10()).grid(row=21, column=0, sticky=E)
Label(master, text="0").grid(row=21, column=1, sticky=E)
scaleVal10 = tk.IntVar()
scaleVal10.set(5)
scaleVar10 = ttk.Scale(master, from_="0", to="40", orient=HORIZONTAL, variable=scaleVal10, command=lambda _: round_number10())
scaleVar10.grid(row=21, column=2, stick=EW, ipadx=0, ipady=0)
Label(master, text="40").grid(row=21, column=3)
ttk.Button(master, text="+", command=lambda: onClick_Add10()).grid(row=21, column=4)
Label(master, textvariable=scaleVal10).grid(row=21, column=5)

ttk.Button(master, text="-", command=lambda: onClick_Subtract11()).grid(row=22, column=0, sticky=E)
Label(master, text="0").grid(row=22, column=1, sticky=E)
scaleVal11 = tk.IntVar()
scaleVal11.set(5)
scaleVar11 = ttk.Scale(master, from_="0", to="40", orient=HORIZONTAL, variable=scaleVal11, command=lambda _: round_number11())
scaleVar11.grid(row=22, column=2, stick=EW, ipadx=0, ipady=0)
Label(master, text="40").grid(row=22, column=3)
ttk.Button(master, text="+", command=lambda: onClick_Add11()).grid(row=22, column=4)
Label(master, textvariable=scaleVal11).grid(row=22, column=5)

ttk.Button(master, text="-", command=lambda: onClick_Subtract12()).grid(row=23, column=0, sticky=E)
Label(master, text="0").grid(row=23, column=1, sticky=E)
scaleVal12 = tk.IntVar()
scaleVal12.set(5)
scaleVar12 = ttk.Scale(master, from_="0", to="40", orient=HORIZONTAL, variable=scaleVal12, command=lambda _: round_number12())
scaleVar12.grid(row=23, column=2, stick=EW, ipadx=0, ipady=0)
Label(master, text="40").grid(row=23, column=3)
ttk.Button(master, text="+", command=lambda: onClick_Add12()).grid(row=23, column=4)
Label(master, textvariable=scaleVal12).grid(row=23, column=5)

#Lower Buttons
ttk.Button(master, text='Quit', command=master.quit).grid(row=24, column=0, sticky=EW)
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
																 int(scaleVar12.get()))).grid(row=24, column=2, sticky=E, pady=4, padx=4)
ttk.Button(master, text='Preview', command=lambda: run_the_code_once(e1.get(),
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
																	 int(scaleVar12.get()))).grid(row=24, column=3, sticky=EW, pady=4, columnspan=2)

#Images
master.grid_columnconfigure(7, weight=1)

ttk.Separator(master, orient=VERTICAL).grid(row=2, column=6, rowspan=23, sticky=NS)
ttk.Separator(master, orient=HORIZONTAL).grid(row=11, column=6, columnspan=24, sticky=EW)

class Mockapapella1(tk.Label):
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


lbl1 = Mockapapella1()
lbl1.grid(row=3, column=7, sticky=N, pady=4, padx=4, rowspan=8, columnspan=23)

class Mockapapella2(tk.Label):
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

lbl2 = Mockapapella2()
lbl2.grid(row=13, column=7, sticky=N, pady=4, padx=4, rowspan=10, columnspan=23)

master.geometry("960x600")
mainloop()
