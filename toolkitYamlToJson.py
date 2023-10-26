import json

#5 places of float precision.

class LevelData:
    def __init__(self):
        self.levelData = {}
        self.currentPath = {}

    def navigatePath(self, stepBackAmount : int = 0, ignoreIndex : bool = False):
        counter = 0
        currentLevel = self.levelData
        for level, val in self.currentPath.items():
            isList, index = val["isList"], val["index"]

            if len(self.currentPath) - 1 - (stepBackAmount - 1) == counter:
                return currentLevel

            if (not isList) or ignoreIndex:
                currentLevel = currentLevel[level]
            else:
                currentLevel = currentLevel[level][index]

            counter += 1

        return currentLevel
    
    def convertTopToList(self):
        prevData = self.navigatePath(1)
        prevData[self.getTopOfPath()] = [{}]
        self.currentPath[self.getTopOfPath()]["isList"] = True

    def isTopList(self):
        return self.currentPath[self.getTopOfPath()]["isList"]
    
    def incrementIndexOnPath(self, key):
        self.currentPath[key]["index"] += 1
        self.navigatePath(0,True).append({})

    def getTopOfPath(self):
        return list(self.currentPath.keys())[-1]
    
    def addToPath(self, key):
        self.currentPath[key] = {"isList":False, "index": 0}

    def removeFromPath(self, amount):
        for i in range(0, amount):
            del self.currentPath[self.getTopOfPath()]


def extractKeyValuePair(text):
    pass

yamlData = None

levelData = LevelData()

indentKeys = {}

lastIndent = 0

previousKey = None

currentListIndex = 0

with open("TESTING.yaml","r") as f:
    yamlData = f.readlines()

for i in range(0, 41):
    line = yamlData[i]

    leadingSpaces = len(line) - len(line.lstrip(' '))

    indentLevel = leadingSpaces // 2

    firstCharacter = line[leadingSpaces]

    if indentLevel > lastIndent:
        levelData.addToPath(previousKey)
        indentKeys[lastIndent] = previousKey
    if indentLevel < lastIndent:
        levelData.removeFromPath(lastIndent - indentLevel)


    lastIndent = indentLevel

    if firstCharacter == "-":

        if not levelData.isTopList():
            levelData.convertTopToList()

        afterDash = line[line.find("-")+1:]
        
        levelData.navigatePath()["data"] = afterDash.lstrip(" ")

        levelData.incrementIndexOnPath(indentKeys[indentLevel-1])

    elif firstCharacter.isalpha():
        #Assignment stuff
        keyText = line[leadingSpaces:line.find(":")]
        
        valueText = line[line.find(":")+1:len(line)].lstrip(" ")

        if valueText == "\n":
            previousKey = keyText
            
            valueText = {}

        levelData.navigatePath()[keyText] = valueText

print(levelData.levelData)
#     currentIndentLevel = 0

#     for i, char in enumerate(line):
#         if char == " ":
#             currentIndentLevel += 1
    
#     currentIndentLevel //= 2
        
