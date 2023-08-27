import datetime
import glob
import json

import sys
import os
from pathlib import Path
import gc

import argparse
import logging
from pathlib import Path

#import signal
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import pylab

from scipy.signal import spectrogram


import sys
import os
#import signal
import numpy as np
# main function
from pathlib import Path

# Import logging features
import logging


def log_and_raise(msg, exception_type=ValueError):
    logging.error(msg)
    raise exception_type(msg)


# create a function called sdr_load_db which creates a list of dictionary objects from the json files in the file_path directory and returns that list.
# The function takes the following parameters:
# file_path - a string that is a directory path
# 
# The function will return a list of dictionary objects.
def sdr_load_db(file_path):
    # check of valid parameters
    
    # verify file_path is a string or Path or None
    if not isinstance(file_path, (str, Path, type(None))):
        log_and_raise('The file_path is not a string, Path or None')
        
    # create a list of dictionary objects
    json_dict_list = []
    
    # get a list of the json files in the file_path directory
    json_files = glob.glob(os.path.join(file_path, '*.json'))
    
    # loop through the json files
    for json_file in json_files:
        # open the json file
        with open(json_file, 'r') as fp:
            # load the json file into a dictionary object
            logging.debug(f'Loading {json_file}')
            json_dict = json.load(fp)
            # add the dictionary object to the list
            json_dict_list.append(json_dict)
            
    # return the list of dictionary objects
    return json_dict_list

# This function will load a capture file and return the data as a numpy array. The input is a dictionary with the following keys:
#     full_file_name: the name of the capture file with path
# The function also accepts an optional parameter which is new_file_path which is a string that is the path to the new file. If this parameter 
# is not None, then the function will load the file specified by the key 'file_name' using the path specified by new_file_path. 
# new_file_path can be None in which case the file specified by the key 'file_name' will be loaded using the path specified by the key 'file_path'. This can also be a PAth object or a string
# The function returns the data as a numpy array. the function also returns the full file name of the file that was loaded.
def load_capture_file(params, new_file_path=None):
    # check that params is a dict and the parameter dictionary has the correct keys
    if not isinstance(params, dict):
        raise TypeError('params must be a dictionary')
    if not 'full_file_name' in params:
        raise ValueError('params must have full_file_name key')
    if not isinstance(params['full_file_name'], str):
        raise TypeError('params[\'full_file_name\'] must be a string')
    
    # check that new_file_path is a string, Path object,  or None
    if not isinstance(new_file_path, (str, Path, type(None))):
        raise TypeError('new_file_path must be a string, Path, or None')
    
    # if new_file_path is not None, then check that it is a valid path
    if new_file_path is not None:
        if isinstance(new_file_path, str):
            full_file_name =Path(new_file_path, params['file_name'])
        elif isinstance(new_file_path, Path):
            full_file_name = new_file_path / params['file_name']
        else:
            raise TypeError('new_file_path must be a string, Path, or None')        
    else:
        full_file_name = Path(params['full_file_name'])
        
    if not full_file_name.exists():
        raise ValueError(f'The full_file_name {full_file_name} does not exist')
    if not full_file_name.is_file():
        raise ValueError(f'The full_file_name {full_file_name} is not a file')
        
    # open the file with np.load and check for errors
    try:

        data = np.load(full_file_name)

    except:
        print('Error opening file: ', full_file_name)
        raise
    
    # return the data
    return (data, full_file_name)


