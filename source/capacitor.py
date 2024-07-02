#!/usr/bin/python
from conductor import Conductor
import numpy as np
from plot import Plot
from filer import Filer


class Capacitor:

    name, material, mass, temperature, new_temperature = None, None, None, None, None
    temp_v_time, power_v_time = None, None
    index, data, groups = None, None, None

    def __init__(self, name, material, mass, temperature, **kwargs):
        self.name = name
        self.material = material
        self.mass = mass
        self.temperature = temperature
        self.new_temperature = temperature
        self.connectors, self.heat_sources = [], []
        self.temp_v_time, self.power_v_time = [], []
        self.position = 0., 0.      # Tuple holding the position of the element in the thermal model diagram
        if Capacitor.data is None:
            plot_data = kwargs.get('plot_data', False)
            filer = Filer()
            data, groups = filer.load_data('capacity.csv')
            Capacitor.data, Capacitor.groups = data, groups
            if plot_data:
                Capacitor.plot_data(group='Marvel')
        return

    def get_text(self):
        text = "{:s}\n{:s}\n{:.1f} kg\n{:.1f} K".format(self.name, self.material, self.mass, self.temperature)
        return text

    def find_new_temperature(self, time, delta_time):
        """ Find the new temperature of this body after delta_time by summing the heat flow from connected
        elements.  The new temperature must be applied once they have been calculated for all elements.
        """
        power = 0.0
        self.temp_v_time.append([time, self.temperature])
        # text = ''
        for connector in self.connectors:
            con_power = Conductor.heat_flow(self, connector)
            # text += "{:10.1f}".format(con_power)
            power += con_power
        for heat_source in self.heat_sources:
            hs_power = heat_source.get_power(delta_time)
            # text += "{:10.1f}".format(hs_power)
            power += hs_power
        # print(text)
        heat = power * delta_time
        self.new_temperature = Capacitor.get_new_temperature(self, heat)
        self.power_v_time.append([time, power])
        return power

    def apply_new_temperature(self):
        self.temperature = self.new_temperature
        return

    def attach_connector(self, connector):
        self.connectors.append(connector)
        return

    def attach_heat_source(self, heat_source):
        self.heat_sources.append(heat_source)
        return

    @staticmethod
    def get_new_temperature(element, heat):
        material = element.material
        temp = element.temperature
        temps = Capacitor.data['Temp']
        caps = Capacitor.data[material]
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
        data = Capacitor.data
        groups = Capacitor.groups
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
