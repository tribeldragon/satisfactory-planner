import dearpygui.dearpygui as dpg

class UI:
    def __init__(self, data_manager, engine):
        self.data_manager = data_manager
        self.engine = engine
        self.node_editor_id = None
        self.target_item = "Plastic"
        self.target_amount = 60.0
        self.visual_link_to_data = {} # dpg_link_id -> engine_link_tuple

    def build(self):
        dpg.create_context()
        dpg.create_viewport(title='Satisfactory Planner', width=1280, height=720)
        dpg.setup_dearpygui()

        with dpg.window(label="Control Panel", width=300, height=720, pos=(0,0), no_close=True, no_move=True):
            dpg.add_text("Auto Generate")
            items = self.data_manager.items
            dpg.add_combo(items, default_value=self.target_item, label="Target Item", tag="target_item_combo")
            dpg.add_input_float(default_value=self.target_amount, label="Amount / min", tag="target_amount_input")
            dpg.add_button(label="Generate", callback=self.on_generate)
            dpg.add_separator()

            dpg.add_text("Alternate Recipes")
            for recipe in self.data_manager.recipes:
                if recipe["is_alternate"]:
                    dpg.add_checkbox(label=recipe["name"], callback=self.on_toggle_alternate, user_data=recipe["name"])

            dpg.add_separator()
            dpg.add_text("Manual Add")
            recipes = [r["name"] for r in self.data_manager.recipes]
            dpg.add_combo(recipes, label="Recipe", tag="manual_recipe_combo")
            dpg.add_input_float(default_value=1.0, label="Machine Count", tag="manual_amount_input")
            dpg.add_button(label="Add Node", callback=self.on_add_manual)

        with dpg.window(label="Node Editor", width=980, height=720, pos=(300,0), no_close=True, no_move=True):
            self.node_editor_id = dpg.add_node_editor(callback=self.link_callback, delink_callback=self.delink_callback)

        dpg.show_viewport()

    def on_toggle_alternate(self, sender, app_data, user_data):
        self.data_manager.toggle_alternate(user_data, app_data)

    def on_generate(self, sender, app_data, user_data):
        item = dpg.get_value("target_item_combo")
        amount = dpg.get_value("target_amount_input")
        self.engine.clear()
        self.visual_link_to_data.clear()
        dpg.delete_item(self.node_editor_id, children_only=True)
        self.engine.auto_generate(item, amount)
        self.refresh_nodes()

    def on_add_manual(self, sender, app_data, user_data):
        recipe_name = dpg.get_value("manual_recipe_combo")
        machines = dpg.get_value("manual_amount_input")
        recipe = self.data_manager.get_recipe_by_name(recipe_name)
        if recipe:
            # We assume manual amount input means scale relative to 1 machine
            amount = recipe["products"][0]["amount"] * machines if recipe["products"] else 0
            if recipe["name"] == "Awesome Sink":
                amount = machines # Treat machine count as amount to sink for manual
            self.engine.add_manual_node(recipe_name, amount)
            self.refresh_nodes()

    def refresh_nodes(self):
        dpg.delete_item(self.node_editor_id, children_only=True)
        self.visual_link_to_data.clear()

        # Track attribute IDs for auto-linking
        self.output_attrs = {} # (node_id, item_name) -> attr_id
        self.input_attrs = {}  # (node_id, item_name) -> attr_id

        self.attr_to_data = {} # attr_id -> (node_id, item_name)

        x, y = 50, 50

        for node in self.engine.nodes:
            with dpg.node(parent=self.node_editor_id, label=f"{node.recipe['name']} (x{node.machine_count:.1f}) [{node.recipe['machine']}]", pos=(x, y)) as n:

                # Inputs
                for ing, amt in node.inputs.items():
                    with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input) as attr:
                        dpg.add_text(f"{ing}: {amt:.1f}/m")
                        self.input_attrs[(node.id, ing)] = attr
                        self.attr_to_data[attr] = (node.id, ing)

                # Outputs
                for prod, amt in node.outputs.items():
                    with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output) as attr:
                        dpg.add_text(f"{prod}: {amt:.1f}/m")
                        self.output_attrs[(node.id, prod)] = attr
                        self.attr_to_data[attr] = (node.id, prod)

            x += 250
            if x > 800:
                x = 50
                y += 200

        # Create auto-generated and manual links visually
        for link_tuple in self.engine.links:
            source_node_id, source_item, target_node_id, target_item, amount = link_tuple
            source_attr = self.output_attrs.get((source_node_id, source_item))
            target_attr = self.input_attrs.get((target_node_id, target_item))

            # For Any pin on sink
            if not target_attr and target_item == "Any" and target_node_id:
                # Try to find the generic "Any" input on the target
                target_attr = self.input_attrs.get((target_node_id, "Any"))

            if source_attr and target_attr:
                link_id = dpg.add_node_link(source_attr, target_attr, parent=self.node_editor_id)
                self.visual_link_to_data[link_id] = link_tuple

    def link_callback(self, sender, app_data):
        # app_data -> (source_attr, target_attr)
        link_id = dpg.add_node_link(app_data[0], app_data[1], parent=sender)

        source_data = self.attr_to_data.get(app_data[0])
        target_data = self.attr_to_data.get(app_data[1])

        if source_data and target_data:
            source_node_id, source_item = source_data
            target_node_id, target_item = target_data

            # Add to engine state so it persists across manual node additions
            link_tuple = (source_node_id, source_item, target_node_id, target_item, 0)
            if link_tuple not in self.engine.links:
                self.engine.links.append(link_tuple)

            self.visual_link_to_data[link_id] = link_tuple

    def delink_callback(self, sender, app_data):
        # app_data -> link_id
        if app_data in self.visual_link_to_data:
            link_tuple = self.visual_link_to_data[app_data]
            if link_tuple in self.engine.links:
                self.engine.links.remove(link_tuple)
            del self.visual_link_to_data[app_data]

        dpg.delete_item(app_data)

    def run(self):
        dpg.start_dearpygui()
        dpg.destroy_context()
