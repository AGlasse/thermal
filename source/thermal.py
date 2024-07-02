#!/usr/bin/python
import math
import numpy as np
import matplotlib.transforms as mtrans
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, BoxStyle
from plot import Plot
from conductor import Conductor
from heat_source import HeatSource
from capacitor import Capacitor


class Thermal:

    capacity, conductivity = None, None
    elements, conductors, heat_sources = None, None, None

    def __init__(self):
        return

    @staticmethod
    def load_model():
        # Unique name, Material, mass/kg, temperature/K
        element1 = Capacitor('E1', 'Al_6061', 10.0, 280.0, plot_data=True)
        element2 = Capacitor('E2', 'Al_6061', 10.0, 140.0)
        element3 = Capacitor('E3', 'Al_6061', 10.0, 140.0)
        Thermal.elements = [element1, element2, element3]
        # Name, Material, length/m, xs_area/m2
        conductor1 = Conductor('C1', 'Cu_RRR=100', 0.1, 0.01, plot_data=True)
        conductor2 = Conductor('C2', 'Cu_RRR=100', 0.1, 0.01)
        conductor3 = Conductor('C3', 'Cu_RRR=100', 0.1, 0.01)
        conductor1.link(element1, element2)
        conductor2.link(element1, element3)
        conductor3.link(element2, element3)
        Thermal.conductors = [conductor1, conductor2, conductor3]
        # heat_source1 = HeatSource('H1', 1000.)  # , sinvar=(1., 600.))           # Name, power, kw = 'sinvar, power, period'
        # heat_source1.link(element1)
        # Thermal.heat_sources = [heat_source1]
        Thermal.plot_model()
        return

    @staticmethod
    def plot_model():
        plot = Plot()
        axs = plot.set_plot_area('Temperature v Time', aspect='equal')
        ax = axs[0, 0]
        ax.set_xlim([-1, 1.])
        ax.set_ylim([-1, 1.])

        box_style = BoxStyle('circle', pad=0.)
        w, h = 0.45, 0.45
        theta = 0.
        radius = .5
        n_elements = len(Thermal.elements)
        dtheta = 2. * math.pi / n_elements
        for element in Thermal.elements:
            xc, yc = radius * math.sin(theta), radius * math.cos(theta)
            theta += dtheta
            element.position = xc, yc
            xbl, ybl = xc - w/2., yc - h/2.
            xtr, ytr = xbl + w, ybl + h
            bb = mtrans.Bbox([[xbl, ybl], [xtr, ytr]])
            box = FancyBboxPatch((bb.xmin, bb.ymin), abs(bb.width), abs(bb.height),
                                 boxstyle=box_style, lw=2., fc='lightgrey', ec='lightgrey')
            text = element.get_text()
            ax.add_patch(box)
            ax.text(xc, yc, text,
                    fontsize=10, color='blue', backgroundcolor='lightgrey',
                    va='center', ha='center')
        for conductor in Thermal.conductors:
            pos1, pos2 = conductor.element1.position, conductor.element2.position
            xc, yc = 0.5 * (pos1[0] + pos2[0]), 0.5 * (pos1[1] + pos2[1])

            arrow = FancyArrowPatch(pos1, pos2)
            text = conductor.get_text()
            ax.add_patch(arrow)
            ax.text(xc, yc, text,
                    fontsize=10, color='black', backgroundcolor='lightgrey',
                    va='center', ha='center'
                    )
        plot.show()
        return

    @staticmethod
    def run():
        delta_time = 1.                    # 10 second tick
        run_time = 10000.                   # Run for n seconds
        elements = Thermal.elements
        for time in np.arange(0., run_time, delta_time):
            for element in elements:
                element.find_new_temperature(time, delta_time)
            for element in elements:
                element.apply_new_temperature()
        Thermal.plot_profiles(elements)
        return

    @staticmethod
    def plot_profiles(elements):
        plot = Plot()
        axs = plot.set_plot_area('Temperature v Time')
        ax = axs[0, 0]
        for element in elements:
            label = element.name
            xy = np.array(element.temp_v_time)
            ax.plot(xy[:, 0], xy[:, 1], label=label)
        ax.legend()
        plot.show()

        axs = plot.set_plot_area('Heat flow (watt) v Time')
        ax = axs[0, 0]
        for element in elements:
            label = element.name
            xy = np.array(element.power_v_time)
            ax.plot(xy[:, 0], xy[:, 1], label=label)
        ax.legend()
        plot.show()
        return
