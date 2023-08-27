# Overview 
This is currently a bare bones repository containing tools to use GNURadio from Jupyter Notebooks
and manage collection capture and analysis. 

* functions collect data and save. Each collect is a directory and can be thought of as a table
* functions to scan RF bands. Creates a bunch of 
* functions to search data

This assumes GNURadio has been installed, but not build from scratch. therefore to get this code to work you need to set the `PYTHONPATH` to first point to your notebook virtual environment, then the system python which contains gnuradio modules. This is a hack, but so far it has been successful for me. An example of the `PYTHONPATH` is given below

```
PYTHONPATH=/home/user/src/rf_analysis/.rf_analysis/lib/python3.10/site-packages:/usr/lib/python3/:/usr/lib/python3/dist-packages
```

If using VScode this can be included in the `.env` file in your root path.


