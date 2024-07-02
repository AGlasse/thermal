#!/usr/bin/python
import numpy as np


class Filer:

    def __init__(self):
        return

    @staticmethod
    def load_data(file_name):
        path = '../materials/' + file_name
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



