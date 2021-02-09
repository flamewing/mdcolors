#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013-2021  Flamewing <flamewing.sonic@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from gimpfu import gimp
from gimpfu import pdb
from gimpfu import register
from gimpfu import PF_IMAGE
from gimpfu import PF_DRAWABLE
from gimpfu import PF_RADIO
from gimpfu import PF_BOOL
from gimpfu import main

import sys
import os
# extend the python path to include the script's directory
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from enum import IntEnum

class ColorMode(IntEnum):
	SonMapEd = 1
	SKCollect = 2
	Measured = 3

class FadeMode(IntEnum):
	CurrentToBlack = 1
	BlackToCurrent = 2
	CurrentToWhite = 3
	WhiteToCurrent = 4

# Normal mode valid colors per color mode
lutValsSME_def = [0x00, 0x20, 0x40, 0x60, 0x80, 0xA0, 0xC0, 0xE0]
lutValsSKC_def = [0x00, 0x22, 0x44, 0x66, 0x88, 0xAA, 0xCC, 0xEE]
lutValsVDP_def = [0x00, 0x34, 0x57, 0x74, 0x90, 0xAC, 0xCE, 0xFF]

# Shadow/highlight mode valid colors per color mode
lutValsSME_shl = [0x00, 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80, 0x90, 0xA0, 0xB0, 0xC0, 0xD0, 0xE0]
lutValsSKC_shl = [0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC, 0xDD, 0xEE]
lutValsVDP_shl = [0x00, 0x1D, 0x34, 0x46, 0x57, 0x65, 0x74, 0x82, 0x90, 0x9E, 0xAC, 0xBB, 0xCE, 0xE4, 0xFF]

def FindIndex(ii, vals):
	return min(xrange(len(vals)), key=lambda jj: abs(vals[jj]-ii))

# Build lookup tables for color conversion in the color -> index direction.
# SonMapEd-like source
lutSME_src_def = {ii : FindIndex(ii, lutValsSME_def) for ii in xrange(256)}
lutSME_src_shl = {ii : FindIndex(ii, lutValsSME_shl) for ii in xrange(256)}
# S&KC-like source
lutSKC_src_def = {ii : FindIndex(ii, lutValsSKC_def) for ii in xrange(256)}
lutSKC_src_shl = {ii : FindIndex(ii, lutValsSKC_shl) for ii in xrange(256)}
# VDP-like source
lutVDP_src_def = {ii : FindIndex(ii, lutValsVDP_def) for ii in xrange(256)}
lutVDP_src_shl = {ii : FindIndex(ii, lutValsVDP_shl) for ii in xrange(256)}

# Build lookup tables for color conversion in the index -> color direction.
# SonMapEd destination
lutSME_dst_def = {ii : lutValsSME_def[ii] for ii in xrange(8)}
lutSME_dst_shl = {ii : lutValsSME_shl[ii] for ii in xrange(15)}
# S&KC destination
lutSKC_dst_def = {ii : lutValsSKC_def[ii] for ii in xrange(8)}
lutSKC_dst_shl = {ii : lutValsSKC_shl[ii] for ii in xrange(15)}
# VDP destination
lutVDP_dst_def = {ii : lutValsVDP_def[ii] for ii in xrange(8)}
lutVDP_dst_shl = {ii : lutValsVDP_shl[ii] for ii in xrange(15)}

def SelectValsLUT(mode):
	if mode == ColorMode.SonMapEd:
		return lutValsSME_def
	if mode == ColorMode.SKCollect:
		return lutValsSKC_def
	if mode == ColorMode.Measured:
		return lutValsVDP_def

def FindColor(clr, mode):
	lut = SelectValsLUT(mode)
	return lut[FindIndex(clr, lut)]

def SelectSrcLUT(mode):
	if mode == ColorMode.SonMapEd:
		return lutSME_src_def
	if mode == ColorMode.SKCollect:
		return lutSKC_src_def
	if mode == ColorMode.Measured:
		return lutVDP_src_def

