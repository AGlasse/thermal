#!/usr/bin/python
from thermal import Thermal

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    thermal = Thermal()
    thermal.load_model()
    thermal.run()
