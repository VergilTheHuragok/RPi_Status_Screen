import pygame
import pygame
import os
import time
import socket
import pygame
from pygame.locals import *
from time import sleep
import urllib.request
import colorsys
import math
import random
import gzip

HOST = "192.168.0."
HOSTEND = "100"
PORT = 12742
badsock = True
while badsock:
	badsock = False
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.settimeout(.1)
		sock.connect((HOST + HOSTEND, PORT))
	except:
		print("BAD IP: " + HOST + HOSTEND)
		if int(HOSTEND) > 120:
			HOSTEND = "99"
		HOSTEND = str(int(HOSTEND) + 1)
		print(HOSTEND)
		badsock = True

reply = "\n"
with gzip.open("page.gz", 'wb') as outfile:
	outfile.write(bytes(reply, 'UTF-8'))
with gzip.open("page.gz", 'r') as infile:
	outfile_content = infile.read()
sock.sendall(outfile_content + "\n".encode('UTF-8'))
print("Sending: " + reply)

HOST = HOST + HOSTEND
print("Good IP: " + HOST)

#Display/UI settings

backContrastThreshold = 5			#Larger number makes back more contrasting to text
textSimThreshold = 150 				#Smaller number increases likelihood of similar colors
backLightThreshold = .5			        #0-1 Smaller threshold makes text harder to read against background
backSaturationThreshold = .5 		        #0-1 Smaller threshold makes text harder to read against background
									
						#Multiply values in getBestOptions by these
bestSimilarEnhancer = 1				
bestSaturationEnhancer = .5			#Generally saturation and lightness should add to one whole. 
bestLightEnhancer = .5
bestContrastEnhancer = 1
bestShadeEnhancer = 4

hueScale = 1 					#0-1 Larger number increases variety of text color hues
safeCutoff = 450 				#smaller numbers can streamline color generation but constrict possibilities for color
shadeBias = 25					#Larger number reduces tendency to stick to one area of spectrum with text
backSelection = 2 				#larger selection finds background colors faster and can increase contrast. May be less varied
accentShift = .45				#Amount of light shift for accent colors

numTextColors = 5				#Number of text colors to generate including header color and first color generated

dispGen = False					#Display generation process (Slower)
dragShift = 40					#Distance to drag to change page

spacing = 4					#Spacing between characters vertically
charWidth = 9					#Width of characters in pixels
charHeight = 13					#Height of characters in pixels

pressLength = 1500				#Number of millis seconds to hold to show menu

startPage = "!requestPages"			#Page to start on. !requestPages to choose default page

delayStart = 0					#Start for delay between requests in order to retrieve all information. Automatically increased if too fast
delayInterval = .01				#Amount of time to scale delay with
delayMax = .4  				        #Max value for delay


#Set up touchscreen
#Comment each line to display on computer rather than pi

os.environ['SDL_VIDEODRIVER'] = 'fbcon'
os.environ['SDL_MOUSEDEV'] = '/dev/input/touchscreen'
os.environ['SDL_MOUSEDRV'] = 'TSLIB'
os.putenv('SDL_FBDEV', '/dev/fb1')

#Initiate Pygame

pygame.init()
myfont = pygame.font.SysFont("monospace", 15)
lcd = pygame.display.set_mode((320, 240))
pygame.mouse.set_visible(False)

#Color Methods

