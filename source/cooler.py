#!/usr/bin/python
import numpy as np
from plot import Plot
from filer import Filer


class Cooler:

    material, length, xsarea = None, None, None
    element1, element2 = None, None

    def __init__(self, name):
        self.name = name
        # self.material = material
        # self.xsarea_length = xsarea / length
        self.position = 0., 0.      # Tuple holding the position of the element in the thermal model diagram
        if Cooler.data is None:
            plot_data = kwargs.get('plot_data', False)
            filer = Filer()
            data, groups = filer.load_data('coolers.csv')
            Cooler.data, Cooler.groups = data, groups
            if plot_data:
                Cooler.plot_data(group='Marvel')
        return

    def get_text(self):
        text = "{:s}\n{:s}\n{:.3f} m".format(self.name, self.material, self.xsarea_length)
        return text

    def get(self):
        return self.material, self.xsarea_length

    def link(self, element1, element2):
        element1.attach_connector(self)
        element2.attach_connector(self)
        self.element1 = element1
        self.element2 = element2
        return
