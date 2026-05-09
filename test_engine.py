from data import DataManager
from engine import CalculationEngine

dm = DataManager()
engine = CalculationEngine(dm)
root = engine.auto_generate("Plastic", 60)

for node in engine.nodes:
    print(f"Node: {node.recipe['name']} (x{node.machine_count})")
    print(f"  Inputs: {node.inputs}")
    print(f"  Outputs: {node.outputs}")

print("Links:")
for link in engine.links:
    print(link)
