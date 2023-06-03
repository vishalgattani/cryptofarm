import datetime
import warnings
from os import environ

import numpy as np
import pandas as pd
from coinmetrics.api_client import CoinMetricsClient
from tqdm import tqdm

warnings.simplefilter(action="ignore", category=FutureWarning)

pd.options.mode.chained_assignment = None  # default='warn'
import logging
import sys
import time
from pathlib import Path

import chart_studio
import chart_studio.plotly as cspy
import chart_studio.tools as tls
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objs as go
import plotly.io as pio
from _plotly_future_ import v4_subplots
from plotly.offline import download_plotlyjs, init_notebook_mode, iplot, plot

from plotly_credentials import api_key, username
from print_utils import Printer
from utils import Coinmetrics_API, calculate_s2f

chart_studio.tools.set_credentials_file(username=username, api_key=api_key)


def read_btc_data_from_csv(fname="btc_updated.csv"):
    data = pd.read_csv(fname)
    data["time"] = pd.to_datetime(data["time"]).apply(lambda x: x.date())
    data = data.drop(["Unnamed: 0"], axis=1)
    return data


def days_between(d1, d2):
    d1 = datetime.strptime(d1, "%Y-%m-%d")
    d2 = datetime.strptime(d2, "%Y-%m-%d")
    return abs((d2 - d1).days)


def btcSupplyAtBlock(b):
    if b >= 33 * 210000:
        return 20999999.9769
    else:
        reward = 50e8
        supply = 0
        y = 210000
        while b > y - 1:
            supply = supply + y * reward
            reward = int(reward / 2.0)
            b = b - y
        supply = supply + b * reward
        # print(supply,reward)
        return (supply + reward) / 1e8


def btcRewardAtBlock(b):
    if b >= 33 * 210000:
        return 20999999.9769
    else:
        reward = 25e8
        supply = 0
        y = 210000
        while b > y - 1:
            supply = supply + y * reward
            reward = int(reward / 2.0)
            b = b - y
        supply = supply + b * reward

        return reward / 1e8


def get_s2f_table():
    genesis = "2009-01-01"
    halving_dates = [
        "2009-01-01",
        "2012-11-28",
        "2016-09-07",
        "2020-05-11",
        "2024-05-01",
        "2028-05-01",
        "2032-05-01",
    ]

    sftable = pd.DataFrame(columns=["date", "StockBTC", "RewardBTC", "FlowBTC"])
    sflist = []
    # sftable.columns = ["Date","StockBTC","RewardBTC","FlowBTC"]
    for date in halving_dates:
        block = days_between(genesis, date) * 24 * 6
        d1 = datetime.strptime(date, "%Y-%m-%d")
        l = [
            d1,
            btcSupplyAtBlock(block),
            btcRewardAtBlock(block),
            365 * 24 * 60 * 0.1 * btcRewardAtBlock(block),
        ]
        sflist.append(l)
        # print(date + " - " + str(btcSupplyAtBlock(block))+ " - " + str(btcRewardAtBlock(block)))
    sftable = pd.DataFrame(sflist, columns=["date", "StockBTC", "RewardBTC", "FlowBTC"])
    # sftable['date'] = pd.to_datetime(sftable['date'], format='%y-%m-%d')

    sftable.set_index("date", inplace=True)
    sftable["s2f"] = sftable.StockBTC / sftable.FlowBTC
    return sftable


def get_btc_info_yesterday():
    asset_metrics = client.get_asset_metrics(
        assets=["BTC"],
        metrics=metrics,
        start_time=date_yesterday,
        end_time=date_yesterday,
        frequency="1d",
    ).to_dataframe()

    return asset_metrics


def d_parser(s):
    return pd.to_datetime(s, format="%Y-%m-%d")


try:
    api_key = environ["CM_API_KEY"]
    logging.info("Using API key found in environment")
except KeyError:
    api_key = ""
    logging.info("API key not found. Using community client")

client = CoinMetricsClient(api_key)
# starting_date = datetime.datetime(2009, 1, 3)


btc_csv = Path("./btc.csv")
assert (
    btc_csv.exists()
), "download data from 'https://coinmetrics.io/community-network-data/'"


def add_btc_info(df):
    df["time"] = pd.to_datetime(df["time"]).dt.strftime("%Y-%m-%d")
    df["BlkHeight"] = df.BlkCnt.cumsum()
    df["Reward"] = 50 / (2 ** np.floor(df["BlkHeight"] / 210000))
    df["BTCGenFrmBlk"] = df.BlkCnt * df["Reward"]
    df["totalBTC"] = df.BTCGenFrmBlk.cumsum()
    return df


df = pd.read_csv("btc.csv", low_memory=False)
df = add_btc_info(df)


updated_btc_csv = Path("./btc_updated.csv")
if not updated_btc_csv.exists():
    btc_supply_by_dates = []
    my_API_fetcher = Coinmetrics_API()
    for i in tqdm(range(len(df))):
        btc_supply_by_dates.append(my_API_fetcher.btcSupplyOnDate(df.iloc[i].time))
        time.sleep(0.5)
    df["btc_supply_by_dates"] = btc_supply_by_dates
    df.to_csv("btc_updated.csv")


# metrics = df.columns.to_list()[1:]
# last_date_in_data = df.time.iloc[-1]
# date_today = datetime.date.today()
# date_yesterday = date_today - datetime.timedelta(days=1)

# delta = date_yesterday - last_date_in_data   # returns timedelta
# for i in range(delta.days + 1):
#     day = last_date_in_data + datetime.timedelta(days=i)
#     print(day)


data = read_btc_data_from_csv("btc_updated.csv")
data = calculate_s2f(data, 463)
data = calculate_s2f(data, 10)

idx = pd.date_range("01-01-2009", "05-01-2032")
# idx = pd.date_range('08-01-2010', '05-01-2032')
result = data.copy(deep=True)
result = result[
    [
        "time",
        "BlkCnt",
        "BlkHeight",
        "Reward",
        "CapRealUSD",
        "PriceBTC",
        "BTCGenFrmBlk",
        "totalBTC",
        "btc_supply_by_dates",
        "s2f_ratio_463",
        "s2f_ratio_usd_463",
        "s2f_ratio_10",
        "s2f_ratio_usd_10",
    ]
]
result = result.set_index(["time"])
result = result.reindex(idx, fill_value=None)
Printer.blue(result.columns)
result.loc["2024-05-02"]["Reward"] = 3.125
result.loc["2028-05-02"]["Reward"] = 1.5625
result = result.bfill()
result.Reward = result.Reward.ffill()
result.BlkCnt = result.BlkCnt.bfill()
result.BlkCnt = result.BlkCnt.fillna(144)
result.BTCGenFrmBlk = result.BlkCnt * result.Reward
result = result.reset_index()
lastvalidindex = result["btc_supply_by_dates"].index.get_loc(
    result["btc_supply_by_dates"].last_valid_index()
)

for i in range(lastvalidindex, len(result)):
    result.iloc[i, result.columns.get_loc("btc_supply_by_dates")] = float(0)
    result.iloc[i, result.columns.get_loc("btc_supply_by_dates")] = (
        result.iloc[i - 1, result.columns.get_loc("btc_supply_by_dates")]
        + result.iloc[i, result.columns.get_loc("BTCGenFrmBlk")]
    )

result = calculate_s2f(result, 463)
result = calculate_s2f(result, 10)

print(result.describe())

plt.plot(result["time"], result["PriceUSD"])
plt.show()
