import csv
import os

import barometerdrivers.smooth.smoothalgorithms as smooth


def load_sample_data():
    osr_list = [256, 512, 1024, 2048, 4096]
    sensors = ['HP206C', 'MS5803_01BA']
    filename_template = os.path.join(os.path.dirname(__file__),
                                     'osr_{}_5_second_samples.tsv')
    data = {}
    for osr in osr_list:
        with open(filename_template.format(osr), 'r') as tsv_file:
            tsv_reader = csv.reader(tsv_file, delimiter='\t', quotechar='|')
            next(tsv_reader)  # skip tsv header row
            data[osr] = {sensor: {'s': [], 'mbar': [], 'C': []}
                         for sensor in sensors}
            for sensor, _, time, temperature, pressure in tsv_reader:
                data[osr][sensor]['s'].append(float(time))
                data[osr][sensor]['C'].append(float(temperature))
                data[osr][sensor]['mbar'].append(float(pressure))
    return data


def smooth_with_kalman(data, p_estimate_err, q_process_noise, r_measure_noise):
    """
    MS5803_01BA, 4096: p=4, q=0.0625, r=4
    """
    smoother = smooth.OneDKalman(
        data[0], p_estimate_err, q_process_noise, r_measure_noise, 2)
    return _smooth_data(data[1:], smoother)


def smooth_with_rms(data, buffersize):
    smoother = smooth.RollingRootMeanSquared(data[0], buffersize, 2)
    return _smooth_data(data[1:], smoother)


def smooth_with_mean(data, buffersize):
    smoother = smooth.RollingMean(data[0], buffersize, 2)
    return _smooth_data(data[1:], smoother)


def _smooth_data(data, smoother):
    smoothed_data = [smoother.value]
    for datum in data:
        smoother.update(datum)
        smoothed_data.append(smoother.value)
    return smoothed_data
