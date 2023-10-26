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
    
    def convertTopToList(self, indentLevel):
        prevData = self.navigatePath(1)
        prevData[self.getTopOfPath()] = [{}]
        self.currentPath[self.getTopOfPath()]["isList"] = True
        self.currentPath[self.getTopOfPath()]["itemIndent"] = indentLevel

    def isTopList(self):
        return self.currentPath[self.getTopOfPath()]["isList"]
    
    def incrementIndexOnPath(self, key):
        self.currentPath[key]["index"] += 1
        self.navigatePath(0,True).append({})

    def getTopOfPath(self):
        return list(self.currentPath.keys())[-1]
    
    def addToPath(self, key):
        self.currentPath[key] = {"isList":False, "index": -1, "itemIndent":-1}

    def removeFromPath(self, amount):
        for i in range(0, amount):
            del self.currentPath[self.getTopOfPath()]

    def getTopIndentLevel(self):
        return self.currentPath[self.getTopOfPath()]["itemIndent"]


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

        change = indentLevel-lastIndent

        isList = True
        try:
            if levelData.isTopList():

                listIndexLevel = levelData.getTopIndentLevel()

                if change <= 1:
                    indentLevel = listIndexLevel
                else:
                    isList = False
            else:
                isList = False
                
        except:
            isList = False
        
        if not isList:
            levelData.addToPath(previousKey)
            indentKeys[lastIndent] = previousKey

    elif indentLevel < lastIndent:
        levelData.removeFromPath(lastIndent - indentLevel)

    lastIndent = indentLevel

    if firstCharacter == "-":
        if not levelData.isTopList():
            
            print(indentLevel)
            levelData.convertTopToList(indentLevel)

        afterDash = line[line.find("-")+1:]
        
        levelData.navigatePath()["data"] = afterDash.lstrip(" ")

        levelData.incrementIndexOnPath(levelData.getTopOfPath())

    elif firstCharacter.isalpha():

        #Assignment stuff
        keyText = line[leadingSpaces:line.find(":")]
        
        valueText = line[line.find(":")+1:len(line)].lstrip(" ")

        if valueText == "\n":
            previousKey = keyText
            
            valueText = {}

        #print(levelData.currentPath)
        #print(levelData.navigatePath())
        levelData.navigatePath()[keyText] = valueText

print(levelData.levelData)
#     currentIndentLevel = 0

#     for i, char in enumerate(line):
#         if char == " ":
#             currentIndentLevel += 1
    
#     currentIndentLevel //= 2
        