def SelectSrcLUTShl(mode):
	if mode == ColorMode.SonMapEd:
		return lutSME_src_shl
	if mode == ColorMode.SKCollect:
		return lutSKC_src_shl
	if mode == ColorMode.Measured:
		return lutVDP_src_shl

def SelectDstLUT(mode):
	if mode == ColorMode.SonMapEd:
		return lutSME_dst_def
	if mode == ColorMode.SKCollect:
		return lutSKC_dst_def
	if mode == ColorMode.Measured:
		return lutVDP_dst_def

def SelectDstLUTShl(mode):
	if mode == ColorMode.SonMapEd:
		return lutSME_dst_shl
	if mode == ColorMode.SKCollect:
		return lutSKC_dst_shl
	if mode == ColorMode.Measured:
		return lutVDP_dst_shl

def BuildColorLUT(srcmode, dstmode, shlmode):
	srclut = SelectSrcLUT(srcmode)
	dstlut = SelectDstLUT(dstmode)
	if shlmode is True:
		srclutshl = SelectSrcLUTShl(srcmode)
		dstlutshl = SelectDstLUTShl(dstmode)
		# LUT wrapper
		return {ii : (dstlutshl[srclutshl[ii]],dstlut[srclut[ii]],srclutshl[ii]<=7,srclutshl[ii]>=7) for ii in xrange(256)}
	# LUT wrapper
	return {ii : (dstlut[srclut[ii]],dstlut[srclut[ii]],False,False) for ii in xrange(256)}

def ConvertColormap(image, lut):
	nbytes,colormap = pdb.gimp_image_get_colormap(image)
	max_progress = nbytes
	# Create empty colormap
	ncolomap = []
	# For progress bar
	progress = 0
	# Fill new colormap by converting from old colormap
	for ii in xrange(nbytes/3):
		valshl1,valnor1,shad1,high1 = lut[colormap[3*ii+0]]
		valshl2,valnor2,shad2,high2 = lut[colormap[3*ii+1]]
		valshl3,valnor3,shad3,high3 = lut[colormap[3*ii+2]]

		if shad1 == shad2 == shad3 == True or high1 == high2 == high3 == True:
			ncolomap.append(valshl1)
			ncolomap.append(valshl2)
			ncolomap.append(valshl3)
		else:
			ncolomap.append(valnor1)
			ncolomap.append(valnor2)
			ncolomap.append(valnor3)
		progress = progress + 3
		gimp.progress_update(float(progress) / max_progress)
	# Activate the new colormap
	pdb.gimp_image_set_colormap(image, nbytes, ncolomap)
	layer.flush()
	gimp.displays_flush()

def ConvertTile(srcTile, dstTile, lut):
	# Iterate over the pixels of each tile.
	for ii in xrange(srcTile.ewidth):
		for jj in xrange(srcTile.eheight):
			# Get the pixel.
			pixel = srcTile[ii, jj]
			valshl1,valnor1,shad1,high1 = lut[ord(pixel[0])]
			valshl2,valnor2,shad2,high2 = lut[ord(pixel[1])]
			valshl3,valnor3,shad3,high3 = lut[ord(pixel[2])]

			res = ''
			if shad1 == shad2 == shad3 == True or high1 == high2 == high3 == True:
				res += chr(valshl1)
				res += chr(valshl2)
				res += chr(valshl3)
			else:
				res += chr(valnor1)
				res += chr(valnor2)
				res += chr(valnor3)
			if len(pixel) >= 3:
				for kk in xrange(3, len(pixel)):
					res += pixel[kk]
			# Save the value in the result layer.
			dstTile[ii, jj] = res

def FindLayer(image, layer):
	for ll,lay in enumerate(image.layers):
		if lay == layer:
			return ll
	# Should be impossible
	assert False, "This should be unreachable... Gimp is broken."

