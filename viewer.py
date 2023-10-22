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


pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720

UNIT_SIZE = 32
#Actual Size is 256

FONT = [pygame.font.Font("dogicapixelbold.ttf",x) for x in range(0,90)]

STATIC_LOOKUP = {"ObjectGoalPole":"END","PlayerLocator":"START","ObjectWonderTag":"START SEED","ItemWonderFinishWonderSead":"END SEED","RetryPoint":"CHECKPOINT","ObjectTalkingFlower":"TALKING FLOWER","ObjectTalkingFlowerS":"TALKING FLOWER"}

OBJECT_LOOKUP = {"ObjectMiniFlowerInAir":"MINI WONDER FLOWER","ObjectCoinYellow":"COIN","ObjectMiniLuckyCoin":"MINI WONDER COIN","ObjectCoinRandom":"WONDER COIN","ObjectBigTenLuckyCoin":"10 WONDER COIN","BlockRengaLight":"EMPTY BRICK","BlockRengaItem":"BRICK WITH COIN","BlockHatena":"? BLOCK","BlockClarity":"HIDDEN ? BLOCK","ObjectDokan":"PIPE"} #ObjectBlockSurpriseYellow

BLOCK_LOOKUP = {"BlockRengaItem":(141,79,58),"BlockRengaLight":(141,79,58),"BlockHatena":(255,211,36),"BlockClarity":(255,211,36,155)}

CIRCLE_LOOKUP = {"ObjectCoinYellow":(234,220,111)}

SMALL_CIRCLE_LOOKUP = {"ObjectMiniLuckyCoin":(203,87,253)}

LARGE_CIRCLE_LOOKUP = {"ObjectBigTenLuckyCoin":(203,87,253)}

cameraX, cameraY = 0, 0

currentHoverHash = None

searchHash = None

searchDeleteList = []

with open("Course1.json","r") as f:
    levelData = json.load(f)

REVERSE_LINKS = {}

for link in levelData["root"]["Links"]:
    if link["Dst"] not in REVERSE_LINKS:
        REVERSE_LINKS[link["Dst"]] = [link["Src"]]
    else:
        REVERSE_LINKS[link["Dst"]].append(link["Src"])
#3
# for actor in levelData["root"]["Actors"]:
#     objectType, position = actor["Gyaml"], actor["Translate"]
#     if objectType == "ObjectDokan":
#         print(actor)

running = True

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

clock = pygame.time.Clock()

dt = 0

