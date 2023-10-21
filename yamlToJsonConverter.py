import yaml
import json
import regex
import os
from io import BytesIO

pattern = regex.compile("!..? ")

filename = "Course13.yaml"#input("Enter filepath: ")

finalLines = []

with open(filename,"r") as f:
    fileLines = f.readlines()

for line in fileLines:
    collisions = pattern.finditer(line)
    newLine = line
    for collision in collisions:
        start, end = collision.span()
        tag = line[start:end]
        newLine = newLine.replace(tag, "")
    
    finalLines.append(newLine)

with open("temp.yaml","w") as f:
    f.writelines(finalLines)

with open("temp.yaml","r") as f:
    yamlData = yaml.safe_load(f)

os.remove("temp.yaml")

newFilename = filename[:filename.rfind(".")]+".json"

with open(newFilename,"w") as f:
    json.dump(yamlData, f)
    


