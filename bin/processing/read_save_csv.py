#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 31 14:59:53 2019

@author: julia
"""

import pandas as pd

def read_data(path,file):
    df = pd.read_csv(path+file, sep=",", header=2, skipfooter=1, engine="python",
                       parse_dates={'datetime': ['DATE', 'TIME']},
                       index_col="datetime")
    
    df.columns = [x.lower() for x in df.columns]
    dtype = df.columns[df.dtypes.eq(object)]
    df[dtype] = df[dtype].apply(pd.to_numeric, errors="coerce")
    return df

def save_data(path, file, df):
    df.to_csv(path + file, index_label="datetime")