import json

class DataManager:
    def __init__(self, recipes_file="recipes.json"):
        self.recipes_file = recipes_file
        self.items = []
        self.recipes = []
        self.enabled_alternates = set()
        self.load_data()

    def load_data(self):
        try:
            with open(self.recipes_file, "r") as f:
                data = json.load(f)
                self.items = data.get("items", [])
                self.recipes = data.get("recipes", [])
        except FileNotFoundError:
            print(f"Error: Could not find {self.recipes_file}")

    def toggle_alternate(self, recipe_name, enabled):
        if enabled:
            self.enabled_alternates.add(recipe_name)
        else:
            if recipe_name in self.enabled_alternates:
                self.enabled_alternates.remove(recipe_name)

    def get_available_recipes(self):
        available = []
        for r in self.recipes:
            if not r["is_alternate"] or r["name"] in self.enabled_alternates:
                available.append(r)
        return available

    def get_recipes_producing(self, item_name):
        producing = []
        for r in self.get_available_recipes():
            for p in r["products"]:
                if p["item"] == item_name:
                    producing.append(r)
        return producing

    def get_recipe_by_name(self, name):
        for r in self.recipes:
            if r["name"] == name:
                return r
        return None
