#!/usr/bin/python
from conductor import Conductor
import numpy as np
from plot import Plot
from filer import Filer


class Capacitor:

    # temp_v_time, power_v_time = None, None
    kint_v_temp, kint_groups = None, None
    cool_v_temp, cool_groups = None, None
    index = 0

    def __init__(self, name, material, mass, temperature, color, **kwargs):
        self.name, self.material, self.mass, self.temperature, self.color = name, material, mass, temperature, color
        # Instantaneous heat flow into capacitor due to conduction, radiation, cooling
        self.con_power, self.rad_power = 0., 0.

        self.cooler_name = kwargs.get('cooler', None)
        self.new_temperature = self.temperature
        self.connectors, self.radiators = [], []
        self.temp_v_time, self.power_v_time = [], []
        self.position = 0., 0.      # Tuple holding the position of the element in the thermal model diagram
        if Capacitor.kint_v_temp is None:
            filer = Filer()
            Capacitor.kint_v_temp, Capacitor.kint_groups = filer.load_data('capacity.csv')
            Capacitor.cool_v_temp, Capacitor.cool_groups = filer.load_data('coolers.csv')
        self.active_paths = {'con': None, 'rad': None, 'cool': None}
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
        cool_power = 0.
        if self.cooler_name is not None:
            temp = self.temperature
            cool_temps = Capacitor.cool_v_temp['Temp']
            cool_powers = Capacitor.cool_v_temp[self.cooler_name]
            cool_power = np.interp(temp, cool_temps, cool_powers)
            self.active_paths['cool'] = True
        tot_power = self.con_power + self.rad_power - cool_power
        heat = tot_power * delta_time
        self.temperature = Capacitor.get_new_temperature(self, heat)
        # self.power_v_time.append([time, self.con_power, self.rad_power, cool_power])
        self.con_power, self.rad_power = 0., 0.
        return tot_power

    # def apply_new_temperature(self):
    #     self.temperature = self.new_temperature
    #     return

    def attach_connector(self, connector):
        self.connectors.append(connector)
        self.active_paths['con'] = True
        return

    def attach_radiator(self, radiator):
        self.radiators.append(radiator)
        self.active_paths['rad'] = True
        return

    @staticmethod
    def get_new_temperature(element, heat):
        material = element.material
        temp = element.temperature
        temps = Capacitor.kint_v_temp['Temp']
        caps = Capacitor.kint_v_temp[material]
        cap = np.interp(temp, temps, caps)
        new_temperature = temp + heat / (element.mass * cap)
        return new_temperature

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
