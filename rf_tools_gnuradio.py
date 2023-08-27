import os
import numpy as np
from pathlib import Path
import logging
import datetime
import json


from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio import blocks
from gnuradio.fft import window
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import soapy


def log_and_raise(msg, exception_type=ValueError):
    logging.error(msg)
    raise exception_type(msg)

# Instructions on how to use the SoapySDR module with GNU Radio
# https://joshisanerd.com/projects/sdr_snippets/gnuradio_and_ipython//0%20First%20Attempt.html


def sdr_rtlsdr_get_samples(sample_rate = 1024000, center_freq_Hz = 100e6, time_to_collect_sec = 10):
    tb = gr.top_block()
    N = int(time_to_collect_sec*sample_rate)
    
    stream_args = ''
    tune_args = ['']
    settings = ['']
    dev = 'driver=rtlsdr'
    
    soapy_rtlsdr_source_0 = soapy.source(dev, "fc32", 1, '',
                              stream_args, tune_args, settings)
    soapy_rtlsdr_source_0.set_sample_rate(0, sample_rate)
    soapy_rtlsdr_source_0.set_gain_mode(0, False)
    soapy_rtlsdr_source_0.set_frequency(0, center_freq_Hz)
    soapy_rtlsdr_source_0.set_frequency_correction(0, 0)
    soapy_rtlsdr_source_0.set_gain(0, 'TUNER', 20)
    
    
    # Let's try to flush out the first bunch of samples
    skip_head = blocks.skiphead(gr.sizeof_gr_complex, 1)
    
    # Limit ourselves to N samples
    head = blocks.head(gr.sizeof_gr_complex, N)
    
    # And a sink to dump them into
    sink = blocks.vector_sink_c()
    
    
    tb.connect(soapy_rtlsdr_source_0, skip_head, head, sink) # Can use the handy serial connect method here
    tb.run()
    tb.stop()
    x = np.array(sink.data())
    return x

# Write a function that takes as input:
# sample_rate: which is a number
# center_freq_Hz: which is a positive number representing the frequency the sdr should be at
# time_to_collect_sec which is a positive number that is how long the collection time is
# sdr_type: a string that is either "rtlsdr" or "hackrf"
# file_path: which is a string that is the path to the file to save the samples to
# and the function calls sdr_rtlsdr_get_samples to first collect the samples and then saves them to the file_path. The file should be saved as a numpy array.
# and the name of the file should be the following where <name> is the value of the variable. The file name is:
# sdr_<sdr_type>_fc_<center_freq_Hz>_fs_<sample_rate>_YYYYMMDD_HHMMSS.npy
# where the date and time is the current date and time.
# The function should return the name of the file that was saved.
# Also the function should save a json file with the same name as the numpy file but with a .json extension. The json file should have the following fields:
# sample_rate
# center_freq_Hz
# time_to_collect_sec
# sdr_type
# file_path
# and the values should be the values of the variables.
# If there is an error, the function should return None.

