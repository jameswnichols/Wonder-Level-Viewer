import json

#5 places of float precision.
#!u - Unsigned int(?)
#!l - Signed 64bit int.
#!ul - Unsigned 64bit int.
#!f64 - binary64 floating point value.

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

    def addStructure(self, key, isList, indent):

        value = [] if isList else {}
        self.getCurrentStructure()[key] = value

        self.currentPath[key] = {"isList":isList,"index":-1,"indent":indent}

    def removeTopStructure(self, newIndent):

        keys = list(self.currentPath.keys())

        for i in range(0, len(keys)):

            index = len(keys) - 1 - i
                    
            key = keys[index]

            indent = self.currentPath[key]["indent"]

            if indent != newIndent:
                del self.currentPath[keys[index]]
            else:
                break

    def getTopStructure(self):
        return self.currentPath[list(self.currentPath.keys())[-1]]

    def increaseIndexOfTopList(self):
        self.currentPath[list(self.currentPath.keys())[-1]]["index"] += 1
        self.getCurrentStructure(ignoreFinalIndex=True).append({})

    def setDataInTopList(self, data):
        self.getCurrentStructure(ignoreFinalIndex=True)[self.getTopStructure()["index"]] = data

def getIndentAndStartCharacter(line):
    leadingSpaces = len(line) - len(line.lstrip(' '))

    indentLevel = leadingSpaces // 2

    firstCharacter = line[leadingSpaces]

    return leadingSpaces, indentLevel, firstCharacter
    
def getLineData(line, index, yamlData):
    colonLocation = line.find(":")

    keyText = line[0:colonLocation]
    valueText = line[colonLocation+1:len(line)]

    newIndex = index if index + 1 == len(yamlData) else index + 1

    isList = getIndentAndStartCharacter(yamlData[newIndex])[2] == "-"
    isDict = valueText == "\n" and not isList

    return keyText, valueText, isList, isDict

def processValueText(vt : str):

    CONVERSIONS = {"False":"false","True":"true","None":"null"}

    stripped = vt.rstrip().lstrip()

    type = "generic"

    if "{" in vt:
        
        converted = dictPreProcess(vt)
        type = "inlineDict"

    else:
        if "!" in stripped:
            type = stripped[:stripped.find(" ")]

            stripped = stripped[stripped.find(" "):]
        
        for conIn, conOut in CONVERSIONS.items():
            stripped = stripped.replace(conIn, conOut)

        converted = stripped

        try:
            converted = json.loads(stripped)
        except:
            pass
    
    return {"value":converted,"type":type}

def dictPreProcess(dct : str):

    REPLACEMENTS = {"{":'{"',
                    ": ":'": "',
                    ", ":'", "',
                    "}":'"}'}

    stripped = dct.rstrip()
    
    for repIn, repOut in REPLACEMENTS.items():
        stripped = stripped.replace(repIn, repOut)
    
    convertedDict = json.loads(stripped)

    processedDict = {}

    for key, value in convertedDict.items():
        processedDict[key] = processValueText(value)

    return processedDict

yamlData = None

levelData = LevelData()

lastIndentLevel = 0

indentKeys = {}

with open("TESTING.yaml","r") as f:
    yamlData = f.readlines()

for i, line in enumerate(yamlData): #21632 77 , line in enumerate(yamlData)
    #line = yamlData[i]

    leadingSpaces, indentLevel, firstCharacter = getIndentAndStartCharacter(line)

    newLine = line[leadingSpaces:len(line)]

    itemCarry = False

    if firstCharacter == "-":
        #Is List Item
        indentLevel += 1

        if indentLevel < lastIndentLevel:
            
            change = lastIndentLevel - indentLevel
            levelData.removeTopStructure(indentLevel)

        levelData.increaseIndexOfTopList()

        itemData = line[line.find("- ")+2:]

        curleyBracketIndex = itemData.find("{")

        colonIndex = itemData.find(":")

        bothExist = curleyBracketIndex != -1 and colonIndex != -1
        
        if (":" in itemData and not bothExist) or (bothExist and (colonIndex < curleyBracketIndex)):
            itemCarry = True
        else:
            if bothExist and (curleyBracketIndex < colonIndex):
                itemData = {"value":dictPreProcess(itemData),"type":"inlineDict"}
            else:
                itemData = processValueText(itemData)

            levelData.setDataInTopList(itemData)
        
    if firstCharacter != "-" or itemCarry:

        lineData = newLine

        if itemCarry:
            lineData = itemData

        keyText, valueText, isList, isDict = getLineData(lineData, i, yamlData)

        if indentLevel < lastIndentLevel and not itemCarry:
            change = lastIndentLevel - indentLevel

            levelData.removeTopStructure(indentLevel)

        #22807

        # print(f"{keyText} : {repr(valueText)} :: IsList : {isList} IsDict : {isDict}")

        if not isList and not isDict:
            levelData.getCurrentStructure()[keyText] = processValueText(valueText)

        else:

            indentKeys[indentLevel] = keyText

            increase = 2 if isList else 1

            levelData.addStructure(keyText, isList, indentLevel+increase)

    lastIndentLevel = indentLevel

with open("output.json","w") as f:
    json.dump(levelData.levelData,f, indent=3)

#print(levelData.levelData)
