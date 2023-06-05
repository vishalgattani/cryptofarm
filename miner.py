import datetime

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

url = "https://www.bitrawr.com/difficulty-estimator"
rv = requests.get(url)
content = rv.text


class Difficulty_Fetcher:
    def __init__(self):
        self.url = "https://btc.com/stats/diff"
        self.difficulty = {}

    def fetch_difficulty(self):
        rv = requests.get(self.url)
        soup = BeautifulSoup(rv.text, features="html.parser")
        html_text = soup.find("div", {"class": "diff-summary"}).text
        html_text = html_text.splitlines()
        html_text = [i.strip() for i in html_text if i]
        curr_difficulty = float(
            html_text[html_text.index("Difficulty") + 1].split("-")[0].replace(",", "")
        )
        next_difficulty = float(
            html_text[html_text.index("Next Difficulty Estimated") + 1]
            .split("-")[0]
            .replace(",", "")
        )
        self.difficulty = {
            "curr_difficulty": curr_difficulty,
            "next_difficulty": next_difficulty,
        }

    def get_difficulty(self):
        return self.difficulty


class Miner:
    def __init__(
        self,
        name: str,
        hashrate: float,
        hashrate_units: str,
        cost: float,
        electrical_consumption: float,
    ) -> None:
        self.name = name
        self.hashrate = hashrate
        self.hashrate_units = hashrate_units
        self.cost = cost
        self.electrical_consumption = electrical_consumption
        self.hashrate_value = self.get_hashrate_value()
        self.params_dict = {}

    def get_params(self):
        self.params_dict = {
            "name": self.name,
            "hashrate": self.hashrate_value,
            "cost": self.cost,
            "electrical_consumption": self.electrical_consumption,
        }
        return self.params_dict

    def __str__(self) -> str:
        return self.name

    def get_hashrate_value(self):
        if self.hashrate_units == "kH":
            self.hashrate_value = self.hashrate * 10e3
        elif self.hashrate_units == "MH":
            self.hashrate_value = self.hashrate * 10e6
        elif self.hashrate_units == "GH":
            self.hashrate_value = self.hashrate * 10e9
        elif self.hashrate_units == "TH":
            self.hashrate_value = self.hashrate * 10e12
        elif self.hashrate_units == "PH":
            self.hashrate_value = self.hashrate * 10e15
        elif self.hashrate_units == "EH":
            self.hashrate_value = self.hashrate * 10e18
        elif self.hashrate_units == "ZH":
            self.hashrate_value = self.hashrate * 10e21
        else:
            self.hashrate_value = None
        return self.hashrate_value


class Mining:
    def __init__(self, miner, num_miners, uptime_factor, result):
        self.miner = miner
        self.num_miners = num_miners
        self.uptime_factor = uptime_factor
        self.electricity_cost_min = None
        self.electricity_cost_max = None
        self.electricity_cost_avg = None
        self.difficulty_increase_min_2wk = 0.01
        self.difficulty_increase_max_2wk = 0.05
        self.result = result
        self.mined_data = None
        self.difficulty_fetcher = Difficulty_Fetcher()

    def start_mining(self, from_date):
        mining_df = self.result.copy()
        mask = mining_df.index == datetime.datetime.strptime(from_date, "%Y-%m-%d")
        # mask = mining_df.index == from_date
        mining_df.DiffLast = mining_df.DiffLast.ffill()
        mining_df["diff_last_min"] = np.nan
        mining_df["diff_last_max"] = np.nan
        mining_df["diff_last_avg"] = np.nan

        row_from_date = np.where(mask)[0][0]

        self.difficulty_fetcher.fetch_difficulty()
        difficulty = self.difficulty_fetcher.get_difficulty()

        next_diff = difficulty.get("next_difficulty", None)
        assert next_diff is not None
        next_diffmin = next_diff
        next_diffmax = next_diff
        next_diffavg = next_diff
        for i in range(row_from_date, len(mining_df), 14):
            mining_df["diff_last_avg"].iloc[i] = next_diff
            next_diffmin = next_diff * (1 + self.difficulty_increase_min_2wk)
            next_diffmax = next_diff * (1 + self.difficulty_increase_max_2wk)
            next_diffavg = (next_diffmin + next_diffmax) / 2
            next_diff = next_diffavg
            mining_df["diff_last_min"].iloc[i] = next_diffmin
            mining_df["diff_last_max"].iloc[i] = next_diffmax
            mining_df["diff_last_avg"].iloc[i] = next_diffavg
        mining_df.diff_last_avg = mining_df.diff_last_avg.ffill()
        mining_df.diff_last_min = mining_df.diff_last_min.ffill()
        mining_df.diff_last_max = mining_df.diff_last_max.ffill()

        mined_df = mining_df.copy()
        mined_df = mined_df[
            mined_df.index >= datetime.datetime.strptime(from_date, "%Y-%m-%d")
        ]
        mined_df["daily_btc_mined_avg"] = (
            mined_df.Reward * self.num_miners * self.miner.hashrate_value * 86400
        ) / (mined_df.diff_last_max * (2**32))
        mined_df["btc_mined"] = mined_df["daily_btc_mined_avg"].cumsum()
        self.mined_data = mined_df

    def return_mined_data(self):
        return self.mined_data


if __name__ == "__main__":
    s19pro = Miner("s19 pro", 110, "TH", 11500, 3.250)
    print(s19pro)

    minerslist = [
        ["s19", 95, 9000, 3.250],
        ["s19j pro", 100, 10707, 3.050],
        ["s19 pro", 110, 11500, 3.250],
    ]
    hoursPerDay = 24
    uptime_factor = 1
    uptimeHours = uptime_factor * hoursPerDay
    uptimeSec = uptimeHours * 3600
    # max 30 cents, min 7 cents
    electricitycostmax = 0.3
    electricitycostmin = 0.07
    electricitycosttaken = 0.1
    miners = pd.DataFrame(
        minerslist, columns=["name", "hashrate", "cost", "consumption"]
    )
    miners["consumptionMax"] = miners.consumption * (1.05)
    miners["consumptionMin"] = miners.consumption * (0.95)
    miners["electricityCostTaken"] = (
        miners.consumption * uptimeHours * electricitycosttaken
    )
    miners["electricityCostMax"] = (
        miners.consumptionMax * uptimeHours * electricitycosttaken
    )
    miners["electricityCostMin"] = (
        miners.consumptionMin * uptimeHours * electricitycosttaken
    )