def MDColors(image, layer, srcmode, dstmode, shlmode):
	lut = BuildColorLUT(srcmode, dstmode, shlmode)
	gimp.progress_init("Converting to MD colors...")
	# Indexed images are faster
	if layer.is_indexed:
		ConvertColormap(image, lut)
	else:
		pdb.gimp_image_undo_group_start(image)
		# Get the layer position.
		pos = FindLayer(image, layer)
		# Create a new layer to save the results (otherwise is not possible to undo the operation).
		newLayer = layer.copy()
		image.add_layer(newLayer, pos)
		layerName = layer.name
		# Clear the new layer.
		pdb.gimp_edit_clear(newLayer)
		newLayer.flush()
		# Calculate the number of tiles.
		tn = int(layer.width / 64)
		if (layer.width % 64) > 0:
			tn += 1
		tm = int(layer.height / 64)
		if (layer.height % 64) > 0:
			tm += 1
		# Iterate over the tiles.
		for tx in xrange(tn):
			for ty in xrange(tm):
				# Update the progress bar.
				gimp.progress_update(float(tx * tm + ty) / float(tn * tm))
				ConvertTile(layer.get_tile(False, ty, tx), newLayer.get_tile(False, ty, tx), lut)
		# Update the new layer.
		newLayer.flush()
		newLayer.merge_shadow(True)
		newLayer.update(0, 0, layer.width, layer.height)
		# Remove the old layer.
		image.remove_layer(layer)
		newLayer.name = layerName
		gimp.displays_flush()
		pdb.gimp_image_undo_group_end(image)

def MDFade(image, layer, srcmode, dstmode, fademode):
	srclut = SelectSrcLUT(srcmode)
	dstlut = SelectDstLUT(dstmode)
	gimp.progress_init("Generating palette fade...")
	pdb.gimp_image_undo_group_start(image)
	# Get the layer position.
	pos = FindLayer(image, layer)
	srcWhite = FindColor(255, srcmode)
	if (fademode == FadeMode.CurrentToBlack):
		conv = lambda jj,ss: (jj*(15-ss)) // 15
	elif (fademode == FadeMode.BlackToCurrent):
		conv = lambda jj,ss: (jj*ss) // 15
	elif (fademode == FadeMode.CurrentToWhite):
		conv = lambda jj,ss: (jj*(15-ss) + srcWhite*ss) // 15
	else:#if (fademode == FadeMode.WhiteToCurrent):
		conv = lambda jj,ss: (jj*ss + srcWhite*(15-ss)) // 15
	finalLayer = None
	for step in xrange(15):
		lut = {chr(ii) : chr(dstlut[srclut[conv(ii, step)]]) for ii in xrange(256)}
		# Create a new layer to save the results (otherwise is not possible to undo the operation).
		newLayer = layer.copy()
		image.add_layer(newLayer, pos)
		# Clear the new layer.
		pdb.gimp_edit_clear(newLayer)
		newLayer.flush()
		# Calculate the number of tiles.
		tn = int(layer.width / 64)
		if (layer.width % 64) > 0:
			tn += 1
		tm = int(layer.height / 64)
		if (layer.height % 64) > 0:
			tm += 1
		# Iterate over the tiles.
		for tx in xrange(tn):
			for ty in xrange(tm):
				# Update the progress bar.
				gimp.progress_update(float(step * tn * tm + tx * tm + ty) / float(15 * tn * tm))
				# Get the tiles.
				srcTile = layer.get_tile(False, ty, tx)
				dstTile = newLayer.get_tile(False, ty, tx)
				# Iterate over the pixels of each tile.
				for ii in xrange(srcTile.ewidth):
					for jj in xrange(srcTile.eheight):
						# Get the pixel.
						pixel = srcTile[ii, jj]
						res = ''
						for kk in xrange(len(pixel)):
							if kk >= 3:
								res += pixel[kk]
							else:
								res += lut[pixel[kk]]
						# Save the value in the result layer.
						dstTile[ii, jj] = res
		# Update the new layer.
		newLayer.flush()
		newLayer.merge_shadow(True)
		newLayer.update(0, 0, layer.width, layer.height)
		finalLayer = newLayer
	# Remove the old layer.
	if finalLayer is not None:
		layerName = layer.name
		image.remove_layer(layer)
		finalLayer.name = layerName
	gimp.displays_flush()
	pdb.gimp_image_undo_group_end(image)

