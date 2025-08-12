import os
import datetime as dt
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

import requests
import janitor
import re
from lib.save_data import save_data

def main():
    df = pd.read_csv("output/data/cpi.csv")
    standard_table(df)
    standard_plot(df, col="overall", levels=[1, 3], title="CPI Inflation, Overall")
    standard_plot(df, col="core", levels=[1, 3], title="CPI Inflation, Core")
    standard_plot(df, col="shelter", levels=[1, 3], title="CPI Inflation, Shelter")

def standard_table(df, cols=["overall", "core", "core_ex_shelter", "core_ex_shelter_used_cars", "core_goods", "core_services" ], levels=(1, 3, 6, 12), date=None):
    date = pd.to_datetime(date) if date else df["date"].max()
    print(f"CPI report for {date}")
    df_filtered = df.query("date == @date")
    dfs = []
    for level in levels:
        column_list = [f"{col}_{level}m" for col in cols]
        df = (
            df_filtered
            .select(columns=column_list)
            .melt(var_name="series", value_name=f"{level}-month")
            .assign(
                series = lambda x: x["series"].str.replace(f"_{level}m", ""),
                **{f"{level}-month": lambda x: round(x[f"{level}-month"], 1)}
            )
        )
        dfs.append(df)
    
    df_final = dfs[0]
    for df in dfs[1:]:
        df_final = df_final.merge(df, on="series", how="left")
    
    print(df_final.head(10))
    return df_final

def standard_plot(df, col="core", levels=[1, 3], title="CPI Inflation, Core", color_map={1: "lightblue", 3: "firebrick", 6: "purple", 12: "darkgreen"}):
    
    fig, ax = plt.subplots(figsize=(8, 6))
    dates = df["date"]
    labels = [f"{m}, {y}" for m, y in zip(df["month"], df["year"])]
    min_val = 0
    max_val = 10
    for level in levels:
        series_name = f"{col}_{level}m"
        color = color_map.get(level)
        if level == 1:
            ax.bar(dates, df[series_name], label=f"{level}-month change", alpha=0.5, color=color)
        else:
            ax.plot(dates, df[series_name], label=f"{level}-month change", marker='o', alpha=0.8, color=color)
        
        min_val = min(min_val, df[series_name].min() * 1.1)
        max_val = max(max_val, df[series_name].max() * 1.1)

    title_y = 1.08
    subtitle_y = 1.02

    ax.text(0, title_y, title, transform=ax.transAxes, ha="left", va="bottom", fontsize=16, fontweight="bold")
    ax.text(0, subtitle_y, "Percent change, annual rate", transform=ax.transAxes, ha="left", va="bottom",fontsize=12, fontweight="normal")

    ax.set_ylim(bottom=min_val, top=max_val)
    ax.yaxis.grid(True, color="gray", linestyle="--", alpha=0.3)
    ax.xaxis.grid(False)
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)
    
    ax.set_xticks(dates)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=12)
    ax.xaxis.set_major_locator(plt.MaxNLocator(10))
    
    ax.tick_params(axis="y", labelsize=12)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    
    ax.legend(loc='upper right', ncol=3, fancybox=True, shadow=True, frameon=True)
    fig.text(0.01, 0.01, "Source: Bureau of Labor Statistics; Julien Berman's calculations.", ha="left", va="bottom", fontsize=12)
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    
    outfile = re.sub(r"[.,-]", "", title.lower().replace(' ', '_'))
    plt.savefig(f"output/figures/{outfile}.png", dpi=300, bbox_inches='tight')
    plt.close()
    
if __name__ == "__main__":
    main()