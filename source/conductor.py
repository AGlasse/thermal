#!/usr/bin/python
import numpy as np
from plot import Plot
from filer import Filer


class Conductor:

    material, length, xsarea = None, None, None
    element1, element2 = None, None
    data = None

    def __init__(self, name, material, length, xsarea, **kwargs):
        self.name = name
        self.material = material
        self.xsarea_length = xsarea / length
        if Conductor.data is None:
            filer = Filer()
            data, groups = filer.load_data('conductivity.csv')
            data = Conductor.convert_to_integrals(data)
            Conductor.data, Conductor.groups = data, groups
            plot_data = kwargs.get('plot_data', False)
            if plot_data:
                Conductor.plot_data(group='Marvel')
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
    def heat_flow(element, connector):
        """ Find the conductive heat flow along a connector from this element.
        """
        t1, t2 = connector.element1.temperature, connector.element2.temperature
        if element.name != connector.element1.name:
            t1, t2 = connector.element2.temperature, connector.element1.temperature
        material, area_length = connector.get()
        temps = Conductor.data['Temp']
        kints = Conductor.data[material]
        [k1, k2] = np.interp([t1, t2], temps, kints)
        power = area_length * (k2 - k1)                     # power < 0. if t1 > t2
        return power

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

