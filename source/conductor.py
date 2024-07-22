#!/usr/bin/python
import numpy as np
from plot import Plot
from filer import Filer


class Conductor:

    data = None
    index = 0

    def __init__(self, name, material, length, xsarea, cap_names):
        self.name = name
        self.material = material
        self.xsarea_length = xsarea / length
        self.cap_names = cap_names
        self.from_to_name = cap_names[0] + '->' + cap_names[1]
        self.capacitors = []                    # Massive heat capacitors connected by this conductor
        self.power_v_time = []
        if Conductor.data is None:
            filer = Filer()
            data, groups = filer.load_data('conductivity.csv')
            data = Conductor.convert_to_integrals(data)
            Conductor.data, Conductor.groups = data, groups
        self.index = Conductor.index
        Conductor.index += 1
        return

    def __str__(self):
        text = "{:s}, {:s}\nA/L={:.2f} mm".format(self.name, self.material[0:2], self.xsarea_length * 1.0E3)
        return text

    def get(self):
        return self.material, self.xsarea_length

    def create_links(self, all_capacitors):
        for cap_name in self.cap_names:
            for capacitor in all_capacitors:
                if cap_name == capacitor.name:
                    self.capacitors.append(capacitor)
                    capacitor.attach_connector(self)
                    break
        return

    @staticmethod
    def convert_to_integrals(data):
        """ Replace input thermal conductivity values (W/m/K) into integrals (W/m (T))
        """
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
        cap_a, cap_b = self.capacitors[0], self.capacitors[1]
        ta, tb = cap_a.temperature, cap_b.temperature
        material, area_length = self.material, self.xsarea_length
        temps = Conductor.data['Temp']
        kints = Conductor.data[material]
        [kta, ktb] = np.interp([ta, tb], temps, kints)
        power = area_length * (kta - ktb)                     # power < 0. if t1 > t2
        cap_a.con_power -= power                              # Ta > Tb, cap_a gets hotter, cap_b gets cooler
        cap_b.con_power += power
        return power, cap_a, cap_b

    @staticmethod
    def plot_data(**kwargs):

        group = kwargs.get('group', 'All')
        plot = Plot()
        title = "Conductivity - {:s}".format(group)

        axs = plot.set_plot_area(title)
        ax = axs[0, 0]
        ax.set_yscale('log')
        ax.set_xlabel('T [K]')
        ax.set_ylabel('Kint [Watt / m / K]')
        data = Conductor.data
        groups = Conductor.groups
        temps = data['Temp']
        materials = list(data.keys())
        for material in materials[1:]:
            group_name = groups[material]
            if group == group_name and group != 'All':
                conds = data[material]
                ax.plot(temps, conds, label=material)
        ax.legend()
        plot.show()
        return

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
