import json

#5 places of float precision.

yamlData = None

levelData = {}

lastIndent = 0

currentPath = []

with open("TESTING.yaml","r") as f:
    yamlData = f.readlines()

for line in yamlData:

    currentIndentLevel = 0

    for i, char in enumerate(line):
        if char == " ":
            currentIndentLevel += 1
    
    currentIndentLevel //= 2

    if currentIndentLevel >
        
