#!/usr/bin/python
""" Created on Feb 21, 2023

@author: achg
"""

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from closed_loop import ClosedLoop as CL


class Plot:

    def __init__(self):
        return

    @staticmethod
    def plot_output(model, plot_pid=False):
        parameters, elements, output = model['parameters'], model['elements'], model['time_series']
        closed_loop = model['closed_loop']
        scale_length, duration = parameters['scale_length'], parameters['duration']
        t_sampling = parameters['t_sampling']
        cl_target = closed_loop['cl_target']
        # Group plots by colour (so all sensors on the grating should be 'orange' say.
        row = 0
        group = {}
        for name in elements:
            element = elements[name]
            cat = element['category']
            if cat in ['sen', 'htr', 'cls', 'clh']:
                colour = element['colour']
                if colour not in group.keys():
                    group[colour] = []
                    row += 1
                group[colour].append(element)
        n_plots = row
        if plot_pid and CL.series is not None:       # Extra row for closed loop parameter plot.
            n_plots += 1

        fig, ax_list = plt.subplots(figsize=(10, 8), ncols=1, nrows=n_plots, sharex=True)
        t_sim = output['t_sim']
        i = 0
        ylabel = None
        ax = None
        for colour in group:
            for element in group[colour]:
                name = element['name']
                cat = element['category']
                if 'elm' in cat:
                    continue
                ax = ax_list[i] if n_plots > 1 else ax_list
                y = output[name]
                ylabel = "T / K" if cat in ['sen', 'cls', 'bth'] else "P / W"
                ax.plot(t_sim, y, label=name, color=colour)
            ax.legend()
            ax.set_ylabel(ylabel)
            i += 1
        if plot_pid and CL.series is not None:
            ax = ax_list[i]
            t = CL.get_series('time')
            y_sum = np.zeros(t.shape)
            for term in [('q_pro', 'solid'), ('q_int', 'dashed'), ('q_dif', 'dotted')]:
                key, ls = term
                label = key[2].upper()
                y = CL.get_series(key)
                ax.plot(t, y, color='dimgrey', ls=ls, lw=1.0, label=label)
                y_sum += y
            ax.plot(t, y_sum, color='black', ls='-', lw=2., label='q_sum')
        plt.legend()
        # Plot x axis label for lowest (last) plot
        ax.set_xlabel("Time / second")
        plt.show()
        return

    @staticmethod
    def plot_grid(model):
        parameters, elements, tgrid = model['parameters'], model['elements'], model['tmp_grid_init']
        sl = parameters['scale_length']
        plot = Plot()
        fig, ax = plt.subplots(subplot_kw={"projection": "3d"}, figsize=(10, 8),
                               ncols=1, nrows=1,
                               sharex=True, sharey=True)
        title = "scale length = {:5.3f} mm".format(sl * 1000.)
        ax.set_title(title)
        nx, ny, nz = tgrid.shape
        ax.set_xlim([0., float(nx)])
        ax.set_ylim([0., float(ny)])
        # Vectorise scatter points
        xs, ys, zs, ts = [], [], [], []
        for x in range(0, nx):
            for y in range(0, ny):
                for z in range(0, nz):
                    xs.append(x)
                    ys.append(y)
                    zs.append(z)
                    t = tgrid[x, y, z]
                    if t is None:
                        continue
                    ts.append(t)
        cmap = mpl.colormaps['viridis']
        tmap = ax.scatter(xs, ys, zs, c=ts, cmap=cmap, marker='.')
        fig.colorbar(tmap, ax=ax, shrink=0.5, aspect=10)

        plot_elements = True
        if plot_elements:
            for name in elements:
                el = elements[name]
                x1, y1, z1 = el['corner1']
                x2, y2, z2 = el['corner2']
                u = np.array([[x1, x2, x2], [x2, x1, x1], [x1, x2, x2], [x2, x2, x2], [x1, x1, x2], [x1, x1, x1]]) - .5
                v = np.array([[y1, y1, y2], [y2, y2, y1], [y1, y1, y1], [y1, y2, y2], [y2, y2, y2], [y1, y1, y2]]) - .5
                w = np.array([[z1, z1, z1], [z1, z1, z1], [z2, z2, z1], [z2, z2, z1], [z1, z2, z2], [z1, z2, z2]]) - .5
                col = el['colour']
                for edge in range(0, 6):        # Draw element bounds
                    # x = np.array
                    ax.plot(u[edge], v[edge], w[edge], color=col)
                ax.text(x1, y1, z1, name, color=col)
        plt.show()
        return
