#!/usr/bin/python
import math
import numpy as np
from matplotlib.patches import FancyArrowPatch
from plot import Plot
from conductor import Conductor
from capacitor import Capacitor
from radiator import Radiator


class Thermal:

    capacity, conductivity = None, None
    capacitors, conductors, heaters = None, None, None

    # Unique name, Material, mass/kg, temperature/K, emissivity, surface_area/m2
    # Coolers and heaters can be included,
    t_amb = 285.
    marvel_capacitors = [# 'rs_outer': Capacitor(('Al_6061', 0.103, t_amb)),
                         Capacitor('getter', 'Cu(OFHC)', .343, t_amb, 'darkgray'),
                         Capacitor('link_joint', 'Cu(OFHC)', .1, t_amb, 'pink'),
                         Capacitor('block', 'Cu(OFHC)', .132, t_amb, 'brown'),
                         Capacitor('rs_rear_cover', 'Al_6061', 0.138, t_amb, 'aqua'),
                         Capacitor('rs_front', 'Al_6061', 0.219, t_amb, 'darkturquoise'),
                         Capacitor('world', 'Cu(OFHC)', 10000., t_amb, 'orange'),
                         Capacitor('spider', 'Invar(Fe-36Ni)', 0.694, t_amb, 'green'),
                         Capacitor('pt16', 'Cu(OFHC)', 0.5, t_amb, 'dodgerblue', cooler='PT16_st')
                        ]
    # Name, Material, length/m, xs_area/m2
    marvel_conductors = [Conductor('get_pt16_bolt', 'Cu_RRR=100', .0004, 1.E-6, ['pt16', 'getter']),
                         Conductor('flexi_linkx4', 'Cu_RRR=100', .150, 4.E-5, ['getter', 'link_joint']),
                         Conductor('det_link', 'Cu_RRR=100', .170, 4.E-5, ['link_joint', 'block']),
                         Conductor('rs_link_1', 'Cu_RRR=100', .070, 1.E-5, ['block', 'rs_rear_cover']),
                         Conductor('rs_link_2', 'Cu_RRR=100', .050, 1.E-5, ['rs_front', 'rs_rear_cover']),
                         Conductor('g10_flexures', 'G10_norm-dir', .030, 1.44E-4, ['spider', 'world']),
                         Conductor('g10_support', 'G10_norm-dir', .003, 1.6E-5, ['rs_front', 'world']),
                         Conductor('spdr_blck_bolt', 'Cu_RRR=100', .0004, 1.E-6, ['spider', 'block'])
                         ]
    # name, coupling_emissivity, coupling_area (m2), cap1_name, cap2_name, plot_colour
    marvel_radiators = [Radiator('ro_1', 0.05, 0.05, ['world', 'rs_front'], 'red'),
                        Radiator('ro_2', 0.05, 0.05, ['world', 'rs_rear_cover'], 'peru'),
                        Radiator('ri_3', 0.05, 0.05, ['rs_front', 'block'], 'cadetblue'),
                        Radiator('ri_4', 0.05, 0.05, ['rs_rear_cover', 'block'], 'dodgerblue'),
                        Radiator('window', 0.2, 0.01, ['world', 'block'], 'goldenrod')
                        ]
    output = None

    def __init__(self):
        return

    @staticmethod
    def load_model():

        capacitors = []
        for capacitor in Thermal.marvel_capacitors:
            capacitors.append(capacitor)

        Thermal.capacitors = capacitors

        conductors = []
        for conductor in Thermal.marvel_conductors:
            conductor.create_links(capacitors)
            conductors.append(conductor)
        Thermal.conductors = conductors

        radiators = []
        for radiator in Thermal.marvel_radiators:
            radiator.create_links(capacitors)
            radiators.append(radiator)
        Thermal.radiators = radiators

        plot_data = False
        if plot_data:
            Capacitor.plot_data(group='Marvel')
        plot_model = True
        if plot_model:
            Thermal.plot_model()
        return

    @staticmethod
    def run():
        delta_time = 1.                     # Model tick in seconds
        run_time = 6*3600.                     # Run for n seconds
        capacitors = Thermal.capacitors
        conductors = Thermal.conductors
        radiators = Thermal.radiators
        n_caps = len(capacitors)
        heat_flow_matrix = {'con': np.zeros((n_caps, n_caps)),    # Heat flow between capacitors (conduction and radiation)
                            'rad': np.zeros((n_caps, n_caps))}

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
            color = 'blue' if capacitor.cooler_name is not None else 'green'
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
                    fontsize=10, color='red', backgroundcolor='white',
                    va='center', ha='center'
                    )
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
            ax.plot(times_hr, temperatures, label=label, color=color)
        ax.legend()
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
        ax.legend()
        plot.show()

        _, axs = plot.set_plot_area('Rate of heat gain (watt v time)')
        ax = axs[0, 0]
        ax.set_xlabel('Time / hr')
        ax.set_ylabel('Power / Watt')
        colit = iter(colors)
        for element in capacitors:
            xy = np.array(element.power_v_time)
            time_hr = xy[:, 0] / 3600.
            ls_list = ['solid', 'dashed', 'dotted']
            color=next(colit)
            for i in range(1, 4):
                tag = tags[i-1]
                ls = ls_list[i-1]
                if element.active_paths[tag]:
                    label = "{:s} {:s}".format(element.name, tag)
                    power_watt = xy[:, i]
                    ax.plot(time_hr, power_watt, ls=ls, label=label, color=color)

        ax.legend()
        plot.show()
        return
