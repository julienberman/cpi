import pandas as pd
import matplotlib.pyplot as plt

def plot_time_series(df, value_cols, date_col="date", title=None, ylabel=None, xlabel=None, start=None, end=None):
    if start:
        df = df.query(f"{date_col} >= @start")
    if end:
        df = df.query(f"{date_col} <= @end")
    
    if date_col in df.columns:
        dates = df[date_col]
    elif df.index.name == date_col:
        dates = df.index
    else:
        raise KeyError(f"'{date_col}' not found in columns or index.")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    for value_col in value_cols:
        ax.plot(dates, df[value_col], label=f"{value_col}", marker='o', alpha=0.8)
    ax.set_xlabel(xlabel if xlabel else 'Date')
    ax.set_ylabel(ylabel if ylabel else 'Value')
    ax.set_title(title if title else None)
    ax.set_ylim(bottom=0, top = df[value_cols].max().max() * 1.1)
    ax.grid(True)
    
    ax.tick_params(axis='x', rotation=45)
    ax.xaxis.set_major_locator(plt.MaxNLocator(10))
    
    fig.legend(loc = 'upper center', bbox_to_anchor = (0.5, -0.01), ncol = 3, fancybox = True, shadow = True)

    plt.tight_layout()
    plt.show()