while running:

    currentHoverHash = None

    textHoverOffset = 0

    screen.fill((255,255,255))

    screenMinX, screenMaxX = cameraX, (cameraX + SCREEN_WIDTH)

    screenMinY, screenMaxY = cameraY, (cameraY + SCREEN_HEIGHT)

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
                    points.append([(position[0]*UNIT_SIZE)-cameraX+UNIT_SIZE//2,SCREEN_HEIGHT-((position[1]*UNIT_SIZE)-UNIT_SIZE//2-cameraY-1)])
                
                pygame.draw.polygon(screen,(127,51,0),points)
            
            for floor in section["BeltRails"]:
                isClosed = floor["IsClosed"]
                points = []
                for point in floor["Points"]:
                    position = point["Translate"]
                    relativeLocation = [(position[0]*UNIT_SIZE)-cameraX+UNIT_SIZE//2,SCREEN_HEIGHT-((position[1]*UNIT_SIZE)-UNIT_SIZE//2-cameraY-1)]
                    points.append(relativeLocation)

                    if distanceBetween(relativeLocation,pygame.mouse.get_pos()) < 10 and pygame.key.get_pressed()[pygame.K_m]:
                        txt = FONT[10].render(f"{position}",False,(255,0,0))
                        screen.blit(txt,(relativeLocation[0]-txt.get_width()//2,relativeLocation[1]-10))
                
                pygame.draw.lines(screen,(38,127,0),isClosed,points,width=4)

    for actor in levelData["root"]["Actors"]:
        objectType, position, hash = actor["Gyaml"], actor["Translate"], actor["Hash"]

        if objectType.startswith("MapObj"):
            continue

        position = (position[0] * UNIT_SIZE, position[1] * UNIT_SIZE, position[2] * UNIT_SIZE)

        if objectType == "ObjectDokan":
            position = (position[0] - UNIT_SIZE//2, position[1] + UNIT_SIZE//2, position[2])

        #Make sure its in the visible area.
        if not (screenMinX <= position[0] <= screenMaxX):
            continue
        if not (screenMinY <= position[1] <= screenMaxY):
            continue
        if abs(position[2]) > UNIT_SIZE*4:
            continue

        screenX = position[0] - cameraX
        screenY = SCREEN_HEIGHT - (position[1] - cameraY)

        if hash not in REVERSE_LINKS:
            pygame.draw.circle(screen,(255,0,0), ((screenX), (screenY)),2)
        else:

            pygame.draw.circle(screen,(0,255,0), ((screenX), (screenY)),2)

        distanceFromMouse = distanceBetween((screenX,screenY),pygame.mouse.get_pos())

        if distanceFromMouse < 5:
            currentHoverHash = hash

        if objectType in STATIC_LOOKUP:
            
            info = STATIC_LOOKUP[objectType]

            text = FONT[15].render(info,False,(255,0,0))

            width = text.get_size()[0]

            screen.blit(text,(screenX-width//2,screenY-20))

        elif distanceFromMouse < 5:
            
            name = OBJECT_LOOKUP[objectType] if objectType in OBJECT_LOOKUP else objectType

            text = FONT[15].render(name,False,(255,0,0)) #+"::"+str(hash)

            width = text.get_size()[0]

            screen.blit(text,(screenX-width//2,screenY-20+textHoverOffset))

            textHoverOffset -= 20
        
        if objectType in BLOCK_LOOKUP:

            block = pygame.Surface((UNIT_SIZE,UNIT_SIZE),pygame.SRCALPHA)
            block.fill(BLOCK_LOOKUP[objectType])

            screen.blit(block, (screenX, screenY))
        
        if objectType in CIRCLE_LOOKUP or objectType in SMALL_CIRCLE_LOOKUP or objectType in LARGE_CIRCLE_LOOKUP:
            centerX = screenX + UNIT_SIZE//2
            centerY = screenY + UNIT_SIZE//2

            if objectType in CIRCLE_LOOKUP:
                radius = UNIT_SIZE//2
                colour = CIRCLE_LOOKUP[objectType]
            elif objectType in SMALL_CIRCLE_LOOKUP:
                radius = UNIT_SIZE//4
                colour = SMALL_CIRCLE_LOOKUP[objectType]
            elif objectType in LARGE_CIRCLE_LOOKUP:
                radius = UNIT_SIZE
                colour = LARGE_CIRCLE_LOOKUP[objectType]

            pygame.draw.circle(screen,colour,(centerX,centerY),radius)

        if hash == searchHash:
            pygame.draw.circle(screen,(0,0,255),(screenX,screenY),4)

        if hash in searchDeleteList:
            pygame.draw.circle(screen,(255,0,255), ((screenX), (screenY)),4)  

        if objectType == "ObjectDokan":
            pipeHeight = actor["Scale"][1]
            pipeAngle = actor["Rotate"][2]

            actualPipeHeight = ((4/3) * UNIT_SIZE) * pipeHeight

            pipeWidth = 2 * UNIT_SIZE

            pivotPoint = (screenX, screenY)

            points = [(screenX, screenY),(screenX, screenY - actualPipeHeight),(screenX + pipeWidth,screenY - actualPipeHeight),(screenX + pipeWidth, screenY)]

            rotatedPoints = [rotatePoint(pivotPoint, point, pipeAngle) for point in points]

            pygame.draw.polygon(screen, (68,161,61), rotatedPoints)
            
            #(68,161,61)
            #screen.blit(pipeSurface,(rotatedX,rotatedY))
        
        if pygame.key.get_pressed()[pygame.K_o]:
            
            objectRotation = actor["Rotate"][2]

            pivotPoint = (screenX, screenY)

            pointsOnOutline = [(screenX, screenY),(screenX + UNIT_SIZE, screenY),(screenX + UNIT_SIZE, screenY + UNIT_SIZE),(screenX, screenY + UNIT_SIZE)]

            rotatedPoints = [rotatePoint(pivotPoint, point, objectRotation) for point in pointsOnOutline]

            furthestLeftX = min([x[0] for x in rotatedPoints])
            furthestUpY = min([y[1] for y in rotatedPoints])

            offsetX, offsetY = screenX - furthestLeftX, screenY - furthestUpY

            rotatedPoints = [(x+offsetX, y+offsetY) for x, y in rotatedPoints]

            pygame.draw.polygon(screen, (255,0,0), rotatedPoints, 1)

            # outline = pygame.Rect(screenX, screenY, UNIT_SIZE, UNIT_SIZE)
            # pygame.draw.rect(screen, (255,0,0), outline, 1)

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