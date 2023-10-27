import json
import random

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

class JsonTrace:
    def __init__(self):
        pass

def getIndentAndStartCharacter(line):
    leadingSpaces = len(line) - len(line.lstrip(' '))

    indentLevel = leadingSpaces // 2

    firstCharacter = line[leadingSpaces]

    return leadingSpaces, indentLevel, firstCharacter
    
def getLineData(line, index, yamlData, lineIndent):
    colonLocation = line.find(":")

    keyText = line[0:colonLocation]
    valueText = line[colonLocation+1:len(line)]

    newIndex = index if index + 1 == len(yamlData) else index + 1

    _, indentLevel, firstChar = getIndentAndStartCharacter(yamlData[newIndex])

    isList = (firstChar == "-" and lineIndent < indentLevel)
    isDict = valueText == "\n" and not isList

    return keyText, valueText, isList, isDict

def processValueText(vt : str, ignoreType):

    CONVERSIONS = {"False":"false","True":"true"}

    stripped = vt.rstrip().lstrip()

    type = "generic"

    if "{" in vt:
        
        converted = dictPreProcess(vt, ignoreType)
        type = "inlineDict"

    else:
        if "!" in stripped:
            type = stripped[:stripped.find(" ")]

            stripped = stripped[stripped.find(" "):]
        
        for conIn, conOut in CONVERSIONS.items():
            stripped = stripped.replace(conIn, conOut)

        converted = stripped

        if converted == "":
            converted = None

        if converted == "''":
            converted = ""

        try:
            converted = json.loads(stripped)
        except:
            pass
    
    return {"value":converted,"type":type} if not ignoreType else converted

def dictPreProcess(dct : str, ignoreType):

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
        processedDict[key] = processValueText(value, ignoreType)

    return processedDict

def yamlToJson(filePath : str, ignoreTyping : bool = False):
    yamlData = None

    levelData = LevelData()

    lastIndentLevel = 0

    indentKeys = {}

    with open(filePath,"r") as f:
        yamlData = f.readlines()

    for i, line in enumerate(yamlData):

        leadingSpaces, indentLevel, firstCharacter = getIndentAndStartCharacter(line)

        newLine = line[leadingSpaces:len(line)]

        itemCarry = False

        if firstCharacter == "-":
            #Is List Item
            indentLevel += 1

            if indentLevel < lastIndentLevel:
                
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

                    processedData = dictPreProcess(itemData, ignoreTyping)

                    itemData = {"value":processedData,"type":"inlineDict"} if not ignoreTyping else processedData
                else:

                    itemData = processValueText(itemData,ignoreTyping)

                levelData.setDataInTopList(itemData)
            
        if firstCharacter != "-" or itemCarry:

            lineData = newLine

            if itemCarry:
                lineData = itemData

            keyText, valueText, isList, isDict = getLineData(lineData, i, yamlData, indentLevel)

            if indentLevel < lastIndentLevel and not itemCarry:

                levelData.removeTopStructure(indentLevel)

            if not isList and not isDict:
                levelData.getCurrentStructure()[keyText] = processValueText(valueText,ignoreTyping)

            else:

                indentKeys[indentLevel] = keyText

                increase = 2 if isList else 1

                levelData.addStructure(keyText, isList, indentLevel+increase)

        lastIndentLevel = indentLevel
    
    return levelData.levelData

def generateID():
    return "".join([str(random.randint(0, 9)) for x in range(0,16)])

def jsonToYaml(filePath : str):
    
    levelData = None

    lines = []

    with open(filePath,"r") as f:
        levelData = json.load(f,)

    pathsToExplore = {0:levelData}

    while pathsToExplore:

        firstKey = list(pathsToExplore.keys())[0]

        currentPath = pathsToExplore.pop(firstKey)

        if isinstance(currentPath, dict):
            for key, value in currentPath.items():
                if isinstance(value, dict):
                    if "value" in value and "type" in value:
                        lines.append(f"{key}: {value['value']}\n")
                        #print(f"{key}={value['value']}")
                    else:
                        #print(f"Path for {key}")
                        lines.append(f"{key}: \n")
                        pathsToExplore[generateID()] = currentPath[key]
                else:
                    pathsToExplore[generateID()] = currentPath[key]

        elif isinstance(currentPath, list):
            for i, value in enumerate(currentPath):

                if isinstance(value, dict):
                    if "value" in value and "type" in value:
                        lines.append(f"-{firstKey}[{i}]: {value['value']}\n")
                    else:
                        key = list(value.keys())[0]
                        lines.append(f"-{key}: \n")
                        pathsToExplore[generateID()] = currentPath[i]
                else:
                    #lines.append(f"-{key}: ")
                    pathsToExplore[generateID()] = currentPath[i]

    #print(list(pathsToExplore.keys()))

    with open("tempOutput.yaml","w") as f:
        f.writelines(lines)

    
jsonToYaml("tempOutput.json")     

# with open("output.json","w") as f:
#     json.dump(yamlToJson("TESTING.yaml",ignoreTyping=False),f)

