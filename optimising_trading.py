#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 14 01:19:35 2021

@author: christian
"""

from datetime import datetime
from alpaca_trade_api.rest import TimeFrame
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import plot_roc_curve
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import confusion_matrix, plot_confusion_matrix, ConfusionMatrixDisplay
from sklearn.metrics import accuracy_score
from scipy.interpolate import make_interp_spline
from sklearn import metrics
import time
from datetime import datetime, timedelta
import glob
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib
import warnings
import yfinance as yf
import re
import ast
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit
warnings.simplefilter(action = 'ignore')
plt.rcParams["figure.figsize"] = 10, 5

def main() :
    f_acc(p = 0.8, l= 60, probability = True, acc_level = False, plots = True, verbose = True)

    
def f_acc(p = 0.6, l = 60, probability = True, acc_level = False, plots = False, verbose = False):
            
    all_p = pd.read_csv('./data/record_all_predictions.csv')
    all_p['Date'] = pd.to_datetime(all_p['Date'])
    today = datetime.now()
    start = datetime(2021, 1, 9, 0, 0, 0, 0)
    all_p = all_p[all_p['Date'] > start]
    
    # today = datetime.now()
    # recent = today - timedelta(days=1)
    # all_p = all_p[all_p['Date'] <= recent].dropna()
    
    if verbose :
        print('\n\nAll accuracy is : %a perc'% np.round(accuracy_score(all_p['Prediction'], all_p['Outcome'], normalize = True) * 100,2))
    
    df = all_p
    df['Prob'] = df['Probability']
    df['Prob'].mask(df['Prob'] < 0.5, 1-df['Prob'], inplace=True)
    
    level =  np.round(np.linspace(0.5,1,num=50),3)
    
    acc = []
    days = []
    delta = []
    for ll in level :
        df_ = df[df['Prob']>ll]
        df_ = df_.groupby(by=['Date','Traded']).mean()
        df_['Prediction'][df_['Prediction']>0] = 1
        df_['Prediction'][df_['Prediction']<0] = -1
        acc.append(np.round(accuracy_score(df_['Prediction'], df_['Outcome'], normalize = True) * 100,2))
        # print('\n\nAccuracy at %a is : %a perc'% (ll,acc[-1]))
        days.append(round(df_.groupby(by=['Date']).count().mean().Prediction,2))
        # print('Number of trades per day : %a' % days[-1])
        temp = df_['Prediction'] * df_['Delta']
        delta.append(np.round(temp.mean()*100,2))
        if np.isnan(days[-1]) :
            break
    
    def Exp(x, A, B, C):
        y = C + A*np.exp(B*x)
        return y
    
    acc = acc[:-1]
    level = level[:len(acc)]
    days = days[:-1]
    delta = delta[:-1]
    true_level = level
    true_acc = acc
    
    try :
        parameters, covariance = curve_fit(Exp, level, acc)
        level = np.linspace(0.5,max(level),100)
        acc = parameters[2]+parameters[0]*np.exp(parameters[1]*level)
    except :
        print('\nExponential fit failed, trying linear interpolation\n')
        acc = np.maximum.accumulate(acc)
        df = pd.DataFrame({'l': true_level, 'a' : acc, 'd' : days, 'de': delta}).drop_duplicates(['a'], keep='last')
        acc = np.array(df['a'])
        true_level = np.array(df['l'])
        days = np.array(df['d'])
        delta = np.array(df['de'])
        true_acc = acc
        inter = interp1d(true_level, acc, fill_value="extrapolate")
        acc = inter(level)
    
    if plots :
        plt.figure()
        plt.plot(true_level, true_acc, '*', label = "True Accuracy")
        plt.plot(level, acc, 'o', label = "Accuracy from regression")
        plt.xlabel('Probability level')
        plt.ylabel('Accuracy')
        plt.legend(loc='upper left')
        
        plt.figure()
        fig,ax = plt.subplots()
        ax.plot(level, acc ,color="blue", label = 'accuracy')
        plt.legend(loc='upper right')
        ax.set_xlabel('Probability level',fontsize=14)
        ax.set_ylabel('accuracy',color="blue",fontsize=14) 
        ax2=ax.twinx()
        ax2.plot(true_level, days,color="red", label = 'Trades per day')
        ax2.set_ylabel('Trades per day',color="red",fontsize=14)
        plt.legend(loc='upper left')
        #plt.savefig('./Images/trades per day per level.png')
        plt.show()
        
        
        plt.figure()
        fig,ax = plt.subplots()
        ax.plot(level, acc ,color="blue", label = 'accuracy')
        plt.legend(loc='upper right')
        ax.set_xlabel('Probability level',fontsize=14)
        ax.set_ylabel('accuracy',color="blue",fontsize=14) 
        ax2=ax.twinx()
        ax2.plot(true_level, delta ,color="red", label = 'Return')
        ax2.set_ylabel('Average daily delta',color="red",fontsize=14)
        plt.legend(loc='upper left')
        #plt.savefig('./Images/average return per level.png')
        plt.show()
    
    p_level = level[np.where(np.array(acc)>l)[0][0]]
    d_level = days[np.where(np.array(true_acc)>l)[0][0]]
    if p < 0.5 :
        p = 1-p
    acc_p = acc[np.where(np.array(level)>p)[0][0]]
    
    if verbose :
        print('\nUsing probability threshold of %a\n' %p_level)
        print('\nAverage number of trades per day at this level %a\n' %d_level)
        print('\nAccuracy at probability level %a\n' %np.round(acc_p,2))
    
    if p_level < 0.55 :
        print('\nFound probability level to low ({}), raising it to 0.6'.format(p_level))
        p_level = 0.6
        
    if p_level > 0.7 :
        print('\nFound probability level to high ({}), lowering it to 0.6'.format(p_level))
        p_level = 0.6
    
    if probability :
        return np.round(acc_p/50,3)
    
    if acc_level :
        return np.round(p_level,3)

if __name__ == "__main__":
    main()



    