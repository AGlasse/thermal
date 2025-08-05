#!/usr/bin/python
from thermal_elements import ThermalElements
from thermal_grid import ThermalGrid

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    thermal = ThermalGrid()

    # thermal = ThermalElements()
    # thermal.load_model('marvel')
    thermal.run()
