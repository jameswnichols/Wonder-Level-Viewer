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

    for actor in levelData["root"]["Actors"]:
        objectType, position, hash = actor["Gyaml"], actor["Translate"], actor["Hash"]

        position = (position[0] * UNIT_SIZE, position[1] * UNIT_SIZE, position[2] * UNIT_SIZE)

        objectRotation = actor["Rotate"][2] * -1

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

        objectCache[hash] = {"points": rotatedPoints, "clipRect": objectRect}

    return objectCache

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720

UNIT_SIZE = 32
#Actual Size is 256

FONT = [pygame.font.Font("dogicapixelbold.ttf",x) for x in range(0,90)]

BOTTOM_ANCHOR = ["ObjectDokan"]

OBJECT_SIZES = {"ObjectDokan" : (2, 2)}

cameraX, cameraY = 0, 0

currentHoverHash = None

searchHash = None

searchDeleteList = []

clock = pygame.time.Clock()

#GET FILE UPLOAD
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Wonder Level Viewer")
gotFile = False
runFilePreview = True
filepath = None

while runFilePreview:
    screen.fill((0,0,0))

    prompt = FONT[15].render("Drag and drop x.json file here to open",False, (255,255,255))

    promptX, promptY = SCREEN_WIDTH//2 - prompt.get_width()//2, SCREEN_HEIGHT//2 - prompt.get_height()//2

    screen.blit(prompt, (promptX, promptY))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            runFilePreview = False

        if event.type == pygame.DROPFILE:
            filepath = event.file
            if filepath.split(".")[-1] == "json":
                gotFile = True
                runFilePreview = False
    
    pygame.display.flip()
    clock.tick(60)

with open(filepath,"r") as f:
    levelData = json.load(f)

REVERSE_LINKS = {}

for link in levelData["root"]["Links"]:
    if link["Dst"] not in REVERSE_LINKS:
        REVERSE_LINKS[link["Dst"]] = [link["Src"]]
    else:
        REVERSE_LINKS[link["Dst"]].append(link["Src"])

running = gotFile

dt = 0

objectCache = generateObjectCache(levelData)

while running:

    currentHoverHash = None

    textHoverOffset = 0

    screen.fill((255,255,255))

    screenMinX, screenMaxX = cameraX, (cameraX + SCREEN_WIDTH)

    screenMinY, screenMaxY = cameraY, (cameraY + SCREEN_HEIGHT)

    mouseTextList = []

    if "BgUnits" in levelData["root"]:
        for section in levelData["root"]["BgUnits"]:
            if "BeltRails" not in section:
                continue

            for wall in section["Walls"]:
                data = wall["ExternalRail"]
                isClosed, rawPoints = data["IsClosed"], data["Points"]
                points = []
                for point in rawPoints:
                    position = point["Translate"]
                    points.append([(position[0]*UNIT_SIZE)-cameraX,SCREEN_HEIGHT-((position[1]*UNIT_SIZE)-cameraY-1)]) #+UNIT_SIZE//2 -UNIT_SIZE//2
                
                pygame.draw.polygon(screen,(127,51,0),points)
            
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
                
                pygame.draw.lines(screen,(38,127,0),isClosed,points,width=4)

    for actor in levelData["root"]["Actors"]:
        objectType, position, hash = actor["Gyaml"], actor["Translate"], actor["Hash"]

        position = (position[0] * UNIT_SIZE, position[1] * UNIT_SIZE, position[2] * UNIT_SIZE)

        objectClipRect = objectCache[hash]["clipRect"]

        screenRect = pygame.Rect(cameraX, cameraY, SCREEN_WIDTH, SCREEN_HEIGHT)

        #used to detect when mouse is nearby object bounding boxes.
        mouseX, mouseY = pygame.mouse.get_pos()

        mouseRect = pygame.Rect(mouseX - 2.5 + cameraX, (SCREEN_HEIGHT-mouseY) - 2.5 + cameraY, 5, 5)
        
        if not screenRect.colliderect(objectClipRect):
             continue

        #Get rid of background stuff.
        if abs(position[2]) > UNIT_SIZE*4:
            continue

        screenX = position[0] - cameraX
        screenY = SCREEN_HEIGHT - (position[1] - cameraY)

        if hash not in REVERSE_LINKS:
            pygame.draw.circle(screen,(255,0,0), ((screenX), (screenY)),2)
        else:

            pygame.draw.circle(screen,(0,255,0), ((screenX), (screenY)),2)

        #distanceFromMouse = distanceBetween((screenX,screenY),pygame.mouse.get_pos())

        if objectClipRect.colliderect(mouseRect) and not( objectClipRect.contains(mouseRect)):

            currentHoverHash = hash
            
            name = objectType

            mouseTextList.append(name)

        if hash == searchHash:
            pygame.draw.circle(screen,(0,0,255),(screenX,screenY),4)

        if hash in searchDeleteList:
            pygame.draw.circle(screen,(255,0,255), ((screenX), (screenY)),4)

        #Render Bounding Boxes

        rotatedPoints = objectCache[hash]["points"]

        rotatedPoints = [(x - cameraX, SCREEN_HEIGHT - (y - cameraY)) for x, y in rotatedPoints]

        pygame.draw.polygon(screen, (255,0,0), rotatedPoints, 1)

    for i, text in enumerate(mouseTextList):
        renderedText = FONT[15].render(text,False,(255,0,0)) #+"::"+str(hash)

        width = renderedText.get_size()[0]

        screen.blit(renderedText,(mouseX-width//2,mouseY - 20 - (i * 20)))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                if currentHoverHash not in REVERSE_LINKS:
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

    pressedKeys = pygame.key.get_pressed()

    if pressedKeys[pygame.K_d]:
        cameraX += 2 * dt
    if pressedKeys[pygame.K_a]:
        cameraX -= 2 * dt
    if pressedKeys[pygame.K_w]:
        cameraY += 2 * dt
    if pressedKeys[pygame.K_s]:
        cameraY -= 2 * dt

    pygame.display.flip()
    dt = clock.tick(120)

    fps = clock.get_fps()
    pygame.display.set_caption(f"Wonder Level Viewer - FPS: {round(fps,1)}")

pygame.quit()