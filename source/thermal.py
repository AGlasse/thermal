#!/usr/bin/python
import math
import numpy as np
from matplotlib.patches import FancyArrowPatch
from plot import Plot
from conductor import Conductor
from capacitor import Capacitor
from radiator import Radiator
from cooler import Cooler


class Thermal:

    capacity, conductivity = None, None
    capacitors, conductors, radiators, heaters = [], [], [], []
    output = None

    def __init__(self):
        return

    @staticmethod
    def load_model(model_name):

        path = './data/' + model_name + '.csv'
        print('Loading model ' + path)
        with open(path, 'r') as text_file:
            records = text_file.read().splitlines()
            for record in records:
                print(record)
                tokens = tuple([t.strip() for t in record.split(',')])
                if len(tokens) < 1:
                    continue
                tok0 = tokens[0]
                if '#' in tok0:
                    continue
                if 'cap' in tok0:
                    capacitor = Capacitor(tokens[1:6])
                    Thermal.capacitors.append(capacitor)
                if 'coo' in tok0:
                    cooler = Cooler(tokens[1:6])
                    Thermal.capacitors.append(cooler)
                if 'con' in tok0:
                    cap_names = tokens[5].split(';')
                    caps = []
                    for cap_name in cap_names:
                        for cap in Thermal.capacitors:
                            if cap.name in cap_name:
                                caps.append(cap)
                                break
                    conductor = Conductor(tokens[1:6], caps)
                    Thermal.conductors.append(conductor)
                if 'rad' in tok0:
                    cap_names = tokens[5].split(';')
                    caps = []
                    for cap_name in cap_names:
                        for cap in Thermal.capacitors:
                            if cap.name in cap_name:
                                caps.append(cap)
                                break
                    radiator = Radiator(tokens[1:5], caps)
                    Thermal.radiators.append(radiator)

        plot_data = False
        if plot_data:
            Capacitor.plot_data(group='Marvel')
        plot_model = True
        if plot_model:
            Thermal.plot_model()
        return

    @staticmethod
    def run():
        delta_time = 1.                         # Model tick in seconds
        run_time = 1*3600.                      # Run for n seconds
        capacitors = Thermal.capacitors
        conductors = Thermal.conductors
        radiators = Thermal.radiators
        n_caps = len(capacitors)

        temp_series, con_series, rad_series = {}, {}, {}
        for cap in capacitors:
            temp_series[cap.name] = []
        for con in conductors:
            con_series[con.from_to_name] = []
        for rad in radiators:
            rad_series[rad.from_to_name] = []

        times = np.arange(0., run_time, delta_time)
        for time in times:
            for conductor in conductors:        # Calculate heat flows into all capacitors through connectors
                power, cap_a, cap_b = conductor.transfer_heat(time)
                name = cap_a.name + '->' + cap_b.name
                con_series[name].append(power)  # Heat flow from A to B
            for radiator in radiators:        # Calculate heat flows into all capacitors through connectors
                power, cap_a, cap_b = radiator.transfer_heat(time)
                name = cap_a.name + '->' + cap_b.name
                rad_series[name].append(power)  # Heat flow from A to B
            for capacitor in capacitors:        # Find new temperatures of all capacitors (and reset heat flows)
                print(capacitor.name)
                capacitor.find_new_temperature(time, delta_time)
                temp_series[capacitor.name].append(capacitor.temperature)

        Thermal.plot_profiles(capacitors, conductors, radiators, times, temp_series, con_series, rad_series)
        return

    @staticmethod
    def plot_model():
        plot = Plot()
        _, axs = plot.set_plot_area('Model elements', aspect='equal')
        ax = axs[0, 0]
        ax.set_xlim([-1, 1.])
        ax.set_ylim([-1, 1.])

        # box_style = BoxStyle('circle', pad=0.)
        w, h = 0.25, 0.25
        theta = 0.
        radius = .8
        capacitors = Thermal.capacitors
        n_elements = len(capacitors)
        dtheta = 2. * math.pi / n_elements
        for capacitor in capacitors:
            xc, yc = radius * math.sin(theta), radius * math.cos(theta)
            theta += dtheta
            capacitor.position = xc, yc
            xbl, ybl = xc - w/2., yc - h/2.
            text = capacitor.__str__()
            color = 'blue' if capacitor.is_cooler else 'green'
            ax.text(xc, yc, text,
                    fontsize=10, color=color, backgroundcolor='lightgrey',
                    va='center', ha='center')
        for conductor in Thermal.conductors:
            cap1, cap2 = conductor.capacitors[0], conductor.capacitors[1]
            pos1, pos2 = cap1.position, cap2.position
            xc, yc = 0.5 * (pos1[0] + pos2[0]), 0.5 * (pos1[1] + pos2[1]) - 0.09
            arrow = FancyArrowPatch(pos1, pos2)
            ax.add_patch(arrow)
            text = conductor.__str__()
            ax.text(xc, yc, text,
                    fontsize=10, color='black', backgroundcolor='white',
                    va='center', ha='center'
                    )
        for radiator in Thermal.radiators:
            pos1, pos2 = radiator.capacitors[0].position, radiator.capacitors[1].position
            xc, yc = 0.5 * (pos1[0] + pos2[0]), 0.5 * (pos1[1] + pos2[1]) + 0.09
            arrow = FancyArrowPatch(pos1, pos2)
            ax.add_patch(arrow)
            text = radiator.__str__()
            ax.text(xc, yc, text,
                    fontsize=10, color='red', backgroundcolor='white', va='center', ha='center')
        plot.show()
        return

    @staticmethod
    def plot_profiles(capacitors, conductors, radiators, times, temp_series, con_series, rad_series):
        plot = Plot()

        _, axs = plot.set_plot_area('Temperature v time')
        n_caps = len(capacitors)
        colors = plot._make_colours(n_caps)
        ax = axs[0, 0]
        times_hr = times / 3600.
        ax.set_xlabel('Time / hr')
        ax.set_ylabel('Temperature / K')
        for key, capacitor in zip(temp_series, capacitors):
            temperatures = temp_series[key]
            color = capacitor.color
            label = "{:s} ({:d} K)".format(capacitor.name, int(temperatures[-1]))
            ax.plot(times_hr, temperatures, label=label, color=color, ls='dotted')
        ax.legend(loc='upper right')
        plot.show()

        tags = ['con', 'rad', 'cool']
        ls_list = ['solid', 'dashed', 'dotted']

        _, axs = plot.set_plot_area('Heat flow v time')
        ax = axs[0, 0]
        ax.set_xlabel('Time / hr')
        ax.set_ylabel('Power / watt')

        for key, conductor in zip(con_series, conductors):
            tag = tags[0]
            label = "{:s} {:s}".format(conductor.from_to_name, tag)
            power_watt = con_series[key]
            color = colors[conductor.index]
            ax.plot(times, power_watt, ls=ls_list[0], label=label, color=color)
        for key, radiator in zip(rad_series, radiators):
            tag = tags[1]
            label = "{:s} {:s}".format(radiator.from_to_name, tag)
            power_watt = rad_series[key]
            color = radiator.color
            ax.plot(times, power_watt, ls=ls_list[1], label=label, color=color)
        ax.legend(loc='upper right')
        plot.show()

        return

        _, axs = plot.set_plot_area('Rate of heat gain (watt v time)')
        ax = axs[0, 0]
        ax.set_xlabel('Time / hr')
        ax.set_ylabel('Power / Watt')
        colit = iter(colors)
        for element in capacitors:
            xy = np.array(element.power_v_time)
            times_hr = times / 3600.
            ls_list = ['solid', 'dashed', 'dotted']
            color=next(colit)
            for i in range(1, 4):
                tag = tags[i-1]
                ls = ls_list[i-1]
                if element.active_paths[tag]:
                    label = "{:s} {:s}".format(element.name, tag)
                    power_watt = xy[:, i]
                    ax.plot(times_hr, power_watt, ls=ls, label=label, color=color)

        ax.legend()
        plot.show()
        return
