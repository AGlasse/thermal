#!/usr/bin/python
import time
import numpy as np
from filer import Filer
from plot import Plot
from closed_loop import ClosedLoop as CL, ClosedLoop


class ThermalGrid:

    """ Model system as a grid of uniformly sized cells, suitable for the METIS
    echelle and mount.
    """
    model = None
    frame_time = None
    scale_length = 0.01                                                                     # Cell size in metres
    cond_ge, cond_al, cond_ss304, cond_cu, cond_ptfe = 600., 78.55, 7.435, 600., 0.228      # Conductivity at 70 K. (W / m / K)
    cp_ge, cp_al, cp_ss304, cp_cu, cp_ptfe = 130., 298.3, 177.4, 171.8, 275.6               # Specific heat capacity at 70 K, (J / kg / K)
    density_ge, density_al, density_ss304, density_cu, density_ptfe = 5320, 2700, 8000, 8960, 2200  # Density (kg / m3)
    thermal_props = {'Ge': (density_ge, cp_ge, cond_ge),
                     'Al_6061': (density_al, cp_al, cond_al),
                     'SS_304': (density_ss304, cp_ss304, cond_ss304),
                     'Cu': (density_cu, cp_cu, cond_cu),
                     'PTFE': (density_ptfe, cp_ptfe, cond_ptfe),
                     'water': (1000., 4200., 0.6)}

    def __init__(self):
        _ = Filer()
        return

    def run(self):
        model_name = 'bg_load_5j_1000sec'
        model_path = './data/' + model_name

        init_name = 'bg_noload_stable'       # ''
        if init_name == '':         # No initialisation model.  Load model from disk
            model = Filer.load_grid_model(model_path, ThermalGrid.thermal_props)
        else:                       # Initialise from existing model output.
            init_path = './data/' + init_name
            model = Filer.read_pickle(init_path)
            model['tmp_grid_init'] = model['tmp_grid_final']        # Start new model with old temperature grid.
            model['tmp_grid_final'] = None
            model['parameters']['duration'] = 18000.0
            # Explicitly turn on periodic heat load at mount.
            heat_load = model['elements']['mnt_rad']
            heat_load['power'] = 0.5
            heat_load['period'] = 1000.0
            # Patch up sen_m1 plot colour
            sen_m1 = model['elements']['sen_m1']
            sen_m1['colour'] = 'grey'
        delta_time = ThermalGrid.get_frame_time(model)
        Plot.plot_grid(model)
        just_plot = True
        if not just_plot:
            parameters, elements,tgrid = model['parameters'], model['elements'], model['tmp_grid_init']
            sim_duration, t_sampling = parameters['duration'], parameters['t_sampling']
            n_cells = tgrid.size
            n_frames = int(sim_duration / delta_time)
            print("Simulation duration = {:10.3f} seconds".format(sim_duration))
            print("Frame time 1/'{:3.1f}' minimum time constant = {:10.3f}".format(t_sampling, delta_time))
            print("..run will require {:d} frames and {:d} cells.".format(n_frames, n_cells))
            model = ThermalGrid.launch(model, n_frames, delta_time)
            Filer.write_pickle(model_path, model)

        model = Filer.read_pickle(model_path)

        plot_model = True
        if plot_model:
            Plot.plot_grid(model)
        Plot.plot_output(model, plot_pid=False)
        return

    @staticmethod
    def launch(model, n_frames, t_frame):
        """ To begin with, we just keep the current and previous grids.  We will add time series sampling for selected
        cross-sections later.
        """
        parameters, elements, tgrid = model['parameters'], model['elements'], model['tmp_grid_init']
        scale_length, duration = parameters['scale_length'], parameters['duration']
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
        x_cls, y_cls, z_cls = None, None, None
        if cls is not None and clh is not None:
            CL(model)
            output = output | CL.series_keys
            x_cls, y_cls, z_cls = cls['corner1']

        u = np.array(tgrid)
        u_next = np.array(u)
        ds2 = scale_length ** 2
        ds3 = scale_length * ds2
        plot_all = False
        t_start = time.time()
        u_terms = np.zeros(6)

        for f in range(0, n_frames):
            du_dt_max = 0.
            output['t_sim'].append(t_sim)
            for name in elements:
                element = elements[name]
                cat = element['category']
                x1, y1, z1 = element['corner1']
                geom = element['geom']
                if cat in ['sen', 'cls']:
                    output[name].append(u[x1, y1, z1])
                    continue
                x2, y2, z2 = element['corner2']
                if cat in 'bth':
                    u_bth = ThermalGrid.get_bth_temperature(element, t_sim)
                    u_next[x1:x2, y1:y2, z1:z2] = u_bth
                    output[name].append(u_bth)
                    continue

                material = element['material']
                density, cp, cond = ThermalGrid.thermal_props[material]
                k_therm = geom * cond / (cp * density)  # Units m2 / sec
                n_cells = element['n_cells']

                du_dt_htr = 0.
                if cat in ['htr', 'clh']:
                    power = 0.
                    if cat in 'htr':
                        power = ThermalGrid.get_htr_power(element, t_sim)
                    if cat in 'clh':
                        u_cls = u[x_cls, y_cls, z_cls]
                        power, output = CL.get_power(u_cls, t_sim, t_frame, output)
                    output[name].append(power)
                    du_dt_htr = power / (n_cells * cp * density * ds3)      # dT_dt per cell

                for x in range(x1, x2):
                    for y in range(y1, y2):
                        for z in range(z1, z2):
                            u_terms[0] = u[x + 1, y, z]
                            u_terms[1] = u[x - 1, y, z]
                            u_terms[2] = u[x, y + 1, z]
                            u_terms[3] = u[x, y - 1, z]
                            u_terms[4] = u[x, y, z + 1]
                            u_terms[5] = u[x, y, z - 1]
                            # g_list = [gx, gx, gy, gy, gz, gz]
                            # g_list = [1., 1., 1., 1., 1., 1.]
                            du_in = 0.
                            bool = ~np.isnan(u_terms)
                            idx_vals = np.argwhere(bool).flatten()
                            for i in idx_vals:
                                du_in += u_terms[i]
                            n_pts = np.count_nonzero(bool)
                            dku_in = k_therm * du_in
                            dku_out = n_pts * k_therm * u[x, y, z]
                            du_dt_con = (dku_in - dku_out) / ds2
                            du_dt = du_dt_con + du_dt_htr
                            du_dt_max = du_dt_max if du_dt_max > du_dt else du_dt
                            du = du_dt * t_frame
                            u_next[x, y, z] = u[x, y, z] + du

            if f % 1000 == 0:
                est_t_frame = (time.time() - t_start) / (f + 1)
                frames_left = n_frames - f
                est_t_left = est_t_frame * frames_left
                ThermalGrid._print_time(est_t_left, "\rEstimated time left =" )
                if plot_all:
                    Plot.plot_grid((parameters, elements, u))

            u = np.array(u_next)
            t_sim += t_frame
        model['tmp_grid_final'] = np.array(u)
        model['time_series'] = output
        model = CL.finalise(model)
        t_run = time.time() - t_start
        print()
        ThermalGrid._print_time(t_run, "Measured run time =")
        return model

    @staticmethod
    def _print_time(t, leader):
        t_sec = t % 60.
        t_min = t // 60. % 60.
        t_hour = t // 3600.
        time_fmt = "{:5.0f} hr, {:5.0f} min, {:5.0f} sec"
        fmt = leader + time_fmt
        print(fmt.format(t_hour, t_min, t_sec), end=' ')
        return

    @staticmethod
    def get_frame_time(model):
        parameters, elements = model['parameters'], model['elements']
        sl, t_sampling = parameters['scale_length'], parameters['t_sampling']
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
    def get_htr_power(htr, t_sim, t_start_delay=30.):
        """ Find heater power as a function of time, where the 'on' time falls at the end of the period.
        t_start_delay is a power off period at the start of the simulation, to allow settling...
        """
        if t_sim < t_start_delay:
            return 0.
        period = htr['period']
        time_on = htr['time_on']
        phase_on = time_on / period
        phase = ((t_sim - t_start_delay) % period) / period
        power = 0. if phase > phase_on else htr['power']
        return power

    @staticmethod
    def get_bth_temperature(bth, t_sim):
        period = bth['period']
        time_on = bth['time_on']
        phase_on = time_on / period
        phase = (t_sim % period) / period
        u_bth = bth['init_temp']
        if phase < phase_on:
            delta_temp = bth['delta_temp']
            u_bth += delta_temp
        return u_bth

