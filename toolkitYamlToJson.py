import json

#5 places of float precision.

class LevelData:
    def __init__(self):
        self.levelData = {}
        self.currentPath = {}

    def getCurrentStructure(self, ignoreFinalIndex : bool = False):
        currentLevel = self.levelData
        pathIndex = 0
        for level, val in self.currentPath.items():

            isList, index = val["isList"], val["index"]

            if (not isList) or (ignoreFinalIndex and pathIndex == len(self.currentPath)-1):
                currentLevel = currentLevel[level]
            else:
                currentLevel = currentLevel[level][index]

            pathIndex += 1

        return currentLevel

    def addStructure(self, key, isList):

        value = [] if isList else {}
        self.getCurrentStructure()[key] = value

        self.currentPath[key] = {"isList":isList,"index":-1}

    def removeTopStructure(self):
        del self.currentPath[list(self.currentPath.keys())[-1]]

    def increaseIndexOfTopList(self):
        self.currentPath[list(self.currentPath.keys())[-1]]["index"] += 1
        self.getCurrentStructure(ignoreFinalIndex=True).append({})

def getIndentAndStartCharacter(line):
    leadingSpaces = len(line) - len(line.lstrip(' '))

    indentLevel = leadingSpaces // 2

    firstCharacter = line[leadingSpaces]

    return leadingSpaces, indentLevel, firstCharacter
    

yamlData = None

levelData = LevelData()

lastIndentLevel = 0

with open("TESTING.yaml","r") as f:
    yamlData = f.readlines()

for i in range(0, 41):
    line = yamlData[i]

    leadingSpaces, indentLevel, firstCharacter = getIndentAndStartCharacter(line)

    #TODO Add stuff

    if firstCharacter == "-":
        indentLevel += 1

        if indentLevel < lastIndentLevel:
            levelData.removeTopStructure()

        levelData.increaseIndexOfTopList()

        itemData = line[line.find("- ")+1:]
        print(itemData)

        #Is list item
    else:
        colonLocation = line.find(":")

        keyText = line[leadingSpaces:colonLocation]
        valueText = line[colonLocation+1:len(line)]

        isList = getIndentAndStartCharacter(yamlData[i + 1])[2] == "-"
        isDict = valueText == "\n" and not isList

        if indentLevel < lastIndentLevel:
            levelData.removeTopStructure()

        # print(f"{keyText} : {repr(valueText)} :: IsList : {isList} IsDict : {isDict}")

        if not isList and not isDict:
            levelData.getCurrentStructure()[keyText] = valueText

        else:
            print(f"{keyText} :: {indentLevel}")
            levelData.addStructure(keyText, isList)

    lastIndentLevel = indentLevel

    #

print(levelData.levelData)
