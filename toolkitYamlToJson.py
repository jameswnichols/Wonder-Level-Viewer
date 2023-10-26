import json

#5 places of float precision.

class LevelData:
    def __init__(self):
        self.levelData = {}
        self.currentPath = {}

    def navigatePath(self):
        currentLevel = self.levelData
        for level, index in self.currentPath:
            currentLevel = currentLevel[level]
        return currentLevel


def extractKeyValuePair(text):
    pass

yamlData = None

levelData = {}

currentPath = {}

lastIndent = 0

previousKey = None

currentListIndex = 0

with open("TESTING.yaml","r") as f:
    yamlData = f.readlines()

for i in range(0, 15):
    line = yamlData[i]

    leadingSpaces = len(line) - len(line.lstrip(' '))

    indentLevel = leadingSpaces // 2

    firstCharacter = line[leadingSpaces]

    if indentLevel != lastIndent:
        currentPath[previousKey] = 0

    lastIndent = indentLevel

    if firstCharacter == "-":

        listData = navigatePath(levelData,currentPath)

        prevData = navigatePath(levelData, currentPath[:len(currentPath)-1])

        if isinstance(listData,dict) and len(listData) == 0:
            prevData[currentPath[-1]] = []
            currentListIndex = 0

        listData.append({})


    elif firstCharacter.isalpha():
        #Assignment stuff
        keyText = line[leadingSpaces:line.find(":")]
        
        valueText = line[line.find(":")+1:len(line)].lstrip(" ")

        if valueText == "\n":
            previousKey = keyText
            valueText = {}

        navigatePath(levelData,currentPath)[keyText] = valueText

        print(f"{keyText} : {repr(valueText)}")

print(levelData)
#     currentIndentLevel = 0

#     for i, char in enumerate(line):
#         if char == " ":
#             currentIndentLevel += 1
    
#     currentIndentLevel //= 2
        
