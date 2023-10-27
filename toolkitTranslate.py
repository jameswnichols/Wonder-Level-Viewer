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

def parseValue(value, type):

    CUSTOM_TYPES = ["!u","!l","!ul"]

    if type in CUSTOM_TYPES:
        return type + " " + str(value)
    
    if isinstance(value, float):
        return f"{value:.5f}"
    
    if value == None:
        return ""
    
    if value == "":
        return "''"
    
    if isinstance(value, bool):
        return str(value).lower()

    if type == "inlineDict":
        text = ""
        vals = []
        for key, val in value.items():
            vals.append(key + ": " + str(parseValue(val["value"],val["type"])))
        
        text = "{" + ", ".join(vals) + "}"

        return text
    
    return value

def traceThrough(data, path):
    finalLocation = data
    for trace in path:
        finalLocation = finalLocation[trace]
    return finalLocation

def jsonToYaml(filePath : str):
    
    levelData = None

    lines = []

    #["root","Actors",0,"Dynamic","InitDir"]
    #["root","Actors",0,"Dynamic"]
    #["root","Actors",0,"AreaHash"]
    #["root","Actors"]
    #...
    #["root","ActorToRailLinks",1]
    #["root","ActorToRailLinks",0]
    #["root","ActorToRailLinks"]
    #["root"]
    #["HasReferenceNodes"]
    #["SupportPaths"]
    #["IsBigEndian"]
    #["Version"]
    #Pop from the bottom

    with open(filePath,"r") as f:
        levelData = json.load(f)

    pathsToExplore = [[]]

    lines = []

    while pathsToExplore:
        
        traceRoute = pathsToExplore.pop(0)

        currentPoint = traceThrough(levelData, traceRoute)

        pointIndent = (len(traceRoute)-1) * 2

        prevLineNewline = True if len(lines) == 0 else lines[-1].endswith("\n")

        indentText = "" if not prevLineNewline else " " * pointIndent

        newTraces = []

        addLine = True

        try:
            finalPointName = traceRoute[-1]
        except:
            addLine = False
            finalPointName = ""

        if isinstance(currentPoint, dict):

            pointKeys = list(currentPoint.keys())

            if "value" in pointKeys and "type" in pointKeys:
                #HANDLE ASSIGNMENT
                text = f"{finalPointName}: "
                if isinstance(finalPointName,int):
                    text = "- "

                valueText = parseValue(currentPoint['value'], currentPoint["type"])

                if addLine:
                    
                    lines.append(indentText + f"{text}{valueText}\n")

            else:
                text = f"{finalPointName}:\n"

                #IF LIST
                if isinstance(finalPointName,int):
                    text = "- "

                if addLine:
                    lines.append(indentText + text)

                for key, value in currentPoint.items():
                    
                    newRoute = traceRoute + [key]

                    newTraces.append(newRoute)
        
        if isinstance(currentPoint, list):
            if addLine:
                
                lines.append(indentText + f"{finalPointName}:\n")
            for i in range(0, len(currentPoint)):
                newRoute = traceRoute + [i]
                
                newTraces.append(newRoute)
        
        pathsToExplore = newTraces + pathsToExplore

    return lines

with open("yamlToJson.json","w") as f:
    json.dump(yamlToJson("BACKUP.yaml",ignoreTyping=False),f)

with open("JsonToYaml.yaml","w") as f:
    f.writelines(jsonToYaml("yamlToJson.json"))



