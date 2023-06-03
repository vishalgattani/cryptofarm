import logging
import time
from os import environ

from coinmetrics.api_client import CoinMetricsClient
from dateutil import parser

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
import datetime

import numpy as np
import pandas as pd
from tqdm import tqdm

pd.options.mode.chained_assignment = None  # default='warn'
from pathlib import Path


class Coinmetrics_API:
    def __init__(self) -> None:
        try:
            self.api_key = environ["CM_API_KEY"]
            logging.info("Using API key found in environment")
        except KeyError:
            self.api_key = ""
            logging.info("API key not found. Using community client")

        self.client = CoinMetricsClient(self.api_key)
        self.btcwithsupply = None
        self.data = None
        self.btc_data = None
        self.flag = True

    def btcSupplyOnDate(self, date):
        """Provide BTC supply on a given date."""
        """https://github.com/coinmetrics/api-client-python/blob/master/examples/notebooks/sample_api_v4.ipynb

        Returns:
            _type_: _description_
        """
        asset_metrics = self.client.get_asset_metrics(
            assets=["BTC"],
            metrics=["SplyCur"],
            start_time=date,
            end_time=date,
            frequency="1d",
        ).to_dataframe()
        return float(asset_metrics.SplyCur[0])

    def get_supply_till_date(
        self, till_date=datetime.date.today(), from_date=datetime.date(2009, 1, 5)
    ):
        fname = f"btcwithSupply from {str(from_date)}-{str(till_date)}.csv"
        idx = pd.date_range(
            from_date, till_date - datetime.timedelta(days=1)
        )  # date.today - 1
        result = pd.DataFrame()
        result = result.reindex(idx, fill_value=None)
        result.reset_index(inplace=True)
        result.columns = ["date"]

        result["x"] = result.date.apply(lambda x: x.strftime("%Y-%m-%d"))

        result.head()
        df_year_lst = result.groupby(result.date.dt.year)
        df_list = []
        for year, df in df_year_lst:
            df_list.append(df)

        for i in df_list:
            i.reset_index(inplace=True)

        l = []
        for i in df_list:
            l1 = []
            print(i["x"][0])
            for j in tqdm(range(len(i))):
                val = self.btcSupplyOnDate(i["x"][j])
                time.sleep(0.5)
                # print(i["x"][j],val)
                l1.append(val)
            l.append(l1)

        mergedlist = []
        for i in l:
            mergedlist.extend(i)

        se = pd.Series(mergedlist)
        result["btcSupplyOnDate"] = se.values
        self.btcwithsupply = result[["date", "btcSupplyOnDate"]]

        self.btcwithsupply.to_csv(fname)
        self.btcwithsupply = pd.read_csv(fname)
        self.btcwithsupply.set_index("date", inplace=True)
        self.btcwithsupply = self.btcwithsupply[["btcSupplyOnDate"]]

    def combine_data(self):
        self.btc_data.index = pd.DatetimeIndex(self.btc_data.index)
        self.btcwithsupply.index = pd.DatetimeIndex(self.btcwithsupply.index)
        self.data = pd.concat([self.btc_data, self.btcwithsupply], axis=1)
        # idx = pd.date_range('01-05-2009', '11-11-2021')
        # self.data = self.data.reindex(idx,fill_value=None)
        # self.data.to_csv("data.csv")

    def get_data(self):
        return self.data

    def get_data_to_csv(self, fname="data.csv"):
        print(f"Output stored in '{fname}'.")
        self.data.to_csv(fname)


def calculate_s2f(data, days):
    assert all(x in data.columns for x in ["totalBTC", "btc_supply_by_dates"])

    data["diff_totalBTC"] = data["totalBTC"].diff(days)
    data["diff_btc_supply_by_dates"] = data["btc_supply_by_dates"].diff(days)
    data["diff_supplyPeriodAgo"] = data["btc_supply_by_dates"].shift(days)
    data["s2f_ratio_" + str(days)] = (data["diff_supplyPeriodAgo"]) / (
        (data["diff_btc_supply_by_dates"]) / days * 365
    )
    data["s2f_ratio_usd_" + str(days)] = 0.18 * data["s2f_ratio_" + str(days)] ** 3.3

    data = data.drop(
        ["diff_totalBTC", "diff_btc_supply_by_dates", "diff_supplyPeriodAgo"], axis=1
    )
    return data
