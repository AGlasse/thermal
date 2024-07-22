#!/usr/bin/python
""" Created on Feb 21, 2023

@author: achg
"""
import matplotlib.pyplot as plt
import numpy as np


class Plot:

    def __init__(self):
        return

    @staticmethod
    def set_plot_area(title, **kwargs):

        import matplotlib.pyplot as plt

        figsize = kwargs.get('figsize', [12, 9])
        xlim = kwargs.get('xlim', None)            # Common limits for all plots
        ylim = kwargs.get('ylim', None)            # Common limits for all plots
        xlabel = kwargs.get('xlabel', '')          # Common axis labels
        ylabel = kwargs.get('ylabel', '')
        ncols = kwargs.get('ncols', 1)             # Number of plot columns
        nrows = kwargs.get('nrows', 1)
        remplots = kwargs.get('remplots', None)
        aspect = kwargs.get('aspect', 'auto')      # 'equal' for aspect = 1.0
        fontsize = kwargs.get('fontsize', 16)

        plt.rcParams.update({'font.size': fontsize})

        sharex = xlim is not None
        sharey = ylim is not None
        fig, ax_list = plt.subplots(nrows, ncols, figsize=figsize,
                                    sharex=sharex, sharey=sharey,
                                    squeeze=False)
        fig.patch.set_facecolor('white')
        fig.suptitle(title)

        for i in range(0, nrows):
            for j in range(0, ncols):
                ax = ax_list[i,j]
                ax.set_aspect(aspect)       # Set equal axes
                if xlim is not None:
                    ax.set_xlim(xlim)
                if ylim is not None:
                    ax.set_ylim(ylim)
                if (i == nrows-1 and j == 0):
                    ax.set_xlabel(xlabel)
                    ax.set_ylabel(ylabel)
        if remplots is not None:
            rps = np.atleast_2d(remplots)
            for i in range(0, len(rps)):
                ax_list[rps[i,0], rps[i,1]].remove()
        return fig, ax_list

    @staticmethod
    def _make_colours(n_colours):
        """ Generate a list of colours """
        colours = []
        r, g, b = 0.0, 0.0, 0.0         # Always start with black
        for i in range(0, n_colours):
            r += 0.9
            g += 0.3
            b += 0.5
            r = r if r < 1.0 else r - 1.0
            g = g if g < 1.0 else g - 1.0
            b = b if b < 1.0 else b - 1.0
            colours.append([r, g, b])
        return colours

    @staticmethod
    def _get_text_position(xlim, ylim, **kwargs):
        pos = kwargs.get('pos', 'tl')
        inset = kwargs.get('inset', [0.1, 0.1])
        posdict = {'tl': 0, 'tr': 1}

        xr = xlim[1] - xlim[0]
        xt = xlim[0] + inset[0] * xr
        yr = ylim[1] - ylim[0]
        yt = ylim[1] - inset[1] * yr

        return xt, yt

#    @staticmethod
    def plot_points(self, ax, x, y, **kwargs):
        """ Plot an array of points in the open plot region. """

        n_pts = len(x)
        fs = kwargs.get('fs', 'none')
        mk = kwargs.get('mk', 'o')
        mew = kwargs.get('mew', 1.0)
        ms = kwargs.get('ms', 3)
        colour = kwargs.get('colour', 'black')
        rgb = kwargs.get('rgb', None)
        if rgb is None:
            ax.plot(x, y, color=colour, clip_on=True,
                    fillstyle=fs, marker=mk, mew=mew, ms=ms, linestyle='None')
        else:
            for i in range(0, n_pts):
                ax.plot(x[i], y[i], color=rgb[:, i], clip_on=True,
                        fillstyle=fs, marker=mk, mew=mew, ms=ms)
        return

    def plot_line(self, ax, x, y, **kwargs):
        colour = kwargs.get('colour', 'black')
        ls = kwargs.get('linestyle', '-')
        lw = kwargs.get('linewidth', 1.0)

        ax.plot(x, y, clip_on=True, linestyle=ls, linewidth=lw, color=colour)
        return

    def plot_point(self, ax, xy, **kwargs):
        """ Plot a single point in the open plot region.
        """
        import numpy as np
        xyList = np.array([[xy[0]], [xy[1]]])
        self.plot_points(ax, xyList, **kwargs)

    def plotCoverage(self, pars, **kwargs):
        nConfigs = len(pars)
        wLim = kwargs.get('wlim', [2.7, 5.7])
        paLim = kwargs.get('ylim', [5.0, 7.5])

        self.setPlotArea('Prism angle v Wavelength Coverage',
                         wLim, 'Wavelength [micron]',
                         paLim, 'Prism angle [deg]')
        ax = self.axList[0, 0]
        eaMin = -7.0
        eaMax =  7.0
        for i in range(0, nConfigs):
            (ea, so, pa, w1, w2, w3, w4) = pars[i]
            f = (ea - eaMin) / (eaMax - eaMin)
            r = 0.2
            g = f
            b = 1.0 - f
            print(r, g, b)
            ax.plot([w1,w4], [pa,pa],
                    color=[r,g,b], linestyle='-', linewidth=2.0)
        self.show()

    @staticmethod
    def show():
        """ Wrapper for matplotlib show function. """
        import matplotlib.pyplot as plt
        plt.show()
