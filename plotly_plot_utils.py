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

chart_studio.tools.set_credentials_file(username=username, api_key=api_key)


def plot(df, title, xlabel, ylabel, type="log"):
    for i, col in enumerate(df.columns):
        Printer.yellow(f"{i}:{col}")

    columns = str(input())
    columns = [x.strip() for x in columns.split(",")]

    traces = []
    for col in columns:
        trace = go.Scatter(
            x=df.index,
            y=df[df.columns[int(col)]],
            xaxis="x2",
            yaxis="y2",
            name=df.columns[int(col)],
            mode="lines",
        )
        traces.append(trace)
    fig = go.Figure()
    fig.add_traces(traces)
    # initialize xaxis2 and yaxis2
    fig["layout"]["xaxis2"] = {}
    fig["layout"]["yaxis2"] = {}
    # The graph's yaxis MUST BE anchored to the graph's xaxis
    fig.layout.yaxis2.update({"anchor": "x2"})
    fig.layout.yaxis2.update({"title": ylabel})
    fig.layout.xaxis2.update({"title": xlabel})
    # Update the margins to add a title and see graph x-labels.
    fig.update_layout(legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
    fig.update_layout(
        title={"text": title, "y": 0.9, "x": 0.5, "xanchor": "center", "yanchor": "top"}
    )
    fig.update_yaxes(type=type)
    fig.show()