mdcolors_desc = \
	"Coverts an image to Mega Drive colors.\n"

mdfader_desc = \
	"Coverts an image to Mega Drive colors, then performs a fade with 16 steps\n"

mdcolor_info = R'''
A 3-bit Mega Drive color channel can be represented as:
  •	SonMapEd colors:
   	Normal:      0  32  64  96 128 160 192 224
   	Shadow:      0  16  32  48  64  80  96 112
   	Highlight: 112 128 144 160 176 192 208 224
  •	Sonic & Knuckles Collection (S&KC) colors:
   	Normal:      0  34  68 102 136 170 204 238
   	Shadow:      0  17  34  51  68  85 102 119
   	Highlight: 119 136 153 170 187 204 221 238
  •	VDP measurements:
   	Normal:      0  52  87 116 144 172 206 255
   	Shadow:      0  29  52  70  87 101 116 130
   	Highlight: 130 144 158 172 187 206 228 255'''

register(
	"python-fu-mega-drive-colors",
	mdcolors_desc + mdcolor_info,
	mdcolors_desc + mdcolor_info,
	"Flamewing",
	"Flamewing",
	"2013-2021",
	"Fix Colors...",
	"RGB*, GRAY*, INDEXED*",
	[
		(PF_IMAGE, "image", "Input image", None),
		(PF_DRAWABLE, "layer", "Input layer", None),
		(PF_RADIO, "srcmode", "Assume source is close to:",
			ColorMode.SKCollect, (
				("SonMapEd colors" , ColorMode.SonMapEd),
				("S&KC colors"     , ColorMode.SKCollect),
				("VDP measurements", ColorMode.Measured)
			)
		),
		(PF_RADIO, "dstmode", "Destination should use:",
			ColorMode.SKCollect, (
				("SonMapEd colors" , ColorMode.SonMapEd),
				("S&KC colors"     , ColorMode.SKCollect),
				("VDP measurements", ColorMode.Measured)
			)
		),
		(PF_BOOL, "shlmode", "Allow shadow/highlight colors:", False),
	],
	[],
	MDColors, menu="<Image>/Filters/Mega Drive")

register(
	"python-fu-mega-drive-fade",
	mdfader_desc + mdcolor_info,
	mdfader_desc + mdcolor_info,
	"Flamewing",
	"Flamewing",
	"2013-2021",
	"Palette fade...",
	"RGB*",
	[
		(PF_IMAGE, "image", "Input image", None),
		(PF_DRAWABLE, "layer", "Input layer", None),
		(PF_RADIO, "srcmode", "Assume source is close to:",
			ColorMode.SKCollect, (
				("SonMapEd colors" , ColorMode.SonMapEd),
				("S&KC colors"     , ColorMode.SKCollect),
				("VDP measurements", ColorMode.Measured)
			)
		),
		(PF_RADIO, "dstmode", "Destination should use:",
			ColorMode.SKCollect, (
				("SonMapEd colors" , ColorMode.SonMapEd),
				("S&KC colors"     , ColorMode.SKCollect),
				("VDP measurements", ColorMode.Measured)
			)
		),
		(PF_RADIO, "fademode", "Fade mode:",
			ColorMode.SKCollect, (
				("Current to black", FadeMode.CurrentToBlack),
				("Black to current", FadeMode.BlackToCurrent),
				("Current to white", FadeMode.CurrentToWhite),
				("White to current", FadeMode.WhiteToCurrent)
			)
		),
	],
	[],
	MDFade, menu="<Image>/Filters/Mega Drive")

main()
