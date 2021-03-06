#!/usr/bin/env python

"""
 Background:
 --------
 EPIC_xlsx2nc.py
 
 
 Purpose:
 --------
 Convert excel .xlsx files into epic netcdf files.  

 Requirements:
 -------------
 Header Row must only include 'time' (str representation as mm/dd/yy hh:mm:ss) and epic variable names

 See EcoFOCI_config/epickkey.json for valid keys but any key can be made up.

 History:
 --------
 2018-04-23: SBELL - add ability to include a notes column
 2016-12-02: SBELL - Add ctd/profile routines

"""

# System Stack
import os
import sys
import datetime
import argparse
from collections import OrderedDict, defaultdict

# Science Stack
import numpy as np
import pandas as pd

# User defined Stack
from io_utils.ConfigParserLocal import get_config
from io_utils.EcoFOCI_netCDF_write import (
    NetCDF_Create_Timeseries,
    NetCDF_Create_Profile,
)
from calc.EPIC2Datetime import EPIC2Datetime, Datetime2EPIC

__author__ = "Shaun Bell"
__email__ = "shaun.bell@noaa.gov"
__created__ = datetime.datetime(2016, 8, 11)
__modified__ = datetime.datetime(2016, 8, 11)
__version__ = "0.1.0"
__status__ = "Development"
__keywords__ = "Mooring", "data", "netcdf", "epic", "excel", "xlsx"


"""--------------------------------main Routines---------------------------------------"""

parser = argparse.ArgumentParser(
    description="Convert excel data into epic flavored netcdf files"
)
parser.add_argument(
    "ExcelDataPath",
    metavar="ExcelDataPath",
    type=str,
    help="full path to excel (.xlsx) data file",
)
parser.add_argument(
    "ExcelSheet", metavar="ExcelSheet", type=str, help="Relevant Sheet name in workbook"
)
parser.add_argument(
    "OutDataFile", metavar="OutDataFile", type=str, help="full path to output data file"
)
parser.add_argument(
    "config_file_name",
    metavar="config_file_name",
    type=str,
    help="name of config file - eg  epickeys/TRANS_300_epickeys.json",
)
parser.add_argument("-ctd", "--ctd", action="store_true", help="File is a CTD file")
parser.add_argument(
    "--latlondep",
    nargs=3,
    type=float,
    help="latitude, longitude, depth of mooring file",
)
parser.add_argument("--history", nargs=1, type=str, help="universal history notes")

args = parser.parse_args()

wb = pd.read_excel(
    args.ExcelDataPath,
    sheet_name=args.ExcelSheet,
    na_values=[1e35, "1E+35", " 1E+35"],
    parse_dates=True,
)
wb.rename(columns=lambda x: x.strip(), inplace=True)
wb.fillna(1e35, inplace=True)
if args.ctd:
    wb.sort_values(by="dep", ascending=True, inplace=True)

print(wb.info())

if args.config_file_name.split(".")[-1] in ["json", "pyini"]:
    EPIC_VARS_dict = get_config(args.config_file_name, "json")
elif args.config_file_name.split(".")[-1] in ["yaml"]:
    EPIC_VARS_dict = get_config(args.config_file_name, "yaml")
else:
    print("config files must have .pyini, .json, or .yaml endings")
    sys.exit()

# cycle through and build data arrays
# create a "data_dic" and associate the data with an epic key
# this key needs to be defined in the EPIC_VARS dictionary in order to be in the nc file
# if it is defined in the EPIC_VARS dic but not below, it will be filled with missing values
# if it is below but not the epic dic, it will not make it to the nc file
data_dic = {}
for column in wb.keys():
    print("{column} in file".format(column=column))
    data_dic[column] = wb[column].to_dict(into=OrderedDict).values()


if args.history:
    try:
        history = args.history[0] + "\n" + data_dic["Notes"][0]
    except:
        history = args.history[0]
else:
    try:
        history = data_dic["Notes"][0]
    except:
        history = ""

if args.latlondep:
    (lat, lon, depth) = args.latlondep
else:
    (lat, lon, depth) = (-9999, -9999, -9999)

"""if data_dic['Bottom Depth']:
	bottom_depth = data_dic['Bottom Depth'][0]
else:
	bottom_depth = 9999"""

#%%
if not args.ctd:
    ### Time should be consistent in all files as a datetime object
    # convert timestamp to datetime
    time1, time2 = np.array(Datetime2EPIC(data_dic["time"]), dtype="f8")
    ncinstance = NetCDF_Create_Timeseries(savefile=args.OutDataFile)
    ncinstance.file_create()
    ncinstance.sbeglobal_atts(raw_data_file=args.ExcelDataPath.split("/")[-1])
    ncinstance.dimension_init(time_len=len(time1))
    ncinstance.variable_init(EPIC_VARS_dict)
    ncinstance.add_coord_data(
        depth=depth, latitude=lat, longitude=lon, time1=time1, time2=time2
    )
    ncinstance.add_data(EPIC_VARS_dict, data_dic=data_dic)
    ncinstance.close()
else:
    print(data_dic["time"])
    time1, time2 = np.array(Datetime2EPIC(data_dic["time"]), dtype="f8")

    ncinstance = NetCDF_Create_Profile(savefile=args.OutDataFile)
    ncinstance.file_create()
    ncinstance.sbeglobal_atts(
        raw_data_file=args.ExcelDataPath.split("/")[-1],
        CruiseID=data_dic["Cruise"][0],
        Station_Name=data_dic["Cast"][0],
        Cast=data_dic["Cast"][0],
        Water_Depth=depth,
    )
    ncinstance.dimension_init(depth_len=len(data_dic["dep"]))
    ncinstance.variable_init(EPIC_VARS_dict)
    ncinstance.add_coord_data(
        depth=data_dic["dep"],
        latitude=float(data_dic["lat"][0]),
        longitude=float(data_dic["lon"][0]),
        time1=time1[0],
        time2=time2[0],
    )
    ncinstance.add_data(EPIC_VARS_dict, data_dic=data_dic)
    ncinstance.add_history(history)
    ncinstance.close()
