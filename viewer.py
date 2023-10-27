import pygame
import math
import json
import toolkitTranslate

def distanceBetween(c1, c2):
    return math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)

def rotatePoint(pivotPoint, rotatePoint, angle):

    pivotX, pivotY = pivotPoint

    x, y = rotatePoint

    sin = math.sin(angle)
    cos = math.cos(angle)

    originX = x - pivotX
    originY = y - pivotY

    newX = originX * cos - originY * sin
    newY = originX * sin + originY * cos

    return (newX + pivotX, newY + pivotY)

def generatePoints(pivotPoint, scale, objectSize, isBottomMiddle = False):

    centerX, centerY = pivotPoint

    scaleX, scaleY = scale

    sizeX, sizeY = objectSize

    yAnchorOffset = ((UNIT_SIZE//2) * scaleY  * sizeY) if isBottomMiddle else 0
    
    xOffset = (UNIT_SIZE//2) * scaleX * sizeX

    yOffset = (UNIT_SIZE//2) * scaleY * sizeY

    points = [(centerX - xOffset, centerY - yOffset - yAnchorOffset),(centerX + xOffset, centerY - yOffset - yAnchorOffset), (centerX + xOffset, centerY + yOffset - yAnchorOffset), (centerX - xOffset, centerY + yOffset - yAnchorOffset)]

    return points

def generateObjectCache(levelData):
    objectCache = {}

    prettyRotationAdjustments = {3.14159:math.pi,-3.14159:-math.pi,1.5708:90 * (math.pi/180),-1.5708:-90 * (math.pi/180)}

    for actor in levelData["root"]["Actors"]:
        objectType, position, hash = actor["Gyaml"], actor["Translate"], actor["Hash"]

        position = (position[0] * UNIT_SIZE, position[1] * UNIT_SIZE, position[2] * UNIT_SIZE)

        objectRotation = actor["Rotate"][2]

        objectRotation = prettyRotationAdjustments[objectRotation] if objectRotation in prettyRotationAdjustments else objectRotation

        objectRotation += math.pi

        objectScaleX, objectScaleY, _ = actor["Scale"]

        pivotPoint = (position[0], position[1])

        bottomAnchor = (objectType in BOTTOM_ANCHOR) or ("enemy" in objectType.lower())

        objectSize = OBJECT_SIZES[objectType] if objectType in OBJECT_SIZES else (1, 1)

        pointsOnOutline = generatePoints(pivotPoint, (objectScaleX, objectScaleY), objectSize, bottomAnchor)

        rotatedPoints = [rotatePoint(pivotPoint, point, objectRotation) for point in pointsOnOutline]

        pointXs, pointYs = [x[0] for x in rotatedPoints], [y[1] for y in rotatedPoints]

        smallestX, biggestX = min(pointXs), max(pointXs)
        smallestY, biggestY = min(pointYs), max(pointYs)

        objectRect = pygame.Rect(smallestX, smallestY, biggestX - smallestX, biggestY - smallestY)

        clipLines = [[rotatedPoints[0],rotatedPoints[1]],[rotatedPoints[1],rotatedPoints[2]],[rotatedPoints[2],rotatedPoints[3]],[rotatedPoints[3],rotatedPoints[0]]]

        objectCache[hash] = {"points": rotatedPoints, "clipRect": objectRect,"clipLines":clipLines,"position":position}

    return objectCache

def clipLines(rect : pygame.Rect, lines : list[list[tuple]]):
    for p1, p2 in lines:
        if rect.clipline(p1, p2):
            return True
    
    return False

def renderText(font : pygame.Font, text : str, color : tuple):

    characterWidth, characterHeight = font.size("e")

    darkOffsetX, darkOffsetY = characterWidth / 6, characterHeight / 6

    mainTextSurface = font.render(text, False, color) #(255,255,255)

    mtWidth, mtHeight = mainTextSurface.get_size()

    finalSurface = pygame.Surface((mtWidth + darkOffsetX * 2, mtHeight + darkOffsetY * 2),pygame.SRCALPHA)

    textShadowSurface = font.render(text, False, [math.ceil(x/2) for x in color])

    finalSurface.blit(textShadowSurface,(darkOffsetX, darkOffsetY))
    finalSurface.blit(mainTextSurface,(0,0))

    return finalSurface, (mtWidth, mtHeight)

def generateLogicLinks(levelData, objectCache):

    links = {}

    if "Links" not in levelData["root"]:
        return links
    
    for link in levelData["root"]["Links"]:

        destination, type, source = link["Dst"], link["Name"], link["Src"]

        try:
            destionationPosition = objectCache[destination]["position"]

            sourcePosition = objectCache[source]["position"]
        except:
            continue

        if source not in links:
            links[source] = {"send":[(destionationPosition,destination,type)],"recv":[]}
        else:
            links[source]["send"].append((destionationPosition,destination,type))
        
        if destination not in links:
            links[destination] = {"send":[],"recv":[(sourcePosition,source,type)]}
        else:
            links[destination]["recv"].append((sourcePosition,source,type))

    return links

def wrapNumber(x, min, max):
    x = min + (x - min) % (max - min)
    return x


def generateConnectionLine(start, end, offset):

    maxDistanceFromSource = 6

    overlapDelay = 10

    lineLength = math.sqrt((start[0] - end[0]) ** 2 + (start[1] - end[1]) ** 2)

    splitAmount = min(int(lineLength / 6),MAX_TRACE_SAMPLES) #6

    currentPulseIndex = (splitAmount + overlapDelay) * offset

    points = []

    if splitAmount == 0 or lineLength > MAX_TRACE_LENGTH:
        return points

    xPerPoint = (end[0] - start[0]) / splitAmount
    yPerPoint = (end[1] - start[1]) / splitAmount

    for i in range(0, int(splitAmount)):
        pointX = start[0] + (xPerPoint * i)
        pointY = start[1] + (yPerPoint * i)

        distanceFromIndex = min(abs(currentPulseIndex - i), abs((currentPulseIndex-(splitAmount + overlapDelay)) - i))

        distanceInverse = maxDistanceFromSource - max(0, min(distanceFromIndex, maxDistanceFromSource))

        radiusPercentage = 1.5 * (distanceInverse / maxDistanceFromSource) + 1

        points.append(((pointX, pointY), radiusPercentage))

    return points, points[(len(points)//2)-1][0], lineLength

def renderLinkLine(screen, type, startPoint, endPoint, pulseOffset):

    output = generateConnectionLine(startPoint,endPoint,pulseOffset)

    if output == []:
        return

    points, midPoint, lineLength = output
    
    color = LINK_COLOURS[type] if type in LINK_COLOURS else (97,175,227)

    for pos, size in points:
            pygame.draw.circle(screen, color, pos, 2*size)

    if type in LINK_SYMBOLS and lineLength > 100:
        icon, textColor = LINK_SYMBOLS[type]
        textRender, textSize = renderText(FONT[20],icon,textColor)

        newPointX, newPointY = midPoint[0] - textSize[0]//2, midPoint[1] - textRender.get_height()//2

        screen.blit(textRender,(newPointX, newPointY))

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720

SCREEN_CLIP = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)

UNIT_SIZE = 32
#Actual Size is 256  8 - 128

FONT = [pygame.font.Font("dogicapixelbold.ttf",x) for x in range(0,90)]

BOTTOM_ANCHOR = ["ObjectDokan","ObjectTalkingFlower"]

OBJECT_SIZES = {"ObjectDokan" : (2, 2), "ObjectDokanJoint" : (2, 2), "ObjectDokanMiddle" : (2, 2), "ObjectFountainDokan" : (2, 2), "BlockHatenaLong" : (3, 1)}

LINK_SYMBOLS = {"Delete":("X",(224,108,117)),"Create":("+",(152,195,121))}

LINK_COLOURS = {"Delete":(224,108,117),"Create":(152,195,121)}

MAX_TRACE_LENGTH = 1500

MAX_TRACE_SAMPLES = 150

cameraX, cameraY = 0, 0

hoverHashList = []

selectedHashList = []

searchHash = None

searchDeleteList = []

clock = pygame.time.Clock()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

levelData = None

levelLinks = None

running = True

dt = 0

pulseOffset = 0

mouseHeldDown = False
mouseStartX, mouseStartY = 0, 0
mouseStartCameraX, mouseStartCameraY = 0, 0

renderHashes = []

while running:

    hoverHashList = []
    
    renderHashes = []

    textHoverOffset = 0

    screen.fill((33,37,43)) #(33,37,43)

    screenMinX, screenMaxX = cameraX, (cameraX + SCREEN_WIDTH)

    screenMinY, screenMaxY = cameraY, (cameraY + SCREEN_HEIGHT)

    mouseTextList = []

    #Check that a level has been loaded
    if levelData:
        if "BgUnits" in levelData["root"]:
            for section in levelData["root"]["BgUnits"]:
                if "Walls" in section:
                    for wall in section["Walls"]:
                        data = wall["ExternalRail"]
                        isClosed, rawPoints = data["IsClosed"], data["Points"]
                        points = []
                        for point in rawPoints:
                            position = point["Translate"]
                            points.append([(position[0]*UNIT_SIZE)-cameraX,SCREEN_HEIGHT-((position[1]*UNIT_SIZE)-cameraY-1)]) #+UNIT_SIZE//2 -UNIT_SIZE//2
                        
                        pygame.draw.polygon(screen,(96,52,30),points) #127 51 0
                
                if "BeltRails" in section:
                    for floor in section["BeltRails"]:
                        isClosed = floor["IsClosed"]
                        points = []
                        for point in floor["Points"]:
                            position = point["Translate"]
                            relativeLocation = [(position[0]*UNIT_SIZE)-cameraX,SCREEN_HEIGHT-((position[1]*UNIT_SIZE)-cameraY-1)] #+UNIT_SIZE//2 -UNIT_SIZE//2
                            points.append(relativeLocation)

                            if distanceBetween(relativeLocation,pygame.mouse.get_pos()) < 10 and pygame.key.get_pressed()[pygame.K_m]:
                                txt = FONT[10].render(f"{position}",False,(255,0,0))
                                screen.blit(txt,(relativeLocation[0]-txt.get_width()//2,relativeLocation[1]-10))
                        
                        pygame.draw.lines(screen,(149,190,119),isClosed,points,width=4) #38,127,0

        if "Actors" in levelData["root"]:
            for actor in levelData["root"]["Actors"]:
                objectType, position, hash = actor["Gyaml"], actor["Translate"], actor["Hash"]

                position = (position[0] * UNIT_SIZE, position[1] * UNIT_SIZE, position[2] * UNIT_SIZE)

                objectClipRect = objectCache[hash]["clipRect"]

                objectClipLines = objectCache[hash]["clipLines"]

                screenRect = pygame.Rect(cameraX, cameraY, SCREEN_WIDTH, SCREEN_HEIGHT)

                #used to detect when mouse is nearby object bounding boxes.
                mouseX, mouseY = pygame.mouse.get_pos()

                mouseRect = pygame.Rect(mouseX - 5 + cameraX, (SCREEN_HEIGHT-mouseY) - 5 + cameraY, 10, 10)
                
                if (not screenRect.colliderect(objectClipRect)) and hash not in selectedHashList:
                    continue

                #Get rid of background stuff.
                if abs(position[2]) > UNIT_SIZE*4:
                    continue

                screenX = position[0] - cameraX
                screenY = SCREEN_HEIGHT - (position[1] - cameraY)

                #If the mouse is in the objects original box then check if it hits the lines

                mouseTouchingObject = (objectClipRect.colliderect(mouseRect) and clipLines(mouseRect,objectClipLines))

                if mouseTouchingObject or hash in selectedHashList:
                    
                    if mouseTouchingObject:
                        hoverHashList.append(hash)
                        
                        name = objectType

                        mouseTextList.append(name)

                    if hash in levelLinks:

                        renderHashes.append((hash, (screenX, screenY)))

                        #Outbound (152,195,121)
                        #Inbound (97,175,227)
                        #Delete (194,108,107)

                #Render Bounding Boxes

                rotatedPoints = objectCache[hash]["points"]

                rotatedPoints = [(x - cameraX, SCREEN_HEIGHT - (y - cameraY)) for x, y in rotatedPoints]
                
                color = (249,249,249)

                if hash in selectedHashList:
                    color = (229,192,123)

                pygame.draw.polygon(screen, color , rotatedPoints, 2) #249,249,249 2
    
    #Runs if no file is selected
    else:
        prompt = FONT[15].render("Drag and drop (...).yaml file here to open",False, (255,255,255))

        promptX, promptY = SCREEN_WIDTH//2 - prompt.get_width()//2, SCREEN_HEIGHT//2 - prompt.get_height()//2

        screen.blit(prompt, (promptX, promptY))

    for hash, (screenX, screenY) in renderHashes:
        inbound, outbound = levelLinks[hash]["recv"], levelLinks[hash]["send"]

        for (inboundX, inboundY, _), inboundHash, type in inbound:
            
            renderLinkLine(screen,type,(inboundX - cameraX, SCREEN_HEIGHT - (inboundY - cameraY)),(screenX, screenY),pulseOffset)

        for (outboundX, outboundY, _), outboundHash, type in outbound:
            
            renderLinkLine(screen,type,(screenX, screenY),(outboundX - cameraX, SCREEN_HEIGHT - (outboundY - cameraY)),pulseOffset)


    for i, text in enumerate(mouseTextList):
        renderedText, size = renderText(FONT[15], text, (255,255,255))

        width = size[0]

        screen.blit(renderedText,(mouseX-width//2,mouseY - 20 - (i * 20)))


    #Handle user input + dragging
    pressedKeys = pygame.key.get_pressed()

    if not mouseHeldDown:
        if pressedKeys[pygame.K_d]:
            cameraX += 2000 * dt
        if pressedKeys[pygame.K_a]:
            cameraX -= 2000 * dt
        if pressedKeys[pygame.K_w]:
            cameraY += 2000 * dt
        if pressedKeys[pygame.K_s]:
            cameraY -= 2000 * dt

    if pygame.mouse.get_pressed()[2] and not mouseHeldDown:
        mouseHeldDown = True
        mouseStartX, mouseStartY = pygame.mouse.get_pos()
        mouseStartCameraX, mouseStartCameraY = cameraX, cameraY
    elif not pygame.mouse.get_pressed()[2] and mouseHeldDown:
        mouseHeldDown = False
    
    if mouseHeldDown:
        mouseX, mouseY = pygame.mouse.get_pos()
        mouseDeltaX, mouseDeltaY = mouseStartX - mouseX, mouseStartY - mouseY

        cameraX, cameraY = mouseStartCameraX + mouseDeltaX, mouseStartCameraY - mouseDeltaY

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                for hash in hoverHashList:
                    if hash in selectedHashList:
                        selectedHashList.remove(hash)
                    else:
                        selectedHashList.append(hash)
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                for actor in levelData["root"]["Actors"]:
                    if actor["Hash"] in hoverHashList:
                        print(actor)

        if event.type == pygame.DROPFILE:
            filepath = event.file
            if filepath.split(".")[-1] == "yaml":
                try:
                    #with open(filepath,"r") as f:
                    levelData = toolkitTranslate.yamlToJson(filepath, True)

                    objectCache = generateObjectCache(levelData)

                    levelLinks = generateLogicLinks(levelData, objectCache)

                    cameraX, cameraY = 0, 0
                except:
                    levelData = None

    pygame.display.flip()
    dt = clock.tick(240)/1000

    fps = clock.get_fps()
    pygame.display.set_caption(f"Wonder Level Viewer - FPS: {round(fps,1)}")

    pulseOffset += 1 * dt
    pulseOffset = wrapNumber(pulseOffset, 0, 1)


pygame.quit()