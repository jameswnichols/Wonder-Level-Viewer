import yaml
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

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600

UNIT_SIZE = 32
#Actual Size is 256

FONT = [pygame.font.Font("dogicapixelbold.ttf",x) for x in range(0,90)]

STATIC_LOOKUP = {"ObjectGoalPole":"END","PlayerLocator":"START","ObjectWonderTag":"START SEED","ItemWonderFinishWonderSead":"END SEED","RetryPoint":"CHECKPOINT","ObjectTalkingFlower":"TALKING FLOWER","ObjectTalkingFlowerS":"TALKING FLOWER"}

OBJECT_LOOKUP = {"ObjectMiniFlowerInAir":"MINI WONDER FLOWER","ObjectCoinYellow":"COIN","ObjectMiniLuckyCoin":"MINI WONDER COIN","ObjectCoinRandom":"WONDER COIN","ObjectBigTenLuckyCoin":"10 WONDER COIN","BlockRengaLight":"EMPTY BRICK","BlockRengaItem":"BRICK WITH COIN","BlockHatena":"? BLOCK","ObjectBlockSurpriseYellow":"HIDDEN ? BLOCK"}

BLOCK_LOOKUP = {"BlockRengaItem":(141,79,58),"BlockRengaLight":(141,79,58),"BlockHatena":(255,211,36),"ObjectBlockSurpriseYellow":(255,211,36,155)}

CIRCLE_LOOKUP = {"ObjectCoinYellow":(234,220,111)}

SMALL_CIRCLE_LOOKUP = {"ObjectMiniLuckyCoin":(203,87,253)}

LARGE_CIRCLE_LOOKUP = {"ObjectBigTenLuckyCoin":(203,87,253)}

cameraX, cameraY = 0, 0

currentHoverHash = None

searchHash = None

searchDeleteList = []

with open("level.json","r") as f:
    levelData = json.load(f)

REVERSE_LINKS = {}

for link in levelData["root"]["Links"]:
    if link["Dst"] not in REVERSE_LINKS:
        REVERSE_LINKS[link["Dst"]] = [link["Src"]]
    else:
        REVERSE_LINKS[link["Dst"]].append(link["Src"])

for actor in levelData["root"]["Actors"]:
    objectType, position = actor["Gyaml"], actor["Translate"]
    if "tag" in objectType.lower():
        pass
        #print(actor["Hash"])
    #print(f"{objectType} :: {position}")

running = True

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

clock = pygame.time.Clock()

dt = 0

while running:

    currentHoverHash = None

    screen.fill((255,255,255))

    screenMinX, screenMaxX = cameraX, (cameraX + SCREEN_WIDTH)

    screenMinY, screenMaxY = cameraY, (cameraY + SCREEN_HEIGHT)

    for actor in levelData["root"]["Actors"]:
        objectType, position, hash = actor["Gyaml"], actor["Translate"], actor["Hash"]

        if objectType.startswith("MapObj"):
            continue

        position = (position[0] * UNIT_SIZE, position[1] * UNIT_SIZE, position[2] * UNIT_SIZE)

        if position[0] >= screenMinX and position[0] <= screenMaxX:
            if position[1] >= screenMinY and position[1] <= screenMaxY:
                if abs(position[2]) <= UNIT_SIZE*2:

                    screenX = position[0] - cameraX
                    screenY = SCREEN_HEIGHT - (position[1] - cameraY)

                    if hash not in REVERSE_LINKS:
                        pygame.draw.circle(screen,(255,0,0), ((screenX), (screenY)),2)
                    else:

                        pygame.draw.circle(screen,(0,255,0), ((screenX), (screenY)),2)

                    if distanceBetween((screenX,screenY),pygame.mouse.get_pos()) < 10:
                        currentHoverHash = hash

                    if objectType in STATIC_LOOKUP:
                        
                        info = STATIC_LOOKUP[objectType]

                        text = FONT[15].render(info,False,(255,0,0))

                        width = text.get_size()[0]

                        screen.blit(text,(screenX-width//2,screenY-20))

                    elif distanceBetween((screenX,screenY),pygame.mouse.get_pos()) < 10:
                        
                        name = OBJECT_LOOKUP[objectType] if objectType in OBJECT_LOOKUP else objectType

                        text = FONT[15].render(name,False,(255,0,0)) #+"::"+str(hash)

                        width = text.get_size()[0]

                        screen.blit(text,(screenX-width//2,screenY-20))
                    
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


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                if currentHoverHash in REVERSE_LINKS:
                    print(f"Find route for :: {currentHoverHash}")
                    searchHash, searchDeleteList = traceLinkBack(currentHoverHash)

                    for actor in levelData["root"]["Actors"]:
                        if actor["Hash"] == searchHash:
                            position = actor["Translate"]
                            position = (position[0] * UNIT_SIZE, position[1] * UNIT_SIZE, position[2] * UNIT_SIZE)
                            cameraX, cameraY = position[0]-SCREEN_WIDTH//2, position[1]-SCREEN_HEIGHT//2

                            if actor["Gyaml"] == "FloweringCheckTag":
                                pass
                            break

                    print(f"Route leads to :: {searchHash}")

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

pygame.quit()