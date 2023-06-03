import datetime

import numpy as np
import pandas as pd
from coinmetrics.api_client import CoinMetricsClient
from tqdm import tqdm

pd.options.mode.chained_assignment = None  # default='warn'
# init_notebook_mode(connected=True)
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

chart_studio.tools.set_credentials_file(username=username, api_key=api_key)
