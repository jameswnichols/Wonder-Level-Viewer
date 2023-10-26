import json

#5 places of float precision.

class LevelData:
    def __init__(self):
        self.levelData = {}
        self.currentPath = {}

    def navigatePath(self):
        counter = 0
        currentLevel = self.levelData
        for level, val in self.currentPath.items():
            isList, index = val["isList"], val["index"]

            if (not isList):
                currentLevel = currentLevel[level]
            else:
                currentLevel = currentLevel[level][index]

            counter += 1

        return currentLevel

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

    #TODO Add stuff

    if firstCharacter == "-":
        pass
        #Is list item
    else:
        colonLocation = line.find(":")

        keyText = line[leadingSpaces:colonLocation]
        valueText = line[colonLocation+1:len(line)].lstrip(" ")
        
        print(f"{keyText} : {repr(valueText)}")



    #print(f"{indentLevel} :: {firstCharacter}")
        
