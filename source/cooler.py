#!/usr/bin/python
import numpy as np
from plot import Plot
from filer import Filer
from capacitor import Capacitor


class Cooler(Capacitor):

    cool_v_temp, cool_groups = None, None
    index = 0
    cooler_names = ['pt16_st', 'pt16_hp', 'pt30_st', 'pt30_hp']

    def __init__(self, params):
        pname, pmaterial, pmass, ptemperature, pcolor = params
        self.name, self.material, self.color = pname, pmaterial, pcolor
        self.mass, self.temperature = float(pmass), float(ptemperature)

        # Instantaneous heat flow into capacitor due to conduction, radiation, cooling
        self.con_power, self.rad_power = 0., 0.
        self.new_temperature = self.temperature
        self.connectors, self.radiators = [], []
        self.temp_v_time, self.power_v_time = [], []
        self.position = 0., 0.      # Tuple holding the position of the element in the thermal model diagram
        self.is_cooler = True

        if Cooler.cool_v_temp is None:
            filer = Filer()
            Cooler.cool_v_temp, Cooler.cool_groups = filer.load_data('coolers.csv')

        self.active_paths = {'con': None, 'rad': None}
        self.index = Capacitor.index
        Capacitor.index += 1
        return

    def __str__(self):
        text = "{:s}\n{:s}, {:.1f} kg".format(self.name, self.material[0:2], self.mass)
        return text

    def find_new_temperature(self, time, delta_time):
        """ Find the new temperature of this body after delta_time by summing the heat flow from connected
        elements.  The new temperature must be applied once they have been calculated for all elements.
        """
        self.temp_v_time.append([time, self.temperature])
        temp = self.temperature
        cool_temps = Cooler.cool_v_temp['Temp']
        cool_powers = Cooler.cool_v_temp[self.name]
        cool_power = np.interp(temp, cool_temps, cool_powers)
        tot_power = self.con_power + self.rad_power - cool_power
        heat = tot_power * delta_time
        self.temperature = Capacitor.get_new_temperature(self, heat)
        self.con_power, self.rad_power = 0., 0.
        return tot_power

    @staticmethod
    def txt_to_csv():
        path = './materials/capacitance.txt'
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

    @staticmethod
    def plot_data(**kwargs):

        group = kwargs.get('group', 'All')
        plot = Plot()
        title = "Thermal capacity - {:s}".format(group)

        axs = plot.set_plot_area(title)
        ax = axs[0, 0]
        ax.set_yscale('log')
        ax.set_xlabel('T [K]')
        ax.set_ylabel('Cu [J / kg / K]')
        data = Capacitor.kint_v_temp
        groups = Capacitor.kint_groups
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
