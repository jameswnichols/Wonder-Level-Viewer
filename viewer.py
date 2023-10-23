import pygame
import math
import json

def distanceBetween(c1, c2):
    return math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)

def traceLinkBack(hash):
    currentHash = hash
    visited = []
    deletedBy = []

    while True:
        if currentHash not in REVERSE_LINKS or currentHash in visited:

            deletedBy = [x for x in deletedBy if x != currentHash]

            if deletedBy:
                print(f"!! Warning, stopped by {deletedBy} !!")

            return currentHash, deletedBy

        visited.append(currentHash)
        currentHash = REVERSE_LINKS[currentHash][-1]

        linkType = None

        for link in levelData["root"]["Links"]:
            if link["Dst"] == currentHash:
                linkType = link["Name"]
                if linkType == "Delete":
                    if link["Src"] not in deletedBy:
                        deletedBy.append(link["Src"])
                break

        for actor in levelData["root"]["Actors"]:
            if actor["Hash"] == currentHash:
                print(f"Traced Through :: {actor['Gyaml']}")
                break

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

def renderText(font : pygame.Font, text : str):

    characterWidth, characterHeight = font.size("e")

    darkOffsetX, darkOffsetY = characterWidth / 6, characterHeight / 6

    mainTextSurface = font.render(text, False, (255,255,255))

    mtWidth, mtHeight = mainTextSurface.get_size()

    finalSurface = pygame.Surface((mtWidth + darkOffsetX * 2, mtHeight + darkOffsetY * 2),pygame.SRCALPHA)

    textShadowSurface = font.render(text, False, (128,128,128))

    finalSurface.blit(textShadowSurface,(darkOffsetX, darkOffsetY))
    finalSurface.blit(mainTextSurface,(0,0))

    return finalSurface

def generateLogicLinks(levelData, objectCache):

    links = {}

    if "Links" not in levelData["root"]:
        return links
    
    for link in levelData["root"]["Links"]:

        destination, type, source = link["Dst"], link["Name"], link["Src"]

        destionationPosition = objectCache[destination]["position"]

        sourcePosition = objectCache[source]["position"]

        if source not in links:
            links[source] = {"send":[(destionationPosition,destination)],"recv":[]}
        else:
            links[source]["send"].append((destionationPosition,destination))
        
        if destination not in links:
            links[destination] = {"send":[],"recv":[(sourcePosition,source)]}
        else:
            links[destination]["recv"].append((sourcePosition,source))

    return links

def wrapNumber(x, min, max):
    x = min + (x - min) % (max - min)
    return x

def generateConnectionLine(start, end, offset):

    segments = []

    splitAmount = 100

    currentShiftOffset = splitAmount * offset

    currentSegment = []

    connected = 0
    isFilled = True

    xPerPoint = (end[0] - start[0]) / splitAmount
    yPerPoint = (end[1] - start[1]) / splitAmount

    for i in range(0, splitAmount):
        pointX = start[0] + (xPerPoint * i)
        pointY = start[1] + (yPerPoint * i)

        if connected == 0:
            currentSegment.append((pointX, pointY))
        if connected == 3:
            currentSegment.append((pointX, pointY))
            if isFilled:
                segments.append(currentSegment)
                isFilled = False
            else:
                isFilled = True

            connected = -1
            currentSegment = []
        
        connected += 1

    return segments
    

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720

UNIT_SIZE = 32
#Actual Size is 256  8 - 128

FONT = [pygame.font.Font("dogicapixelbold.ttf",x) for x in range(0,90)]

BOTTOM_ANCHOR = ["ObjectDokan"]

OBJECT_SIZES = {"ObjectDokan" : (2, 2), "ObjectDokanJoint" : (2, 2), "ObjectDokanMiddle" : (2, 2), "ObjectFountainDokan" : (2, 2), "BlockHatenaLong" : (3, 1)}

cameraX, cameraY = 0, 0

currentHoverHash = None

searchHash = None

searchDeleteList = []

clock = pygame.time.Clock()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

levelData = None

levelLinks = None

running = True

dt = 0

sinOffset = 0

mouseHeldDown = False
mouseStartX, mouseStartY = 0, 0
mouseStartCameraX, mouseStartCameraY = 0, 0