def sdr_get_samples(sample_rate, center_freq_Hz, time_to_collect_sec, sdr_type='rtlsdr', file_path=None, create_directory = True):
    # verify sample_rate is a number > 0
    if not isinstance(sample_rate, (int, float)):
       log_and_raise('The sample_rate is not a number')
    if sample_rate <= 0:
       log_and_raise('The sample_rate is not a positive number')

    # verify center_freq_Hz is a number > 0
    if not isinstance(center_freq_Hz, (int, float)):
        log_and_raise('The center_freq_Hz is not a number')
    if center_freq_Hz <= 0:
        log_and_raise('The center_freq_Hz is not a positive number')
    
    # verify time_to_collect_sec is a number > 0
    if not isinstance(time_to_collect_sec, (int, float)):
        log_and_raise('The time_to_collect_sec is not a number')
    if time_to_collect_sec <= 0:
        log_and_raise('The time_to_collect_sec is not a positive number')
    
    # verify sdr_type is a string and either 'rtlsdr' or 'hackrf'
    if not isinstance(sdr_type, str):
        log_and_raise('The sdr_type is not a string')
        
    if sdr_type != 'rtlsdr' and sdr_type != 'hackrf':
        log_and_raise('The sdr_type is not "rtlsdr" or "hackrf"')
    
    # verify file_path is a string or Path or None
    if not isinstance(file_path, (str, Path, type(None))):
        log_and_raise('The file_path is not a string, Path or None')
        
    # verify create_directory is a boolean
    if not isinstance(create_directory, bool):
        log_and_raise('The create_directory is not a boolean')
               

    if file_path is not None:
        if os.path.exists(file_path) and os.path.isdir(file_path):
            logging.info(f'The file_path {file_path} exists and is a directory')
        else:
            if create_directory:
                os.mkdir(file_path)
                logging.info(f'The file_path {file_path} does not exist so creating it')
            else:
                log_and_raise(f'The file_path {file_path} is not a directory and create_directory is False')
        
        # check if the file_path is a writable directory
        if not os.access(file_path, os.W_OK):
            log_and_raise(f'The file_path {file_path} is not a writable directory')
        
        
    # collect the samples
    if sdr_type == 'rtlsdr':
        x=sdr_rtlsdr_get_samples(sample_rate = sample_rate, center_freq_Hz = center_freq_Hz, time_to_collect_sec = time_to_collect_sec)
        if not isinstance(x, np.ndarray):
            log_and_raise(f'x must be an np.ndarray')
    elif sdr_type == 'hackrf':
        log_and_raise(f'The sdr_type {sdr_type} is not supported yet')
    else:
        log_and_raise(f'The sdr_type {sdr_type} is not "rtlsdr" or "hackrf"')
    
    if file_path is not None:
        # save the numpy array x
        file_name = 'sdr_' + sdr_type + '_fc_' + str(center_freq_Hz) + '_fs_' + str(sample_rate) + '_' + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + '.npy'
        full_file_name = os.path.join(file_path, file_name)

        np.save(full_file_name, x)
        logging.info(f'Saved the numpy array to {full_file_name}')
        # save the json file
        full_json_file_name = str(full_file_name).replace('.npy', '.json')
        json_dict = {'sample_rate': sample_rate, 'center_freq_Hz': center_freq_Hz, 'time_to_collect_sec': time_to_collect_sec, 'sdr_type': sdr_type, 'file_path': str(file_path), 'file_name': str(file_name), 'full_file_name': str(full_file_name)}
        with open(full_json_file_name, 'w') as fp:
            json.dump(json_dict, fp)
            logging.info(f'Saved the json file to {full_json_file_name}')
    else:
        full_file_name = None
        full_json_file_name = None
    
    return (x, full_file_name, full_json_file_name) 

