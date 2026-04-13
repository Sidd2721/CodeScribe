import sys
import os

# Add current directory to path so we can import app
sys.path.append(os.getcwd())

from app.services.ast_parser import analyze_code
import json

code = """
import os
from typing import List

class Processor:
    '''A sample class'''
    def __init__(self):
        self.data = []

    def process(self, item):
        '''Process an item'''
        self.clean(item)
        print(item)

    def clean(self, item):
        return item.strip()

def main():
    p = Processor()
    p.process(" hello ")
    other_func()

def other_func():
    pass

main()
"""

print("Analyzing code...")
result = analyze_code(code)
print(json.dumps(result, indent=2))

# Basic assertions
assert len(result["classes"]) == 1
assert result["classes"][0]["name"] == "Processor"
assert len(result["classes"][0]["methods"]) == 3
assert len(result["functions"]) == 2 # main, other_func
assert len(result["calls"]) > 0
print("Verification Successful!")
