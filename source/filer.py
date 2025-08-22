#!/usr/bin/python
import numpy as np
import pickle


class Filer:

    def __init__(self):
        return

    @staticmethod
    def load_grid_model(model_path, params):
        """ The geometry (cuboid), and physical properties of each record in the .csv file are loaded into
        'element' dictionary objects, and their footprint in the temperature grid is initialised.  The mass of the
        element provided in the .csv file (from AM's model) is compared to the calculated mass from the simulation
        geometry.
        """
        scale_length, duration = None, None
        parameters = {}
        csv_file = model_path + '.csv'
        print('Loading model ' + csv_file)
        elements, closed_loop = {}, {'int_e_dt': 0., 'u_err_old': 0.}
        tgrid = np.full((400, 400, 400), np.nan)
        with open(csv_file, 'r') as text_file:
            records = text_file.read().splitlines()
            for record in records:
                print(record)
                tokens = record.split(',')
                if tokens[0][0] == '#':  # Skip comment lines
                    continue
                cat = tokens[0]
                if cat in 'scale':
                    scale_length = float(tokens[1])         # Model cell pitch in metres
                    parameters['scale_length'] = scale_length
                    continue
                if cat in 'duration':
                    parameters['duration'] = float(tokens[1])
                    continue
                if cat in 't_sampling':
                    t_sampling = float(tokens[1])
                    parameters['t_sampling'] = t_sampling
                    continue
                if cat in 'cl_target':
                    cl_target = float(tokens[1])
                    closed_loop['cl_target'] = cl_target
                    continue
                if cat in 'cl_rms':
                    cl_error = float(tokens[1])
                    closed_loop['cl_rms'] = cl_error
                    continue
                if cat in 'hdr':  # Header text is uncommented for colour coded .csv identification.
                    continue
                name = tokens[1].strip()
                corn1_f = np.array([tokens[2], tokens[3], tokens[4]], dtype=float) / scale_length
                corn1 = corn1_f.astype(int) + 1
                size_f = np.array([tokens[5], tokens[6], tokens[7]], dtype=float) / scale_length
                size = size_f.astype(int)
                n_cells = np.prod(size)
                geom_f = float(tokens[8])
                colour = tokens[9].strip()
                corn2 = corn1 + size
                elm = {'category': cat, 'name': name, 'n_cells': n_cells,
                       'corner1': corn1, 'corner2': corn2, 'geom': geom_f, 'colour': colour}

                if cat in ['sen', 'cls']:
                    elements[name] = elm
                    if cat in 'cls':
                        closed_loop['cls'] = elm
                    continue
                init_temp = float(tokens[11])
                elm['init_temp'] = init_temp

                material = tokens[10].strip()
                elm['material'] = material
                mass = float(tokens[12])
                elm['mass'] = mass

                el_volume = size[0] * size[1] * size[2] * scale_length**3
                el_density = params[material][0]
                vol_mass = el_density * el_volume
                print(".csv mass = {:5.2f} kg, density x volume= {:5.2f} kg".format(mass, vol_mass))

                tgrid[corn1[0]:corn2[0], corn1[1]:corn2[1], corn1[2]:corn2[2]] = init_temp
                if cat in 'elm':  # Get thermal coefficients and check file v calculated mass consistency
                    elements[name] = elm
                    continue
                if cat in ['htr', 'clh', 'bth']:
                    val = float(tokens[13])
                    elm['power'] = val
                    if cat in ['htr', 'bth']:
                        elm['time_on'] = float(tokens[14])
                        elm['period'] = float(tokens[15])
                        if cat in 'bth':
                            elm['delta_temp'] = float(tokens[16])
                    else:
                        closed_loop['clh'] = elm
                elements[name] = elm

        # Trim the grid to minimum required size.
        is_nan = np.isnan(tgrid)
        is_not_nan = np.logical_not(is_nan)
        arg_not_nan = np.argwhere(is_not_nan)
        nx, ny, nz = tuple(np.amax(arg_not_nan, axis=0))
        tgrid = np.array(tgrid[0:nx + 2, 0:ny + 2, 0:nz + 2])
        # parameters = scale_length, duration, t_sampling, cl_target, cl_error
        model = {'parameters': parameters, 'elements': elements, 'tmp_grid_init': tgrid, 'tmp_grid_final': None,
                 'time_series': None, 'closed_loop': closed_loop}
        return model

    @staticmethod
    def load_data(file_name):
        path = './materials/' + file_name
        print('Loading ' + path)
        data, group = {}, {}
        with open(path, 'r') as text_file:
            records = text_file.read().splitlines()
            group_rec = records[2]
            group_tokens = group_rec.split(',')
            index_rec = records[3]
            index_tokens = index_rec.split(',')
            vals = []
            for row, record in enumerate(records[4:]):
                row_vals = []
                tokens = record.split(',')
                for col, token in enumerate(tokens):
                    val = np.nan if token == '' else float(token)
                    row_vals.append(val)
                vals.append(row_vals)
            text = file_name + " data available for - \n"
            for col, token in enumerate(index_tokens):
                col_vals = []
                for row in range(0, len(vals)):
                    val = vals[row][col]
                    col_vals.append(val)
                data[token] = col_vals
                group[token] = group_tokens[col]
                text += " {:s},".format(token)
                if col % 6 == 0:
                    text += "\n"
            print(text)
        temps = np.array(data['Temp'])
        for material in data.keys():
            v_nan = np.array(data[material])
            v = Filer.replace_nans(temps, v_nan)
            data[material] = v
        return data, group

    @staticmethod
    def replace_nans(temps, vals):
        """ Replace nan values in kints with linear interpolated values.  Assume K(0) = 0.0 and K(T>Tmax) = K(Tmax)
        """
        is_nans = np.isnan(vals)
        n = len(temps)
        vals_out = np.zeros(n)
        t_los, t_his, k_los, k_his = np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(n)
        t_lo, k_lo = 0., 0.
        for i in range(0, n):
            is_nan = is_nans[i]
            if is_nan:
                t_lo, k_lo = t_lo, k_lo
            else:
                t_lo, k_lo = temps[i], vals[i]
            t_los[i], k_los[i] = t_lo, k_lo
        t_hi, k_hi = t_lo, k_lo
        for i in range(n-1, -1, -1):
            is_nan = is_nans[i]
            (t_hi, k_hi) = (t_hi, k_hi) if is_nan else (temps[i], vals[i])
            t_his[i], k_his[i] = t_hi, k_hi
        for i in range(0, n):
            if is_nans[i]:
                t_lo, t_hi, k_lo, k_hi = t_los[i], t_his[i], k_los[i], k_his[i]
                dk_dt = 0.0 if t_hi == t_lo else (k_hi - k_lo) / (t_hi - t_lo)
                vals_out[i] = k_lo + dk_dt * (temps[i] - t_lo)
            else:
                vals_out[i] = vals[i]
        return vals_out

    @staticmethod
    def read_pickle(pickle_root):
        if pickle_root[-4:] != '.pkl':
            pickle_root += '.pkl'
        file = open(pickle_root, 'rb')
        python_object = pickle.load(file)
        file.close()
        return python_object

    @staticmethod
    def write_pickle(pickle_root, python_object):
        file = open(pickle_root + '.pkl', 'wb')
        pickle.dump(python_object, file)
        file.close()
        return