while running:

    currentHoverHash = None

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
                
                if not screenRect.colliderect(objectClipRect):
                    continue

                #Get rid of background stuff.
                if abs(position[2]) > UNIT_SIZE*4:
                    continue

                screenX = position[0] - cameraX
                screenY = SCREEN_HEIGHT - (position[1] - cameraY)

                # if hash in REVERSE_LINKS:
                #     pygame.draw.circle(screen,(0,255,0), ((screenX), (screenY)),2)

                #If the mouse is in the objects original box then check if it hits the lines
                if objectClipRect.colliderect(mouseRect) and clipLines(mouseRect,objectClipLines):
                    currentHoverHash = hash
                    
                    name = objectType

                    mouseTextList.append(name)

                    if hash in levelLinks:
                        inbound, outbound = levelLinks[hash]["recv"], levelLinks[hash]["send"]
                        # for (inboundX, inboundY, _), inboundHash in inbound:
                        #     pygame.draw.aaline(screen,(97,175,227),(screenX, screenY), (inboundX - cameraX, SCREEN_HEIGHT - (inboundY - cameraY)))

                        for (outboundX, outboundY, _), inboundHash in outbound:

                            lineSegments = generateConnectionLine((screenX, screenY),(outboundX - cameraX, SCREEN_HEIGHT - (outboundY - cameraY)),sinOffset)

                            for start, end in lineSegments:
                                pygame.draw.line(screen,(152,195,121),start,end,2)

                            #pygame.draw.aaline(screen,(152,195,121),(screenX, screenY), (outboundX - cameraX, SCREEN_HEIGHT - (outboundY - cameraY)))

                        #Outbound (152,195,121)
                        #Inbound (97,175,227)
                        #Delete (194,108,107)
                        

                # if hash == searchHash:
                #     pygame.draw.circle(screen,(0,0,255),(screenX,screenY),4)

                # if hash in searchDeleteList:
                #     pygame.draw.circle(screen,(255,0,255), ((screenX), (screenY)),4)

                #Render Bounding Boxes

                rotatedPoints = objectCache[hash]["points"]

                rotatedPoints = [(x - cameraX, SCREEN_HEIGHT - (y - cameraY)) for x, y in rotatedPoints]

                pygame.draw.polygon(screen, (249,249,249), rotatedPoints, 2) #249,249,249 2
    
    #Runs if no file is selected
    else:
        prompt = FONT[15].render("Drag and drop (...).json file here to open",False, (255,255,255))

        promptX, promptY = SCREEN_WIDTH//2 - prompt.get_width()//2, SCREEN_HEIGHT//2 - prompt.get_height()//2

        screen.blit(prompt, (promptX, promptY))


    for i, text in enumerate(mouseTextList):
        renderedText = renderText(FONT[15], text)
        #renderedText = FONT[15].render(text,False,(255,0,0)) #+"::"+str(hash)

        width = renderedText.get_size()[0]

        screen.blit(renderedText,(mouseX-width//2,mouseY - 20 - (i * 20)))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:
                if True: #currentHover not in REVERSE_LINKS
                    continue

                print(f"Find route for :: {currentHoverHash}")
                searchHash, searchDeleteList = traceLinkBack(currentHoverHash)

                for actor in levelData["root"]["Actors"]:
                    if actor["Hash"] == searchHash:

                        #Center the camera on the terminating actor.
                        position = actor["Translate"]
                        position = (position[0] * UNIT_SIZE, position[1] * UNIT_SIZE, position[2] * UNIT_SIZE)
                        cameraX, cameraY = position[0]-SCREEN_WIDTH//2, position[1]-SCREEN_HEIGHT//2

                        break

                print(f"Route leads to :: {searchHash}")

            if event.key == pygame.K_p:
                for actor in levelData["root"]["Actors"]:
                    if actor["Hash"] == currentHoverHash:
                        print(actor)
                        break

        if event.type == pygame.DROPFILE:
            filepath = event.file
            if filepath.split(".")[-1] == "json":
                try:
                    with open(filepath,"r") as f:
                        levelData = json.load(f)

                    # REVERSE_LINKS = {}

                    # for link in levelData["root"]["Links"]:
                    #     if link["Dst"] not in REVERSE_LINKS:
                    #         REVERSE_LINKS[link["Dst"]] = [link["Src"]]
                    #     else:
                    #         REVERSE_LINKS[link["Dst"]].append(link["Src"])
                    
                    objectCache = generateObjectCache(levelData)

                    levelLinks = generateLogicLinks(levelData, objectCache)

                    cameraX, cameraY = 0, 0
                except:
                    levelData = None
        
        # if event.type == pygame.MOUSEWHEEL:
        #     if event.y < 0:
        #         old = UNIT_SIZE-1
        #         UNIT_SIZE -= 4
        #         UNIT_SIZE = max(4, min(UNIT_SIZE, 128))
        #         cameraX = ((cameraX) / old) * UNIT_SIZE
                
        #     if event.y > 0:
        #         old = UNIT_SIZE+1
        #         UNIT_SIZE += 4
        #         UNIT_SIZE = max(4, min(UNIT_SIZE, 128))
        #         cameraX = (cameraX / old) * UNIT_SIZE
            
        #     objectCache = generateObjectCache(levelData)

    pressedKeys = pygame.key.get_pressed()

    if not mouseHeldDown:
        if pressedKeys[pygame.K_d]:
            cameraX += 2 * dt
        if pressedKeys[pygame.K_a]:
            cameraX -= 2 * dt
        if pressedKeys[pygame.K_w]:
            cameraY += 2 * dt
        if pressedKeys[pygame.K_s]:
            cameraY -= 2 * dt

    if pygame.mouse.get_pressed()[0] and not mouseHeldDown:
        mouseHeldDown = True
        mouseStartX, mouseStartY = pygame.mouse.get_pos()
        mouseStartCameraX, mouseStartCameraY = cameraX, cameraY
    elif not pygame.mouse.get_pressed()[0] and mouseHeldDown:
        mouseHeldDown = False
    
    if mouseHeldDown:
        mouseX, mouseY = pygame.mouse.get_pos()
        mouseDeltaX, mouseDeltaY = mouseStartX - mouseX, mouseStartY - mouseY

        cameraX, cameraY = mouseStartCameraX + mouseDeltaX, mouseStartCameraY - mouseDeltaY

    pygame.display.flip()
    dt = clock.tick(120)

    fps = clock.get_fps()
    pygame.display.set_caption(f"Wonder Level Viewer - FPS: {round(fps,1)}")

    sinOffset += 1 * dt
    sinOffset = wrapNumber(sinOffset, 0, 1)


pygame.quit()