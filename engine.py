import uuid

class Node:
    def __init__(self, recipe, target_amount, is_manual=False):
        self.id = str(uuid.uuid4())
        self.recipe = recipe
        self.target_amount = target_amount
        self.is_manual = is_manual
        self.machine_count = 0
        self.inputs = {}  # item_name -> amount needed
        self.outputs = {} # item_name -> amount produced
        self.calculate()

    def calculate(self):
        if self.recipe["name"] == "Awesome Sink":
            self.machine_count = 1
            if self.target_amount > 0:
                 self.inputs["Any"] = self.target_amount
            else:
                 self.inputs["Any"] = 0
            return

        if not self.recipe["products"]:
            return

        primary_product = self.recipe["products"][0]
        base_amount = primary_product["amount"]

        scale_factor = self.target_amount / base_amount if base_amount > 0 else 0
        self.machine_count = scale_factor

        for ing in self.recipe["ingredients"]:
            self.inputs[ing["item"]] = ing["amount"] * scale_factor

        for prod in self.recipe["products"]:
            self.outputs[prod["item"]] = prod["amount"] * scale_factor

class CalculationEngine:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.nodes = []
        self.links = []

    def add_manual_node(self, recipe_name, amount):
        recipe = self.data_manager.get_recipe_by_name(recipe_name)
        if recipe:
            node = Node(recipe, amount, is_manual=True)
            self.nodes.append(node)
            return node
        return None

    def auto_generate(self, target_item, target_amount, depth=0):
        # Prevent infinite recursion from looping recipes
        if depth > 50:
            print(f"Max depth reached generating {target_item}")
            return None

        recipes = self.data_manager.get_recipes_producing(target_item)
        if not recipes:
            return None

        # Prefer the primary (non-alternate) recipe if available
        chosen_recipe = recipes[0]
        for r in recipes:
            if not r["is_alternate"] and not r["name"].startswith("Alternate:"):
                chosen_recipe = r
                break

        # Wait, if target_amount is 0, just return none
        if target_amount <= 0:
            return None

        primary_product_amount = 0
        for p in chosen_recipe["products"]:
            if p["item"] == target_item:
                primary_product_amount = p["amount"]
                break

        scale_factor = target_amount / primary_product_amount if primary_product_amount > 0 else 1

        adjusted_target = chosen_recipe["products"][0]["amount"] * scale_factor

        node = Node(chosen_recipe, adjusted_target)
        self.nodes.append(node)

        for ing, amount in node.inputs.items():
            child_node = self.auto_generate(ing, amount, depth + 1)
            if child_node:
                self.links.append((child_node.id, ing, node.id, ing, amount))

        return node

    def clear(self):
        self.nodes = []
        self.links = []