def getBestOptions(colors, backColor): 
	values = []
	for col in colors:
		temp = []
		temp.append(col)
		temp.append(backColor)
		low1, low2, lrat, high1, high2, hrat = getContrast(temp)
		totalAve = 0
		bc = []
		bc.append(backColor)
		for col2 in colors + bc:
			ave = 0
			for i in range(0,3):
				ave = ave + abs(col[i] - col2[i])
			totalAve = totalAve + ave
		simVal = ((totalAve/len(colors))/(len(colors)*765))
		values.append((abs(getLightness(backColor) - getLightness(col)) * bestLightEnhancer) + (abs(getSaturation(backColor) - getSaturation(col)) * bestSaturationEnhancer) + ((hrat/21) * bestContrastEnhancer) + (simVal * bestSimilarEnhancer) + ((1 - abs(getLightness(col) - .5)) * bestShadeEnhancer))
	sortValues = sorted(values)
	fcolors = []
	fvalues = []
	for val in sortValues:
		c = 0
		for val2 in values:
			if val == val2:	
				fcolors.append(colors[c])
				fvalues.append(values[c])
			c = c + 1
	ffcolors = []
	for col in sorted(range(0,len(fcolors)), reverse=True):
		ffcolors.append(fcolors[col])
	ffvalues = []
	for val in sorted(range(0,len(fvalues)), reverse=True):
		ffvalues.append(fvalues[val])
	d = 0
	for l in ffcolors:
		d = d + 1
	return ffcolors

def genShade(color,hueScale,lastDir,shadeBias):
	color = [(float)(color[0])/255,(float)(color[1])/255,(float)(color[2])/255]
	color = colorsys.rgb_to_hls(color[0],color[1],color[2])
	h = (float)(color[0])
	d = 0
	if (lastDir < 0):
		lastDir = 0
	while hueScale < 10:
		hueScale = hueScale * 10
		d = d + 1
	if (random.randint(0,lastDir) > shadeBias):
		h = h + random.randint(1,hueScale)/pow(10,d)
		if (h>1):
			h = 1
		lastDir = lastDir + 1
	else:
		h = h - random.randint(1,hueScale)/pow(10,d)
		if (h<0):
			h = 0
		lastDir = lastDir - 1
	ncolor = [h, random.random(),random.random()]
	ncolor = colorsys.hls_to_rgb(ncolor[0],ncolor[1],ncolor[2])
	ncolor = [(float)(ncolor[0])*255,(float)(ncolor[1])*255,(float)(ncolor[2])*255]
	return ncolor, lastDir
	
def getAccent(color):
	color = [(float)(color[0])/255,(float)(color[1])/255,(float)(color[2])/255]
	color = colorsys.rgb_to_hls(color[0],color[1],color[2])
	if (color[1] <= 0.5):
		ncolor = [color[0],1 - accentShift,color[2]]
	else:
		ncolor = [color[0],accentShift,color[2]]
	ncolor = colorsys.hls_to_rgb(ncolor[0],ncolor[1],ncolor[2])
	ncolor = [(float)(ncolor[0])*255,(float)(ncolor[1])*255,(float)(ncolor[2])*255]
	return ncolor
	
def flatten(color): #unused
	color = [(float)(color[0])/255,(float)(color[1])/255,(float)(color[2])/255]
	color = colorsys.rgb_to_hls(color[0],color[1],color[2])
	h = color[1]
	h = h - random.randint(1,6)/10
	if (h<0):
		h = 0
	color = [color[0], h, color[2]]
	return color

def getLightness(color):
	color = [(float)(color[0])/255,(float)(color[1])/255,(float)(color[2])/255]
	color = colorsys.rgb_to_hls(color[0],color[1],color[2])
	return color[1]
def getSaturation(color):
	color = [(float)(color[0])/255,(float)(color[1])/255,(float)(color[2])/255]
	color = colorsys.rgb_to_hls(color[0],color[1],color[2])
	return color[2]

