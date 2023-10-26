import json

#5 places of float precision.

def navigatePath(data, path):
    currentLevel = data
    for level in path:
        currentLevel = currentLevel[level]
    return currentLevel

yamlData = None

levelData = {"a":{"b":{"c":[]}}}

currentPath = []

lastIndent = 0

with open("TESTING.yaml","r") as f:
    yamlData = f.readlines()

# for line in yamlData:

#     currentIndentLevel = 0

#     for i, char in enumerate(line):
#         if char == " ":
#             currentIndentLevel += 1
    
#     currentIndentLevel //= 2
        
