from data import DataManager
from engine import CalculationEngine
from ui import UI

def main():
    data_manager = DataManager()
    engine = CalculationEngine(data_manager)
    app_ui = UI(data_manager, engine)

    app_ui.build()
    app_ui.run()

if __name__ == "__main__":
    main()
