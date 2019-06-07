#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 30 08:47:23 2019

@author: julia
"""
import pandas as pd
import math
import numpy as np

def read_data(path,file):
    '''
    Read in microtops data from a csv/txt in a pd.DataFrame.
    '''
    df = pd.read_csv(path+file, sep=",", header=2, skipfooter=1, engine="python",
                       parse_dates={'datetime': ['DATE', 'TIME']},
                       index_col="datetime")
    
    df.columns = [x.lower() for x in df.columns]
    dtype = df.columns[df.dtypes.eq(object)]
    df[dtype] = df[dtype].apply(pd.to_numeric, errors="coerce")
    return df

def save_data(path, file, df):
    '''
    Saves pd.DataFrane to selected file.
    '''
    df.to_csv(path + file, sep=" ", index=False)
    
def hourlymean(data):
    '''
    Splits the data after several (at least 5) belonging measurements, gets the
    measurement with the lowest aot936 and calculates the hourly mean of those
    values.
    
    data: pd.DataFrame containing blocks of measurements
    '''
    
    # Angstrom parameter ANG = LN(AOD440/AOD870)/LN(0.87/0.44)
    data = data.assign(ang=((data.aot440 / data.aot870).apply(math.log)
                                  / math.log(.87/.44)))
    # AOT bei 550nm AOT550 = EXP(-ANG*LN(0.55/0.44)+LN(AOT440))
    data = data.assign(aot550=(-data.ang * math.log(.55 / .44)
                                     + (data.aot440).apply(math.log)
                                     ).apply(math.exp))
    # Aerosol Index (=AOT550 * ANG)
    data = data.assign(aeroind=data.aot550 * data.ang)
    # TODO fine-mode AOT fraction  (wie anteilig tragt fine mode aerosol (r<0.5um) zur AOT550 bei)
    #data = data.assign(finefrac=data.)
    
    # setting timedeltas
    week = pd.Timedelta("7Day")
    threemins = pd.Timedelta("3Min")
    twomins = pd.Timedelta("2Min")
    
    # check for single measurements and delete them
    diff1 = abs(data.index[1:] - data.index[:-1])
    diff2 = abs(data.index[:-1] - data.index[1:])
    data = data.assign(timediff1=pd.TimedeltaIndex([threemins]).append(diff1))
    data = data.assign(timediff2=diff2.append(pd.TimedeltaIndex([twomins])))
    data = data[(data["timediff1"] < week) & (data["timediff2"] < week)]
    
    # mask for starting points of measurement blocks
    diff1 = abs(data.index[1:] - data.index[:-1])
    data = data.assign(timediff1=pd.TimedeltaIndex([threemins]).append(diff1))
    masked = data[(data["timediff1"] > twomins)]
    
    # loop through starting points and select measurements belonging together
    # to get the minimum of aot936 for every measurement block
    df_min = pd.DataFrame()
    for ix in range(0,len(masked)):
        r1 = data.index.get_loc(masked.index[ix])
        try:
            r2 = data.index.get_loc(masked.index[ix + 1])
            df = data.iloc[r1:r2]
        except IndexError:
            df = data.iloc[r1:]
        if len(df) < 5:
            continue
        temp_min = pd.DataFrame(df.loc[df.aot936.idxmin()]).T
        df_min = pd.concat([df_min, temp_min])
    
    df_min = df_min.drop(["timediff1", "timediff2"], axis=1)
    df_min = df_min.astype(float)
    
    # sample dataframe in hours
    sampled = df_min.resample("H") # per hour or per day?
    aot_cols = ["aot380", "aot440", "aot550", "aot675", "aot870", "aot936"]
    sel_df = pd.DataFrame()
    for _, df in sampled:
        # drop values per hour where value is more than 25% larger than minimum
        df = df[df["aot936"] < df["aot936"].min() * 1.25]
        # exclude aod values but not watervapor if ang < ang.mean.hour * 0.5
        df.loc[df["ang"] < df["ang"].mean() * 0.5, aot_cols] = np.nan
        sel_df = pd.concat([sel_df, df])
    
    # calculate mean per hour
    sampled = sel_df.resample("H")
    df_mean = sampled.mean().dropna(how="all")
    
    # add column with number of measurements per hour and date and hour
    df_mean = df_mean.assign(size=sampled.size())
    df_mean = df_mean.assign(date=df_mean.index.strftime("%m/%d/%y"))
    df_mean = df_mean.assign(hour=df_mean.index.strftime("%H"))
    df_mean = df_mean.round(3)
    mean_cols = ["date", "hour", "latitude", "longitude", "altitude",
                 "pressure", "sza", "am", "temp", "aot380", "aot440",
                 "aot550", "aot675", "aot870", "aot936", "water", "ang",
                 "aeroind", "size"]
    df_mean = df_mean[mean_cols]
    
    return df_mean

def main(path, readfile, savefile):
    data = read_data(path, readfile)
    data_mean = hourlymean(data)
    save_data(path, savefile, data_mean)

if __name__ == "__main__":
    path = "/Users/julia/Documents/MPI_Sonne/microtops/data/"
    readfile = "Microtops_20190604_173359_to_20190605_031800.txt"
    savefile = "test1.txt"
    main(path, readfile, savefile)
