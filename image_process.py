#!/usr/bin/env python

import cv2
import numpy as np
import math
import os
import glob
from PIL import Image, ImageTk
from operator import itemgetter
from functools import partial

import popupmsg

def CannyEdge1(image, filename, blur_value, edge_detector_1_lower_bound, edge_detector_1_upper_bound):
	#--Read in the Image--#
	img1 = cv2.imread(image)
	img1_resize = cv2.resize(img1, (960, 540))
	#--Edge Threshold--#
	blurred = cv2.GaussianBlur(img1_resize, (blur_value,blur_value), 0) #Replace img1 with img1_resize to process faster
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
	crop = filename_resize[int(y_low):int(y_high), int(x_low):int(x_high)] #Replace filename with filename_resize to process faster
	return crop


def CannyEdge2(channel, edge_detector_2_lower_bound, edge_detector_2_upper_bound, dilation):
	canny = cv2.Canny(channel, edge_detector_2_lower_bound, edge_detector_2_upper_bound) #10, 20
	dilate = cv2.dilate(canny, np.ones((dilation,dilation), np.uint8)) #4,4
	return dilate;


def findSignificantContours(img, sobel_8u, smallest_contour_allowed):
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
	tooSmall = sobel_8u.size * smallest_contour_allowed / 100
	for tupl in level1:
		contour = contours[tupl[0]];
		area = cv2.contourArea(contour)
		if area > tooSmall:
			cv2.drawContours(img, [contour], 0, (0,0,0),-1, cv2.LINE_AA, maxLevel=1) #0, -1
			significant.append([contour, area])
	significant.sort(key=lambda x: x[1])
	return [x[0] for x in significant];


def segment(path, blur2, smallest_contour_allowed, edge_detector_2_lower_bound, edge_detector_2_upper_bound, dilation):
	#Taken from https://gist.github.com/Munawwar/0efcacfb43827ba3a6bac3356315c419
	#And here http://www.codepasta.com/site/vision/segmentation/
	img = path
	blurred = cv2.GaussianBlur(img, (blur2, blur2), 0) # Remove noise, 7,7
	# Edge operator
	canny = np.max(np.array([CannyEdge2(blurred[:,:, 0], edge_detector_2_lower_bound, edge_detector_2_upper_bound, dilation),
						CannyEdge2(blurred[:,:, 1], edge_detector_2_lower_bound, edge_detector_2_upper_bound, dilation),
						CannyEdge2(blurred[:,:, 2], edge_detector_2_lower_bound, edge_detector_2_upper_bound, dilation)]), axis=0)
	# Noise reduction trick, from http://sourceforge.net/p/octave/image/ci/default/tree/inst/edge.m#l182
	mean = np.mean(blurred)
	# Zero any values less than mean. This reduces a lot of noise.
	canny[canny <= mean] = 0;
	canny[canny > 255] = 255;
	sobel_8u = np.asarray(canny, np.uint8)
	# Find contours
	significant = findSignificantContours(img,
										  sobel_8u,
										  smallest_contour_allowed)
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


def SquareImage(image):
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


def log(queue, *text):
	data = ' '.join(map(str, text))
	print(data)
	if queue:
		queue.put(data)


def run_the_code(input_filepath,
				 output_filepath,
				 square_checkbox,
				 smallest_contour_allowed,
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
				 padding_E,
				 queue=None,
				 status_q=None,
				 preview=False):

	slog = partial(log, status_q)
	if input_filepath == "":
		popupmsg.input_filepath_error()
		return
	if blur1 %2 == 0 or blur2 %2 == 0:
		popupmsg.blur_error()
		return
	files = glob.glob(os.path.join(input_filepath, "*.jpg"))
	if preview:
		del files[1:] # preview just uses the first image; remove the rest from the list
	for i, filename in enumerate(files, 1):
		fn = os.path.basename(filename)
		num = "({}/{})".format(i, len(files))
		try:
			slog(fn, num, "- Apply canny edge detection")
			canny_inv = CannyEdge1(filename,
								   filename,
								   blur1,
								   edge_detector_1_lower_bound,
								   edge_detector_1_upper_bound)
			slog(fn, num, "- Crop image to item size")
			img_crop = ImageItemCrop(canny_inv,
									 filename,
									 padding_N,
									 padding_S,
									 padding_E,
									 padding_W)
			img_crop_copy = img_crop.copy()
			mask = segment(img_crop,
						   blur2,
						   smallest_contour_allowed,
						   edge_detector_2_lower_bound,
						   edge_detector_2_upper_bound,
						   dilation)
			unsquare_image = Combination(mask,
										 img_crop_copy)
			slog(fn, num, "- saving")
			if square_checkbox == 1:
				new_image = SquareImage(unsquare_image)
			else:
				new_image = unsquare_image

			#--Save Processed Image--#
			'''
			If no output directory is specified, make one in the current directory
			'''
			if output_filepath == "" or output_filepath == "Output":
				if not os.path.exists("Output/"):
					os.mkdir("Output/")
				dirname = "Output"
				cv2.imwrite(os.path.join(dirname, fn), new_image)
			else:
				cv2.imwrite(os.path.join(output_filepath, fn), new_image)

			b,g,r = cv2.split(new_image)
			new_image = cv2.merge((r,g,b))
			new_image = Image.fromarray(new_image)

			#--Update the images on display in the window--#
			if queue:
				queue.put((Image.open(filename), new_image))
		except Exception as e:
			slog("ERROR:", fn, num, e)
	if queue:
		queue.put('finished')

