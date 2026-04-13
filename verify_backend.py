from app.services.ast_parser import analyze_code
import json

# Actual code with classes and functions (not a string literal)
source_code = """
import os

class Dog:
    def __init__(self, name):
        self.name = name

    def bark(self):
        print("Woof")
        self.jump()

    def jump(self):
        print("Jump")

def walk_dog():
    d = Dog("Buddy")
    d.bark()

walk_dog()
"""

print("--- Source Code ---")
print(source_code)
print("--- Analysis Result ---")
result = analyze_code(source_code)

with open("verification_output.txt", "w") as f:
    f.write("--- Analysis Result ---\n")
    f.write("\n[CLASSES]\n")
    for cls in result["classes"]:
        f.write(f"- {cls['name']}\n")
        for m in cls["methods"]:
            f.write(f"  * method: {m['name']}\n")

    f.write("\n[FUNCTIONS]\n")
    for func in result["functions"]:
        f.write(f"- {func['name']}\n")

    f.write("\n[CALLS]\n")
    for call in result["calls"]:
        f.write(f"- Line {call['line']}: {call['caller_scope']} -> {call['callee']}\n")

print("Verification complete. Check verification_output.txt")


