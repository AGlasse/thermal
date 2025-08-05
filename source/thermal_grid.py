#!/usr/bin/python
import time
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from filer import Filer
from plot import Plot
from closed_loop import ClosedLoop


class ThermalGrid:

    """ Model system as a grid of uniformly sized cells, suitable for the METIS
    echelle and mount.
    """
    model, thermal_props = None, None
    frame_time = None
    scale_length = 0.01         # Cell size in metres
    cond_ge, cond_al, cond_ss304, cond_cu = 600., 78.55, 7.435, 600.    # Conductivity at 70 K. (W / m / K)
    cp_ge, cp_al, cp_ss304, cp_cu = 130., 298.3, 177.4, 171.8           # Specific heat capacity at 70 K, (J / kg / K)
    density_ge, density_al, density_ss304, density_cu = 5320, 2700, 8000, 8960            # Density (kg / m3)
    thermal_props = {'Ge': (density_ge, cp_ge, cond_ge),
                     'Al_6061': (density_al, cp_al, cond_al),
                     'SS_304': (density_ss304, cp_ss304, cond_ss304),
                     'Cu': (density_cu, cp_cu, cond_cu),
                     'water': (1000., 4200., 0.6)}

    def __init__(self):

        _ = Filer()
        return

    def run(self):
        model_name = 'box_grating'
        model_root = './data/' + model_name

        model = Filer.load_grid_model(model_root, ThermalGrid.thermal_props)
        delta_time = ThermalGrid.get_frame_time(model)
        ThermalGrid.plot_grid(model)
        just_plot = False
        if not just_plot:
            parameters, elements, tgrid = model
            _, sim_duration, t_sampling, _ = parameters
            n_cells = tgrid.size
            n_frames = int(sim_duration / delta_time)
            print("Simulation duration = {:10.3f} seconds".format(sim_duration))
            print("Frame time 1/'{:3.1f}' minimum time constant = {:10.3f}".format(t_sampling, delta_time))
            print("..run will require {:d} frames and {:d} cells.".format(n_frames, n_cells))
            model, output = ThermalGrid.launch(model, n_frames, delta_time)
            Filer.write_pickle(model_root, (model, output))

        model, output = Filer.read_pickle(model_root)
        plot_model = True
        if plot_model:
            ThermalGrid.plot_grid(model)
        ThermalGrid.plot_output(model, output)
        return

    @staticmethod
    def launch(model, n_frames, delta_time):
        """ To begin with, we just keep the current and previous grids.  We will add time series sampling for selected
        cross-sections later.
        """
        estimate_run_time = True
        t_start = time.time()
        parameters, elements, tgrid = model
        scale_length, duration, t_sampling, cl_target = parameters
        t_sim = 0.                      # Simulation time
        output = {'t_sim': []}
        cls, clh = None, None
        for name in elements:
            element = elements[name]
            cat = element['category']
            if cat in 'elm':            # Only record heater powers and sensor temperatures
                continue
            if cat in 'cls':
                cls = element
            if cat in 'clh':
                clh = element
            name = element['name']
            output[name] = []
        cloop, x_cls, y_cls, z_cls = None, None, None, None
        if cls is not None and clh is not None:
            cloop = ClosedLoop(cls, clh, cl_target)
            x_cls, y_cls, z_cls = cls['corner1']

        u = np.array(tgrid)
        u_next = np.array(u)
        ds2 = scale_length ** 2
        ds3 = scale_length * ds2
        plot_all = False

        for f in range(0, n_frames):
            if plot_all and f % 100 == 0:
                ThermalGrid.plot_grid((elements, u))
            output['t_sim'].append(t_sim)
            for name in elements:
                element = elements[name]
                cat = element['category']
                x1, y1, z1 = element['corner1']
                if cat in ['sen', 'cls']:
                    output[name].append(u[x1, y1, z1])
                    continue
                x2, y2, z2 = element['corner2']
                if 'bth' in cat:
                    u_next[x1:x2, y1:y2, z1:z2] = element['init_temp']
                    continue

                material = element['material']
                density, cp, cond = ThermalGrid.thermal_props[material]
                k_therm = cond / (cp * density)  # Units m2 / sec
                n_cells = element['n_cells']

                du_dt_htr = 0.
                if cat in ['htr', 'clh']:
                    power = 0.
                    if cat in 'htr':
                        power = ThermalGrid.get_htr_power(element, t_sim)
                    if cat in 'clh':
                        u_cls = u[x_cls, y_cls, z_cls]
                        power = cloop.get_power(u_cls, delta_time)
                    output[name].append(power)
                    du_dt_htr = power / (n_cells * cp * density * ds3)      # dT_dt per cell

                for x in range(x1, x2):
                    for y in range(y1, y2):
                        for z in range(z1, z2):
                            u_terms = np.zeros(6)
                            u_terms[0] = u[x + 1, y, z]
                            u_terms[1] = u[x - 1, y, z]
                            u_terms[2] = u[x, y + 1, z]
                            u_terms[3] = u[x, y - 1, z]
                            u_terms[4] = u[x, y, z + 1]
                            u_terms[5] = u[x, y, z - 1]
                            n_pts = np.count_nonzero(~np.isnan(u_terms))
                            dku_in = k_therm * np.nansum(u_terms)
                            dku_out = n_pts * k_therm * u[x, y, z]
                            du_dt_con = (dku_in - dku_out) / ds2
                            du_dt = du_dt_con + du_dt_htr
                            du = du_dt * delta_time
                            u_next[x, y, z] = u[x, y, z] + du

            if estimate_run_time:
                t_frame = time.time() - t_start
                t_est = t_frame * n_frames
                print("Estimated run time = {:10.1f}".format(t_est))
                estimate_run_time = False

            u = np.array(u_next)
            t_sim += delta_time
        t_run = time.time() - t_start
        print("Measured run time = {:10.1f}".format(t_run))
        model = parameters, elements, u
        return model, output

    @staticmethod
    def plot_output(model, output):
        parameters, elements, _ = model
        scale_length, duration, t_sampling, cl_target = parameters
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
        fig, ax_list = plt.subplots(figsize=(10, 8), ncols=1, nrows=n_plots, sharex=True)
        t_sim = output['t_sim']
        i = 0
        ax = None
        for colour in group:
            for element in group[colour]:
                name = element['name']
                cat = element['category']
                if 'elm' in cat or 'bth' in cat:
                    continue
                ax = ax_list[i] if n_plots > 1 else ax_list
                y = output[name]
                # colour = element['colour']
                ylabel = "Temperature / K" if cat in ['sen', 'cls'] else "Power / W"
                ax.plot(t_sim, y, label=name, color=colour)         # , marker='+'
            ax.legend()
            ax.set_ylabel(ylabel)
            i += 1
        # Plot x axis label for lowest (last) plot
        ax.set_xlabel("Time / second")
        plt.show()
        return

    @staticmethod
    def plot_grid(model):
        parameters, elements, tgrid = model
        sl, _, _, _ = parameters
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
                    x = np.array
                    ax.plot(u[edge], v[edge], w[edge], color=col)
                ax.text(x1, y1, z1, name, color=col)

        plot.show()
        return

    @staticmethod
    def get_frame_time(model, oversample=4):
        parameters, elements, _ = model
        sl, _, t_sampling, _ = parameters
        tc_min = 1000.              # Minimum time constant / seconds
        for name in elements:
            element = elements[name]
            cat = element['category']
            if cat in ['sen', 'cls', 'bth']:
                continue
            material = element['material']
            density, cp, cond = ThermalGrid.thermal_props[material]
            k_therm = cond / (cp * density)
            tc = sl * sl / k_therm
            tc_min = tc if tc < tc_min else tc_min
        frame_time = tc_min / t_sampling
        fmt = "Minimum thermal time constant is {:6.3f} seconds, (frame time = {:6.3f}, for cell size {:6.1f} mm.)"
        print(fmt.format(tc_min, frame_time, sl * 1000.))
        return frame_time

    @staticmethod
    def get_htr_power(htr, t_sim):
        # time = 11.
        period = htr['period']
        time_on = htr['time_on']
        phase_on = time_on / period
        phase = (t_sim % period) / period
        power = 0. if phase > phase_on else htr['power']
        return power

