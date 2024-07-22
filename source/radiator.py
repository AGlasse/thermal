#!/usr/bin/python
import numpy as np
from plot import Plot
from filer import Filer


class Radiator:

    data = None
    index = 0

    def __init__(self, name, emissivity, area, cap_names, color):
        self.name = name
        self.emissivity = emissivity
        self.area = area
        self.cap_names = cap_names
        self.from_to_name = cap_names[0] + '->' + cap_names[1]
        self.color = color
        self.capacitors = []                    # Massive heat capacitors connected by this radiator
        self.power_v_time = []
        self.index = Radiator.index
        Radiator.index += 1
        return

    def __str__(self):
        text = "{:s}\n$\epsilon$={:.2f}\nA={:.3f} m".format(self.name, self.emissivity, self.area)
        return text

    def create_links(self, all_capacitors):
        for cap_name in self.cap_names:
            for capacitor in all_capacitors:
                if cap_name == capacitor.name:
                    self.capacitors.append(capacitor)
                    capacitor.attach_radiator(self)
                    break
        return

    @staticmethod
    def convert_to_integrals(data):
        """ Replace input thermal conductivity valus (W/m/K) into integrals (W/m (T))"""
        temps = np.array(data['Temp'])
        materials = list(data.keys())
        for material in materials[1:]:
            ks = data[material]
            n = len(ks)
            kints, kint = np.zeros(n), 0.
            temp_im1, k_im1 = 0., 0.
            for i in range(0, n):
                temp_i, k_i = temps[i], ks[i]
                dtemp = temp_i - temp_im1
                kint += 0.5 * dtemp * (k_im1 + k_i)
                kints[i] = kint
                temp_im1, k_im1 = temp_i, k_i
            data[material] = kints
        return data

    def transfer_heat(self, time):
        """ Find the conductive heat flow along a connector from this element.
        """
        cap_a, cap_b = self.capacitors[0], self.capacitors[1]
        ta, tb = cap_a.temperature, cap_b.temperature

        sigma = 5.6703744E-8                    # Stephan-Boltzmann constant W m-2 K-4
        power = self.emissivity * self.area * sigma * (ta*ta*ta*ta - tb*tb*tb*tb)   # Ta > Tb, heat flows out of a.
        cap_a.rad_power -= power                            # Ta > Tb, cap_b gets hotter, cap_a gets cooler
        cap_b.rad_power += power
        self.power_v_time.append([time, power])
        return power, cap_a, cap_b

    @staticmethod
    def txt_to_csv():
        path = './materials/conductivity.txt'
        with open(path, 'r') as text_file:
            records = text_file.read().splitlines()
            for record in records:
                tokens = record.split(' ')
                line = ''
                for token in tokens:
                    if len(token) > 0:
                        line += token + ','
                print(line)
        return
