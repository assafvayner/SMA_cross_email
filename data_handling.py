import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import errno
import math

PERIOD = '360d' # to make 180 running average for 180 days
WINDOW_LONG = 180
WINDOW_SHORT = 90
DESIRED_COLUMNS = ['Close']
WEEK = 5

def gen_all_info(file_name):
    tickers, df_dict = gen_data_from_file(file_name)

    keep_list = list()
    responses = list()
    for ticker in tickers:
        crossing, signal = identify_crossing(ticker, df_dict[ticker])
        if crossing:
            keep_list.append(ticker)
            responses.append((ticker, signal))

    plot_file = gen_timeplot(df_dict, keep_list)
    return responses, plot_file

def identify_crossing(ticker, df):
    """
    determines if there is an intersection in the 
    """
    # only concerned about 1 week's worth of data
    # 5 rows
    tail = df.tail(WEEK).copy(deep=True)
    tail['SMA_diff'] = tail['SMA_LONG_Close'] - tail['SMA_SHORT_Close']
    tail['SMA_diff'] = tail['SMA_diff'].apply(abs)
    tail = tail[tail['SMA_diff'] < 0.01 * tail['SMA_LONG_Close']]
    if len(tail) > 0:
        print('There is a SMA crossing for ' + ticker + '. Detrmining what kind of crossing.')
        # return value of identify_type_of_crossing is unused
        signal = identify_type_of_crossing(ticker, df)
        return True, signal
    else:
        return False, None

def identify_type_of_crossing(ticker, df):
    """
    determines given the moving averages in the dataframe if it is correct
    to buy or sell at this time, given that there is an intersection
    """
    df = df.tail(WEEK).copy(deep=True)
    df['SMA_diff'] = df['SMA_LONG_Close'] - df['SMA_SHORT_Close']
    mean_diff = df['SMA_diff'].mean()
    
    # if difference not significant don't indicate any signal
    if abs(mean_diff) > 0.05 * df['SMA_LONG_Close'].max():
        print('no sell or buy signal for: ' + ticker)
        return None

    # if the mean difference used to be negative then the LONG WINDOW SMA
    # is now going above the SHORT WINDOW SMA which is a sell signal
    if mean_diff < 0:
        print('SELL signal for: ' + ticker)
        return False

    # if the condition is false, and mean_diff was positive, then the
    # SHORT WINDOW SMA is going above the LONG WINDOW SMA which is a
    # buy signal
    print('BUY signal for: ' + ticker)
    return True

def gen_data_from_file(tickers_filename):
    """
    generates a dict of dataframes of closing price and simple moving averages
    for all valid tickers in a file

    if tickers_filename is not a file in the directory this function is run
    the function raise a FileNotFound exception
    """
    desired_tickers = read_tickers(tickers_filename)

    df_dict = dict()

    for ticker in desired_tickers:
        df = gen_SMA_df(ticker)
        if df is None:
            desired_tickers.remove(ticker)
            print('No data found for ticker: ' + ticker)
        else:
            df_dict[ticker] = df

    return desired_tickers, df_dict