def getContrast(colors):
	rellum = []
	for color in colors:
		if (color[0] <= 10):
			Rg = (float)(color[0])/3294
		else:
			Rg = pow(((float)(color[0])/269 + .0513),2.4)
		if (color[1] <= 10):
			Gg = (float)(color[1])/3294
		else:
			Gg = pow(((float)(color[1])/269 + .0513),2.4)
		if (color[2] <= 10):
			Bg = (float)(color[2])/3294
		else:
			Bg = pow(((float)(color[2])/269 + .0513),2.4)
		L = 0.2126*Rg + 0.7152*Gg + 0.0722 * Bg
		rellum.append(L)
	contrasts = []
	conColors = []
	for val in rellum:
		temp = []
		for val2 in rellum:
			if val == val2:
				temp.append("Self")
			else:
				if (val < val2):
					valb = val2
					valb2 = val
				else:
					valb = val
					valb2 = val2
				temp.append((valb +.05)/(valb2+.05))
		contrasts.append(temp)
	l = 100000000
	h = 0 
	i = 0
	for data in contrasts:
		for i1 in range(0,len(contrasts)):
			if (data[i1] != "Self" and data[i1] < l):
				l = data[i1]
				li = i
				lio = i1
			if (data[i1] != "Self" and data[i1] > h):
				h = data[i1]
				hi = i
				hio = i1
		i = i + 1
	return colors[li], colors[lio], l, colors[hi], colors[hio], h
	
#Generate Colors
	