# A function called sdr_sweep that takes the following parameters:
# sample_rate   - a number > 0
# time_to_collect_sec - a number > 0
# sdr_type - a string that is either 'rtlsdr' or 'hackrf'
# freq_start_Hz - a number > 0
# freq_end_Hz - a number > 0
# freq_step_Hz - a number > 0
# file_path - a string that is a directory path
# create_directory - a boolean that is True if the directory should be created if it does not exist
# The function will start a collect samples at freq_start_Hz and then increment the frequency by freq_step_Hz until freq_end_Hz is reached.
# The function will save the samples to a file in the file_path directory.
# The function will return a list of the full file names of the saved files.
def sdr_sweep(sample_rate, time_to_collect_sec, sdr_type, freq_start_Hz, freq_end_Hz, freq_step_Hz, file_path=None, create_directory=False):
    # check of valid parameters
    # verify sample_rate is a number > 0
    if not isinstance(sample_rate, (int, float)):
        log_and_raise('The sample_rate is not a number')
    if sample_rate <= 0:
        log_and_raise('The sample_rate is not a positive number')
        
    # verify time_to_collect_sec is a number > 0
    if not isinstance(time_to_collect_sec, (int, float)):
        log_and_raise('The time_to_collect_sec is not a number')
    if time_to_collect_sec <= 0:
        log_and_raise('The time_to_collect_sec is not a positive number')
        
    # verify sdr_type is a string and either 'rtlsdr' or 'hackrf'
    if not isinstance(sdr_type, str):
        log_and_raise('The sdr_type is not a string')
    if sdr_type != 'rtlsdr' and sdr_type != 'hackrf':
        log_and_raise('The sdr_type is not "rtlsdr" or "hackrf"')
        
    # verify freq_start_Hz is a number > 0
    if not isinstance(freq_start_Hz, (int, float)):
        log_and_raise('The freq_start_Hz is not a number')
    if freq_start_Hz <= 0:
        log_and_raise('The freq_start_Hz is not a positive number')
        
    # verify freq_end_Hz is a number > 0
    if not isinstance(freq_end_Hz, (int, float)):
        log_and_raise('The freq_end_Hz is not a number')
    if freq_end_Hz <= 0:
        log_and_raise('The freq_end_Hz is not a positive number')
        
    # verify freq_step_Hz is a number > 0
    if not isinstance(freq_step_Hz, (int, float)):
        log_and_raise('The freq_step_Hz is not a number')
    if freq_step_Hz <= 0:
        log_and_raise('The freq_step_Hz is not a positive number')
        
    # verify file_path is a string or Path
    if not isinstance(file_path, (str, Path, type(None))):
        log_and_raise('The file_path is not a string, Path or None')
        
    # verify create_directory is a boolean
    if not isinstance(create_directory, bool):
        log_and_raise('The create_directory is not a boolean')
        
    # if file_path is not None, then check if the directory exists
    if file_path is not None:
        if not os.path.exists(file_path):
            if create_directory:
                os.mkdir(file_path)
            else:
                log_and_raise(f'The file_path {file_path} does not exist')
                
    # create a list of the full file names of the saved files
    full_file_names = []
    
    # loop through the frequencies
    for freq_Hz in range(freq_start_Hz, freq_end_Hz, freq_step_Hz):
        # collect the samples
        (x, full_file_name, full_json_file_name) = sdr_get_samples(sample_rate, freq_Hz, time_to_collect_sec, sdr_type, file_path=file_path, create_directory=create_directory)
        # add the full file name to the list
        full_file_names.append(full_file_name)
        
    # return the list of full file names
    return full_file_names


# main function which is useful for testing the functions
def main():
    
    # set the sample_rate, center_freq_Hz, time_to_collect_sec, sdr_type
    sample_rate = 1_024_000
    center_freq_Hz = int(100e6)
    time_to_collect_sec = 10
    freq_start_Hz = int(90e6)
    freq_end_Hz = int(100e6)
    freq_step_Hz = int(1e6)
    sdr_type = 'rtlsdr'
    

   
    # setup logging to save to a file
    logging_file = Path.home() / 'log' / 'sdr_get_samples.log'
    
    logging.basicConfig(filename=logging_file, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(funcName)s: %(message)s')

    # create a file_path $HOME/sdr_db. Use the path object. If it already exists, then don't create it.
    file_path = Path.home() / 'data' / 'sdr_db'      
    if not file_path.exists():
        file_path.mkdir()
        logging.debug(f'Created the path for the data {file_path}')
        
    # (x, full_file_name, full_json_file_name)=sdr_get_samples(sample_rate, center_freq_Hz, time_to_collect_sec, sdr_type, file_path, create_directory = True)
    # print(f"Collected {x.shape} samples.")
    # file_path = Path.home() / 'sdr_db'
    # sdr_db = sdr_load_db(file_path)
    
    full_file_name_list =  sdr_sweep(sample_rate, time_to_collect_sec, sdr_type, freq_start_Hz, freq_end_Hz, freq_step_Hz, file_path=file_path, create_directory=True)


# test to see if running as a standalone script and not imported then run main()
if __name__ == '__main__':
    main()
    