def gen_timeplot(df_dict=None, tickers=None):
    """
    creates time plots of the daily closing price and the simple
    moving average given a list of valid tickers and a dict with matching 
    ticker keys from the list and corresponding data frame values
    formatted like the output of 'gen_SMA_df'.

    if only df_dict is passed, then tickers is set to 'list(df_dict.keys())'


    creates one figure with all graphs

    can also take a single ticker string and single dataframe
    and create a timeplot for a single ticker this way
    
    if no input is given for 'df_dict' or 'df_dict' is not a dict returns None
    if tickers or df_dict are of an invalid type raises TypeError
    if the length of tickers and df_dict do not match or the length of either
    is 0, returns None
    """
    if df_dict is None:
        return None 

    # make graph for all dataframes in the dict if not specific list given
    if tickers is None:
        tickers = list(df_dict.keys())

    if len(tickers) == 0 or len(df_dict) == 0 or not tickers[0] in df_dict.keys():
        return None 

    # parameters are 1 string and 1 dataframe, convert to list and
    # dict of dataframe to continue function for expected inputs
    if isinstance(tickers, str) and isinstance(df_dict, pd.DataFrame):
        df_dict = {tickers: df_dict}
        tickers = [tickers]

    if not isinstance(tickers, list):
        raise TypeError("tickers must be a list of tickers, or a single string ticker")

    if not isinstance(df_dict, dict) or not isinstance(df_dict[tickers[0]], pd.DataFrame):
        raise TypeError("df_dict must be a dictionary of dataframs or a single dataframe")

    temp = []
    for ticker in tickers:
        if not ticker in df_dict.keys():
            print(ticker + ' not in df_dict.keys(), cannot create plot for: ' + ticker)
            continue
        temp.append(ticker)
    ticker = temp

    size = len(tickers)

    ncols = math.ceil(math.sqrt(size))
    nrows = math.ceil(size / ncols)
    fig, axs = plt.subplots(nrows, ncols, figsize=(ncols * 6, nrows * 4))
   
    # edge case in plt.subplots returns a single axis object when
    # nrows and ncols are both 1, or a 1D numpy array of axes when
    # nrows is 1 and ncols is 2, convert to 2D numpy array of axis
    # to mimic normal output of plt.subplots
    if size == 1:
        axs = np.array([[axs]])
    elif size == 2:
        axs = np.array([axs])

    row = 0
    col = 0

    for i in range(size):
        title = tickers[i] + ': Closing Price And SMA of Closing Price'
        df_dict[tickers[i]].plot(ax=axs[row, col], title=title)
        col += 1
        if col >= ncols:
            col = 0
            row += 1
        # no bound check on rows, size <= nrows * ncols must be true

    fig.canvas.set_window_title("Plot:")
    fig.tight_layout()

    img_name = 'plot_SMA_' + str(tickers)[1:-1].replace(', ','_').replace('\'','') + '.png'
    fig.savefig(img_name)
    return img_name

def gen_SMA_df(ticker=None):
    """
    Returns a dataframe of the closing price and the 180 day simple moving
    average for the closing price for the given stock/bond ticker parameter
    if no argument is given, or the argument is not a string, returns None
    """
    if ticker is None or not isinstance(ticker, str):
        return None
    
    data = yf.Ticker(ticker)
    data = data.history(period='360d')
    data = data[DESIRED_COLUMNS]
    
    SMA_LONG_data = data.rolling(window=WINDOW_LONG).mean()
    SMA_LONG_data = SMA_LONG_data.rename(columns={'Close': 'SMA_LONG_Close'})
    SMA_LONG_data = SMA_LONG_data.dropna()

    SMA_SHORT_data = data.rolling(window=WINDOW_SHORT).mean()
    SMA_SHORT_data = SMA_SHORT_data.rename(columns={'Close': 'SMA_SHORT_Close'})
    SMA_SHORT_data = SMA_SHORT_data.dropna()

    EWA_data = data.ewm(span=WINDOW_SHORT, min_periods=WINDOW_SHORT).mean()
    EWA_data = EWA_data.rename(columns={'Close': 'EWA_Close'})

    
    SMA_join = SMA_LONG_data.join(SMA_SHORT_data).join(EWA_data).join(data)
    SMA_join = SMA_join.rename(columns={'Close': 'Single_Day_Close'})
    return SMA_join

def read_tickers(tickers_filename):
    """
    return a list of tickers from a file named by 'tickers_filename'
    if given file does not exist or is not a file raises FileNotFoundError
    """
    if not os.path.exists(tickers_filename) or not os.path.isfile(tickers_filename):
        raise FileNotFoundError(
            errno.ENOENT, os.strerror(errno.ENOENT), tickers_filename)
    
    # adding files to set to avoid duplicates in file
    tickers_set = set()
    f = open(tickers_filename)
    lines = f.readlines()
    for line in lines:
        line_len = len(line)
        if line_len > 0 and line_len <= 6: # stock ticker size limit (NASDAQ)
            tickers_set.add(line.strip())
    f.close()
    return list(tickers_set)

