import pandas as pd


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

    def get_params(self):
        return [self.name, self.hashrate, self.cost, self.electrical_consumption]

    def __str__(self) -> str:
        return self.name


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
miners = pd.DataFrame(minerslist, columns=["name", "hashrate", "cost", "consumption"])
miners["consumptionMax"] = miners.consumption * (1.05)
miners["consumptionMin"] = miners.consumption * (0.95)
miners["electricityCostTaken"] = miners.consumption * uptimeHours * electricitycosttaken
miners["electricityCostMax"] = (
    miners.consumptionMax * uptimeHours * electricitycosttaken
)
miners["electricityCostMin"] = (
    miners.consumptionMin * uptimeHours * electricitycosttaken
)