def genColors():
	lcd.fill((0,0,0))
	label = myfont.render("Generating Colors", 1, (255,255,255))
	lcd.blit(label, (320/2 - (len("Generating Colors")*charWidth)/2,240/2))
	pygame.display.update()
	restart = False
	cont = True
	while cont:
		while True:
			backColors = []
			for i in range(0, backSelection):
				backColors.append((random.randint(0,255),random.randint(0,255),random.randint(0,255)))
			if (dispGen):
				N = len(backColors)
				for i in range(0,N):
					lcd.fill(backColors[i],(0,0,(320)-(i*(320/N)),240))
				pygame.display.update()	
			low1, low2, lrat, high1, high2, hrat = getContrast(backColors)
			if (hrat > backContrastThreshold): #finding contrasting colors for background and first text
				backColor = high1
				if (abs(getLightness(backColor) - getLightness(high2)) >= backLightThreshold and abs(getSaturation(backColor) - getSaturation(high2)) >= backSaturationThreshold):
					break

		textColors = []
		textColors.append(high2)
		lastShade = high2
		lastDir = shadeBias * 2
		headerColor = -1
		#Generate Text Colors
		newSet = False
		for i in range(0,numTextColors):
			if (newSet):
				break
			safe = 0
			newSet = False
			while True:
				safe = safe + 1
				if (safe > safeCutoff * len(textColors)):
					newSet = True
					break
				new = False
				ncolor, lastDir = genShade(high2, hueScale, lastDir, shadeBias)#[random.randint(0,255),random.randint(0,255),random.randint(0,255)] #use random colors or generate shades of first text
				if (dispGen):
					lcd.fill(backColor,(0,0,320,240))
					if (i == numTextColors - 1):
						lcd.fill(getAccent(backColor),(0,(240/2) - 15,320,240))	
					N = len(textColors) + 1
					for i in range(0,N):
						if (i == len(textColors)):
							lcd.fill(textColors[i - 1],(0,240/2,(320)-(i *(320/N)),240))
						else:
							lcd.fill(textColors[i],(0,240/2,(320)-(i *(320/N)),240))
					lcd.fill(ncolor,(0,240/2,(320)-i*(320/N),240))
					pygame.display.update()	
				colors = []
				colors.append(ncolor)
				if (i != numTextColors - 1):
					colors.append(backColor)
					backCheck = backColor
				else:
					colors.append(getAccent(backColor))
					backCheck = getAccent(backColor)
				lowb1, lowb2, lratb, highb1, highb2, hratb = getContrast(colors)
				if (hratb > backContrastThreshold and (abs(getLightness(backCheck) - getLightness(ncolor)) >= backLightThreshold and abs(getSaturation(backCheck) - getSaturation(ncolor)) >= backSaturationThreshold)):
					for col in textColors:
						if (new):
							break
						ave = 0
						for b in range(0,3):
							ave = ave + abs(col[b] - ncolor[b])
						if (ave < textSimThreshold):
							new = True
							break
					if ((not new) and (i != numTextColors - 1)):
						textColors.append(ncolor)
						break
					elif (i == numTextColors - 1):
						headerColor = ncolor

		if (len(textColors) > numTextColors - 2 and headerColor != -1):
			cont = False
			colorConts = []
			for col in textColors:
				temp = []
				temp.append(col)
				temp.append(backColor)
				low1, low2, lrat, high1, high2, hrat = getContrast(temp)
				colorConts.append(lrat)
			colorSims = []
			for col in textColors:
				colorSims.append(abs(backColor[0] - col[0]) + abs(backColor[1] - col[1]) + abs(backColor[2] - col[2]))
			colorSats = []
			for col in textColors:
				colorSats.append(abs(getSaturation(col) - getSaturation(backColor)))
			colorLights = []
			for col in textColors:
				colorLights.append(abs(getLightness(col) - getLightness(backColor)))
			m = 0
			for i in range(0,len(colorConts)):
				if (colorConts[i] > m):
					m = colorConts[i]
					contColor = textColors[i]
			hccolor = contColor
			m = 10000000
			for i in range(0,len(colorConts)):
				if (colorConts[i] < m):
					m = colorConts[i]
					contColor = textColors[i]
			lccolor = contColor
			m = 10000000
			for i in range(0,len(colorSims)):
				if (colorSims[i] < m):
					m = colorSims[i]
					simColor = textColors[i]
			lscolor = simColor
			m = 0
			for i in range(0,len(colorSims)):
				if (colorSims[i] > m):
					m = colorSims[i]
					simColor = textColors[i]
			hscolor = simColor
			m = 10000000
			for i in range(0,len(colorSats)):
				if (colorSats[i] < m):
					m = colorSats[i]
					satColor = textColors[i]
			lacolor = satColor
			m = 0
			for i in range(0,len(colorSats)):
				if (colorSats[i] > m):
					m = colorSats[i]
					satColor = textColors[i]
			hacolor = satColor
			m = 10000000
			for i in range(0,len(colorLights)):
				if (colorLights[i] < m):
					m = colorLights[i]
					lightColor = textColors[i]
			llcolor = lightColor
			m = 0
			for i in range(0,len(colorLights)):
				if (colorLights[i] > m):
					m = colorLights[i]
					lightColor = textColors[i]
			hlcolor = lightColor
			
			lcd.fill(backColor)
			i = 0
			best = getBestOptions(textColors, backColor)
			for col in best:
				label = myfont.render("Cool Text " + str(i + 1), 1, col)
				lcd.blit(label, (320/2 - (len("Cool Text i")*charWidth)/2, charHeight * i))
				i = i + 1
			label = myfont.render("High Contrast", 1, hccolor)
			lcd.blit(label, (320/2 - (len("High Contrast")*charWidth)/2, charHeight * i + charHeight))
			label = myfont.render("Low Contrast", 1, lccolor)
			lcd.blit(label, (320/2 - (len("Low Contrast")*charWidth)/2, charHeight * i + (2 * charHeight)))
			label = myfont.render("Most Similar", 1, hscolor)
			lcd.blit(label, (320/2 - (len("Most Similar")*charWidth)/2, charHeight * i + (3 * charHeight)))
			label = myfont.render("Least Similar", 1, lscolor)
			lcd.blit(label, (320/2 - (len("Least Similar")*charWidth)/2, charHeight * i + (4 * charHeight)))
			label = myfont.render("Most Saturated", 1, hacolor)
			lcd.blit(label, (320/2 - (len("Most Saturated")*charWidth)/2, charHeight * i + (5 * charHeight)))
			label = myfont.render("Least Saturated", 1, lacolor)
			lcd.blit(label, (320/2 - (len("Least Saturated")*charWidth)/2, charHeight * i + (6 * charHeight)))
			label = myfont.render("Most Light", 1, hlcolor)
			lcd.blit(label, (320/2 - (len("Most Light")*charWidth)/2, charHeight * i + (7 * charHeight)))
			label = myfont.render("Least Light", 1, llcolor)
			lcd.blit(label, (320/2 - (len("Least Light")*charWidth)/2, charHeight * i + (8 * charHeight)))
			lcd.fill(getAccent(backColor),(0,  charHeight * i + (9 * charHeight) , 320, charHeight + 4))
			label = myfont.render("Header Color", 1, headerColor)
			lcd.blit(label, (320/2 - (len("Header Color")*charWidth)/2, charHeight * i + (9 * charHeight)))
			pygame.display.update()
			

	unassigned = []
	usableColors = textColors
	backColor = backColor
	headerColor = headerColor
	barColor = backColor
		
	found = False
	for col in usableColors:
		if col == best[0]:
			valueColor = best[0]
			usableColors.remove(best[0])
			found = True
			break
	if not found:
		unassigned.append("Value")
	found = False
	for col in usableColors:
		if col == best[2]:
			titleColor = best[2]
			usableColors.remove(best[2])
			found = True
			break
	if not found:
		unassigned.append("Title")
	found = False
	for col in usableColors:
		if col == best[1]:
			labelColor = best[1]
			usableColors.remove(best[1])
			found = True
			break
	if not found:
		unassigned.append("Label")
	found = False
	for col in usableColors:
		if col == best[3]:
			altTitleColor = best[3]
			usableColors.remove(best[3])
			found = True
			break
	if not found:
		unassigned.append("altTitle")
		for name in unassigned:
			if (name == "Title"):
				titleColor = usableColors[0]
				usableColors.remove(usableColors[0])
			if (name == "Label"):
				labelColor = usableColors[0]
				usableColors.remove(usableColors[0])
			if (name == "Value"):
				valueColor = usableColors[0]
				usableColors.remove(usableColors[0])
			if (name == "altTitle"):
				altTitleColor = usableColors[0]
				usableColors.remove(usableColors[0])
	return backColor, titleColor, labelColor, altTitleColor, valueColor, headerColor

