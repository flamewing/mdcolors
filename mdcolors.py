#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013-2016  Flamewing <flamewing.sonic@gmail.com>
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

import math
import struct
from gimpfu import gimp
from gimpfu import pdb
from gimpfu import register
from gimpfu import PF_IMAGE
from gimpfu import PF_DRAWABLE
from gimpfu import PF_RADIO
from gimpfu import PF_BOOL
from gimpfu import main
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

def SelectSrcLUT(mode):
	if mode == ColorMode.SonMapEd:
		return lutSME_src_def
	elif mode == ColorMode.SKCollect:
		return lutSKC_src_def
	elif mode == ColorMode.Measured:
		return lutVDP_src_def

def SelectSrcLUTShl(mode):
	if mode == ColorMode.SonMapEd:
		return lutSME_src_shl
	elif mode == ColorMode.SKCollect:
		return lutSKC_src_shl
	elif mode == ColorMode.Measured:
		return lutVDP_src_shl

def SelectDstLUT(mode):
	if mode == ColorMode.SonMapEd:
		return lutSME_dst_def
	elif mode == ColorMode.SKCollect:
		return lutSKC_dst_def
	elif mode == ColorMode.Measured:
		return lutVDP_dst_def

def SelectDstLUTShl(mode):
	if mode == ColorMode.SonMapEd:
		return lutSME_dst_shl
	elif mode == ColorMode.SKCollect:
		return lutSKC_dst_shl
	elif mode == ColorMode.Measured:
		return lutVDP_dst_shl

def BuildColorLUT(srcmode, dstmode, shlmode):
	srclut = SelectSrcLUT(srcmode)
	dstlut = SelectDstLUT(dstmode)
	if shlmode is True:
		srclutshl = SelectSrcLUTShl(srcmode)
		dstlutshl = SelectDstLUTShl(dstmode)
		# LUT wrapper
		return {ii : (dstlutshl[srclutshl[ii]],dstlut[srclut[ii]],(srclutshl[ii]%2)==0,srclutshl[ii]<=7,srclutshl[ii]>=7) for ii in xrange(256)}
	else:
		# LUT wrapper
		return {ii : (dstlut[srclut[ii]],dstlut[srclut[ii]],True,False,False) for ii in xrange(256)}

def MDColors(image, layer, srcmode, dstmode, shlmode):
	lut = BuildColorLUT(srcmode, dstmode, shlmode)
	# For progress bar
	progress = 0
	gimp.progress_init("Converting to MD colors...")
	# Indexed images are faster
	if layer.is_indexed:
		nbytes,colormap = pdb.gimp_image_get_colormap(image)
		max_progress = nbytes
		# Create empty colormap
		ncolomap = []
		# Fill new colormap by converting from old colormap
		for ii in xrange(nbytes/3):
			valshl1,valnor1,norm1,shad1,high1 = lut[colormap[3*ii+0]]
			valshl2,valnor2,norm2,shad2,high2 = lut[colormap[3*ii+1]]
			valshl3,valnor3,norm3,shad3,high3 = lut[colormap[3*ii+2]]

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
	else:
		pdb.gimp_image_undo_group_start(image)
		# Get the layer position.
		pos = 0
		for ll,lay in enumerate(image.layers):
			if lay == layer:
				pos = ll
				break
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
				# Get the tiles.
				srcTile = layer.get_tile(False, ty, tx)
				dstTile = newLayer.get_tile(False, ty, tx)
				# Iterate over the pixels of each tile.
				for ii in xrange(srcTile.ewidth):
					for jj in xrange(srcTile.eheight):
						# Get the pixel.
						pixel = srcTile[ii, jj]
						valshl1,valnor1,norm1,shad1,high1 = lut[ord(pixel[0])]
						valshl2,valnor2,norm2,shad2,high2 = lut[ord(pixel[1])]
						valshl3,valnor3,norm3,shad3,high3 = lut[ord(pixel[2])]

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
	# For progress bar
	progress = 0
	gimp.progress_init("Generating palette fade...")
	pdb.gimp_image_undo_group_start(image)
	# Get the layer position.
	pos = 0
	for ll,lay in enumerate(image.layers):
		if lay == layer:
			pos = ll
			break
	for step in xrange(15):
		lut = {chr(ii) : chr(dstlut[srclut[ii]]) for ii in xrange(256)}
		newLayer = layer.copy()
		# Create a new layer to save the results (otherwise is not possible to undo the operation).
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
				gimp.progress_update(float(tx * tm + ty) / float(tn * tm) / 15.0)
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
	# Remove the old layer.
	image.remove_layer(layer)
	newLayer.name = layerName
	gimp.displays_flush()
	pdb.gimp_image_undo_group_end(image)