# This function will render a spectrogram to a file. The file will be saved in the same directory as the data file
# The file name will be the same as the data file with the extension changed to .png
# If index is None, then all the records in the database will be used, by looping through the database. Index can also be a list of indexes or a scalar index
# Each file will be saved in the same directory as the data file
# If file_path is None, then the file will be saved in the same directory as the data file
# This will return a list of the full file names of the spectrogram files
# A lot of code was used to clear the memory after each spectrogram was rendered. This was done to prevent the memory from filling up and causing the program to crash.
# which matplotlib is sensitive to. Below are references describing this in detail
# [1] https://github.com/matplotlib/mplfinance/issues/483
# [2] http://datasideoflife.com/?p=1443
# [3] https://stackoverflow.com/questions/2364945/matplotlib-runs-out-of-memory-when-plotting-in-a-loop
#
def render_spectrogram_to_file(sdr_db, index_arg=None, new_file_path=None):
    
    # Desired figure size: (width, height)
    fig_width = 10  # in inches
    fig_height = 6  # in inches
    
    # Save the current backend
    original_backend = matplotlib.get_backend()
    print(f"Original backend is {original_backend}")
    if original_backend != 'Agg':
        matplotlib.use('Agg')
        print(f"Changed backend to {matplotlib.get_backend()}")
        import matplotlib.pyplot as plt
    
    # If index is None, then use the first record in the database
    if index_arg is None:
        index_list = range(len(sdr_db))
    # if index is a scalar, then use that index
    elif isinstance(index_arg, int):
        index_list = [index_arg]
    # if index is a list, then use that list
    elif isinstance(index_arg, list):
        index_list = index_arg
    else:
        raise ValueError("index must be None, an int, or a list")
               
    full_image_file_name_list=[]
    
    for index in index_list:
        # If file_path is None, then use the same directory as the data file
        if new_file_path is None:
            full_file_path = Path(sdr_db[index]['file_path'])
        else:
            full_file_path = Path(new_file_path)
            
        sample_rate = sdr_db[index]['sample_rate']
        
        # Load the capture file
        (x, full_file_name)=load_capture_file(sdr_db[index], new_file_path=full_file_path)
        
        print(f"Processing {full_file_path}") 
        
        full_image_file_name = Path(full_file_name).with_suffix('.png')
        
        (frequencies, times, spectrogram_data)= spectrogram(x, fs=sample_rate, nperseg=128, noverlap=64,return_onesided=False, mode='complex', scaling='density')

        # Why fftshift is needed https://github.com/scipy/scipy/issues/5757#issuecomment-259482424
        frequencies = np.fft.fftshift(frequencies)
        spectrogram_data = np.fft.fftshift(spectrogram_data, axes=0)
        # create a unique colormap to use for the spectrogram plot
        cmap = plt.get_cmap('viridis')

        fig = plt.figure(figsize=(fig_width, fig_height))
        ax = fig.add_subplot(111)
        ph=ax.pcolormesh(times,frequencies, 10*np.log10(np.abs(spectrogram_data)), cmap=cmap)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Frequency (Hz)')
        #set the colorbar
        fig.colorbar(ph, ax=ax)
     
        ax.set_title('Spectrogram')

        # Save the figure to a PNG file
        fig.savefig(full_image_file_name)
        
        # This is a lot of code to clear the memory after each spectrogram was rendered. This was done to prevent the memory from filling up and causing the program to crash.
        plt.close()     
        pylab.close(fig)
        gc.collect()
        
        full_image_file_name_list.append(full_image_file_name)
        print(f"Saved spectrogram to {full_image_file_name}")

    if original_backend != 'Agg':
        matplotlib.use(original_backend)
        print(f"Changed backend back to {matplotlib.get_backend()}")
        
    return full_image_file_name_list

def setup_logging(args):
    # Set up logging
    logging.basicConfig(filename=args.logging_file, level=args.logging_level, format='%(asctime)s %(levelname)s %(funcName)s: %(message)s')
    logging.info("Logging initialized.")

def validate_file_path(file_path):
    path = Path(file_path)
    if not path.exists():
        raise argparse.ArgumentTypeError(f"The file {file_path} does not exist!")
    return path

def main():
    parser = argparse.ArgumentParser(description="Command-line interface for rf_tools.")

    # Global arguments
    parser.add_argument("--logging-file", default=Path("app.log"), type=Path, help="Path to the logging file.")
    parser.add_argument("--logging-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Set the logging level.")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 'render_spectrogram_to_file' command
    render_parser = subparsers.add_parser("render_spectrogram_to_file", help="Render spectrogram to file.")
    render_parser.add_argument("sdr_db_file_path", type=validate_file_path, help="Path to the SDR DB file.")

    # Parse arguments
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    setup_logging(args)

    if args.command == "render_spectrogram_to_file":
        sdr_db = sdr_load_db(file_path=args.sdr_db_file_path)
        print(f"Loaded {len(sdr_db)} records from {new_file_path}")
        render_spectrogram_to_file(sdr_db, new_file_path=args.sdr_db_file_path)
    else:
        parser.print_help()

# def main():
    
#     # set the sample_rate, center_freq_Hz, time_to_collect_sec, sdr_type
#     sample_rate = 1_024_000
#     center_freq_Hz = int(100e6)
#     time_to_collect_sec = 10
#     freq_start_Hz = int(90e6)
#     freq_end_Hz = int(100e6)
#     freq_step_Hz = int(1e6)
#     sdr_type = 'rtlsdr'
    

   
#     # setup logging to save to a file
#     logging_file = Path.home() / 'log' / 'sdr_get_samples.log'
    
#     logging.basicConfig(filename=logging_file, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(funcName)s: %(message)s')

#     # create a file_path $HOME/sdr_db. Use the path object. If it already exists, then don't create it.
#     file_path = Path.home() / 'data' / 'sdr_db'      
#     if not file_path.exists():
#         file_path.mkdir()
#         logging.debug(f'Created the path for the data {file_path}')



      
# test to see if running as a standalone script and not imported then run main()
if __name__ == '__main__':
    main()
    