#Page Methods

def slideRight(page,pages):
	for key in pages.keys():
		if (key.startswith("2")):	
			return key
	return page
def slideLeft(page,pages):
	for key in pages.keys():
		if (key.startswith("0")):	
			return key
	return page

#Socket Methods

def getPages(lcd, startPage, page):
	global delay
	global LOS
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.connect((HOST, PORT))
	except:
		LOS = True
		print("Server Closed")
		lcd.fill(backColor)
		label = myfont.render("Server Closed", 1, valueColor)
		lcd.blit(label, (320/2 - (len("Server Closed")*charWidth)/2, 240/2))
		return None, startPage, page
	
	reply = page
	with gzip.open("page.gz", 'wb') as outfile:
		outfile.write(bytes(reply, 'UTF-8'))
	with gzip.open("page.gz", 'r') as infile:
		outfile_content = infile.read()
	sock.sendall(outfile_content + "\n".encode('UTF-8'))
	print("Sending: " + reply)
	time.sleep(delay)
	sock.settimeout(5)
	try:
		data = sock.recv(10000)
	except:
		LOS = True
		print("No Connection")
		lcd.fill(backColor)
		label = myfont.render("No Connection", 1, valueColor)
		lcd.blit(label, (320/2 - (len("No Connection")*charWidth)/2, 240/2))
		return None, startPage, page
	LOS = False
	data = data.decode('UTF-8')
	lines = [line.rstrip('\n').rstrip('\r') for line in data.split('\n')]
	print(lines)
	ok = False
	if reply == "!requestPages":
		if len(lines) > 2:
			ok = True
	else:
		for l in lines:
			if "#1" in l:
				ok = True
				break
	if (ok):
		print("TRUE")
	else:
		print("FALSE")
	if ((not ok and delay < delayMax)):
		print(delay, "Too Slow")
		delay = delay + delayInterval
		return getPages(lcd, startPage, page)
	else:
		print(delay, "OK")
		pages = {}
		last = ""
		
		for line in lines:
			if line.startswith("#") and not line[1:] in pages:
				if (startPage == "!requestPages"):
					startPage = line[1:]
					page = startPage
				pages[line[1:]] = last
				last = ""
				if line[2:] == page[1:]:
					page = line[1:]
			else:
				last = last + "|" + line
		return pages, startPage, page