mdcolors_desc = \
	"Coverts an image to Mega Drive colors.\n"

mdfader_desc = \
	"Coverts an image to Mega Drive colors, then performs a fade with 16 steps\n"

mdcolor_info = \
	"\n" \
	"A 3-bit Mega Drive color channel can be represented as:\n" \
	"  •\tSonMapEd colors:\n" \
	"   \tNormal:\t  𝟢  𝟥𝟤  𝟨𝟦  𝟫𝟨 𝟣𝟤𝟪 𝟣𝟨𝟢 𝟣𝟫𝟤 𝟤𝟤𝟦\n" \
	"   \tShadow:\t  𝟢  𝟣𝟨  𝟥𝟤  𝟦𝟪  𝟨𝟦  𝟪𝟢  𝟫𝟨 𝟣𝟣𝟤\n" \
	"   \tHighlight:\t𝟣𝟣𝟤 𝟣𝟤𝟪 𝟣𝟦𝟦 𝟣𝟨𝟢 𝟣𝟩𝟨 𝟣𝟫𝟤 𝟤𝟢𝟪 𝟤𝟤𝟦\n" \
	"  •\tSonic & Knuckles Collection (S&KC) colors:\n" \
	"   \tNormal:\t  𝟢  𝟥𝟦  𝟨𝟪 𝟣𝟢𝟤 𝟣𝟥𝟨 𝟣𝟩𝟢 𝟤𝟢𝟦 𝟤𝟥𝟪\n" \
	"   \tShadow:\t  𝟢  𝟣𝟩  𝟥𝟦  𝟧𝟣  𝟨𝟪  𝟪𝟧 𝟣𝟢𝟤 𝟣𝟣𝟫\n" \
	"   \tHighlight:\t𝟣𝟣𝟫 𝟣𝟥𝟨 𝟣𝟧𝟥 𝟣𝟩𝟢 𝟣𝟪𝟩 𝟤𝟢𝟦 𝟤𝟤𝟣 𝟤𝟥𝟪\n" \
	"  •\tVDP measurements:\n" \
	"   \tNormal:\t  𝟢  𝟧𝟤  𝟪𝟩 𝟣𝟣𝟨 𝟣𝟦𝟦 𝟣𝟩𝟤 𝟤𝟢𝟨 𝟤𝟧𝟧\n" \
	"   \tShadow:\t  𝟢  𝟤𝟫  𝟧𝟤  𝟩𝟢  𝟪𝟩 𝟣𝟢𝟣 𝟣𝟣𝟨 𝟣𝟥𝟢\n" \
	"   \tHighlight:\t𝟣𝟥𝟢 𝟣𝟦𝟦 𝟣𝟧𝟪 𝟣𝟩𝟤 𝟣𝟪𝟩 𝟤𝟢𝟨 𝟤𝟤𝟪 𝟤𝟧𝟧"

register(
	"python-fu-mega-drive-colors",
	mdcolors_desc + mdcolor_info,
	mdcolors_desc + mdcolor_info,
	"Flamewing",
	"Flamewing",
	"2013-2018",
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
	"2013-2016",
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
