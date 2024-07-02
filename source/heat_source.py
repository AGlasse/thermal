#!/usr/bin/python
import math


class HeatSource:

    material, length, xsarea = None, None, None
    element1, element2 = None, None

    def __init__(self, name, power, **kwargs):
        self.name = name
        self.power = power
        self.element = None
        self.time = 0.
        self.sinvar = kwargs.get('sinvar', None)
        return

    def get_power(self, delta_time):

        self.time += delta_time
        if self.sinvar is None:
            return self.power
        power_minmax, period = self.sinvar
        phase = 2. * math.pi * self.time / period
        power = 0.5 * power_minmax * (math.sin(phase) + 1.)
        return power

    def link(self, element):
        element.attach_heat_source(self)
        self.element = element
        return