#Util Methods

def containsInt(s):
	return any(char.isdigit() for char in s)

#From the Top

while True:
	
	#Reset Vars and Generate Colors
	
	backColor, titleColor, labelColor, altTitleColor, valueColor, headerColor = genColors()
	lcd.fill(backColor)


	lastPlace = -100

	pressed = 0
	closedBoxes = []

	page = startPage
	tapPos = [0,0]
	pressLen = 0

	delay = delayStart
	
	#Main Event Loop
	print("HERE")
	while True:
		
		if (int(round(time.time()*1000)) > pressed + pressLength and pressed != 0):	
			break #Restart and Regen Colors
		
		#Get Pages
		LOS = True
		while LOS:
			pages, startPage, page = getPages(lcd, startPage, page)
			pygame.display.update()
		# Scan touchscreen events
		for event in pygame.event.get():
			if(event.type is MOUSEBUTTONDOWN):
				position = pygame.mouse.get_pos()
				lastPlace = position[0]
				pressed = int(round(time.time()*1000))
				tapPos = position
				for boxInfo in headerBoxes.keys():
					box = headerBoxes[boxInfo]
					if (position[0] > box[0] and position[1] > box[1] and position[0] < box[2] + box[0] and position[1] < box[3] + box[1]):		
						if boxInfo + "$" + page in closedBoxes:
							closedBoxes.remove(boxInfo + "$" + page)
						else:
							closedBoxes.append(boxInfo + "$" + page)
						break
				pressLen = int(round(time.time()*1000))
			if(event.type is MOUSEBUTTONUP):
				position = pygame.mouse.get_pos()
				if(position[0] < lastPlace - dragShift):
					page = slideRight(page,pages)
					delay = delayStart
					pressLen = 0
				elif(position[0] > lastPlace + dragShift):
					page = slideLeft(page,pages)
					delay = delayStart
					pressLen = 0
				else:
					pass
				tapPos = position
				pressed = 0
		
		for key in pages.keys():
			if key == page:
				lcd.fill(backColor)
				if slideLeft(page,pages) == page:
					disp = ""
				else:
					disp = slideLeft(page,pages)[1:]
				label = myfont.render(disp, 1, altTitleColor)
				lcd.blit(label, (0, 0))
				if slideRight(page,pages) == page:
					disp = ""
				else:
					disp = slideRight(page,pages)[1:]
				label = myfont.render(disp, 1, altTitleColor)
				lcd.blit(label, (320 - len(disp)*charWidth, 0))

				lcd.fill(backColor, ((320/2 - (len(page)*charWidth/2)) - charWidth/2, 0, len(page) * charWidth, charHeight + spacing)) 
				label = myfont.render(page[1:], 1, titleColor)
				lcd.blit(label, (320/2 - (len(page)*charWidth)/2, 0))
				
				i = 1
				bi = -1
				boxStarts = []
				headerBoxes = {}
				if True:
					for line in pages[key].split("|"):
						if line.startswith("$"):
							if (":" in line):
								side1 = line.split(":")
								valueString = ""
								for s in range(1,len(side1)):
									if (s > 1):
										valueString = valueString + ":"
									valueString = valueString + side1[s]
								labelString = line.split(":")[0]
							if (":" in line and (containsInt(valueString) or ("Yes" in valueString or "No" in valueString or "True" in valueString or "False" in valueString))): #Line with value
								if (i > bi + 1 or len(boxStarts) < 1 or (float(line[1:2]) <= boxStarts[len(boxStarts) - 1])): #not in closed box #Causes crash...
									blit = True
									for b in boxStarts:
										if (b >= float(line[1:2])):
											boxStarts.remove(b)
										else:
											blit = False
									if blit:
										label = myfont.render(labelString[2:] + ":", 1, labelColor)
										lcd.blit(label, (float(line[1:2]) * charWidth, i * charHeight + (i * spacing)))
										label = myfont.render(valueString, 1, valueColor)
										lcd.fill(backColor, ((320 - charWidth - (len(valueString)*charWidth)),  i * charHeight + (i * spacing), (len(valueString) * charWidth) + (charWidth), spacing + charHeight)) 
										lcd.blit(label, (320 - charWidth - (len(valueString) * charWidth), i * charHeight + (i * spacing)))
									else:
										i = i - 1
								else:#in closed box
									#if (float(line[1:2]) == boxStarts[len(boxStarts) - 1] + 1):
									label = myfont.render(valueString + " ", 1, headerColor)
									ti = (boxStarts[len(boxStarts) - 1] * charWidth) + closedPos[0] + ni + (charWidth)
									if (ti + len(valueString + " ") * charWidth < 320 - charWidth):
										lcd.blit(label, (ti, closedPos[1]))
									ni = ni + len(valueString + " ") * charWidth
									i = i - 1
									
							else: #Header
								if (i > bi + 1 or len(boxStarts) < 1 or (float(line[1:2]) <= boxStarts[len(boxStarts) - 1])):
									lcd.fill(getAccent(backColor),(float(line[1:2]) * charWidth, i * charHeight + (i * spacing) - 1 , 320, charHeight + 4))	
									label = myfont.render(line[2:], 1, headerColor)
									lcd.blit(label, (float(line[1:2]) * charWidth, i * charHeight + (i * spacing)))
									headerTemp = []
									headerTemp.append(float(line[1:2]) * charWidth)
									headerTemp.append(i * charHeight + (i * spacing) - 1)
									headerTemp.append(320)
									headerTemp.append(charHeight + 4)
									headerBoxes[line[2:]] = headerTemp
								else:
									i = i - 1
								if(line[2:] + "$" + page in closedBoxes): #closed
									if (not (len(boxStarts) > 0 and float(line[1:2]) == boxStarts[len(boxStarts) - 1] + 1)):
										label = myfont.render("[", 1, headerColor)
										lcd.blit(label, ((float(line[1:2]) * charWidth) + (len(line[2:])* charWidth), i * charHeight + (i * spacing)))
										label = myfont.render("]", 1, headerColor)
										lcd.blit(label, (320 -charWidth, i * charHeight + (i * spacing)))
									closedPos = [(float(line[1:2]) * charWidth) + (len(line[2:])* charWidth) , i * charHeight + (i * spacing)]
									for b in boxStarts:
										if (b >= float(line[1:2])):
											boxStarts.remove(b)
									if (len(boxStarts) < 1 or (float(line[1:2]) <= boxStarts[len(boxStarts) - 1])):
										boxStarts.append(float(line[1:2]))
										ni = charWidth
									bi = i
								else: #not closed
									for b in boxStarts:
										if (b >= float(line[1:2])):
											boxStarts.remove(b)
								
							if (i * charHeight + (i * spacing) >= 240 - spacing):
								for r in range(0, 320, 15):
									lcd.fill(getAccent(backColor), (r, (238), 10, 2))
							i = i + 1
				rad = int(round((float(round(time.time()*1000)) - pressLen)) / 2)
				if (rad > dragShift and pressed != 0):
					rad = dragShift
					pressLen = int(round(time.time()*1000))
				if (rad > 500):
					rad = 500
				wid = int(round(float(rad) / 25))
				if (rad <= 1):
					rad = 2
				if (wid >= rad):
					wid = rad - 1
				if (wid < 1):
					wid = 1
				if (pressLen > 0):
					pygame.draw.circle(lcd, getAccent(headerColor), (tapPos[0], tapPos[1]), rad,wid)
				pygame.display.update()
				break


