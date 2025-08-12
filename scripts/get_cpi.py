import os
import datetime as dt
import pandas as pd
import requests
import janitor
from lib.save_data import save_data
from lib.helpers import plot_time_series

def main():
    api_key = get_api_key('lib/api_key.txt')
    series_map = get_series(series=["cpiu", "core", "core_ex_shelter", "core_ex_shelter_used_cars", "core_services", "core_goods", "food", "energy", "shelter"])
    df = fetch_cpi(api_key, series=series_map)
    df_annualized_rates = get_annualized_rates(df)
    save_data(
        df_annualized_rates,
        keys = ["year", "month", "date", "latest"],
        out_file = "output/data/cpi.csv",
        log_file = "output/logs/cpi.log",
        append = False,
        sortbykey = False
    )

def get_api_key(path):
    with open(path, 'r') as file:
        return file.read().strip()

def get_series(series=None, seasonal_adjustment=True):
    with open("lib/series_config.json", "r") as file:
        series_config = pd.read_json(file)
    d = series_config["sa"] if seasonal_adjustment else series_config["nsa"]
    if series:
        return {s: d[s] for s in series}
    return d.to_dict()

def fetch_cpi(api_key, start_date=None, end_date=None, series={"cpiu": "CUSR0000SA0"}):
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    today = dt.date.today()
    end_date = end_date or f"{today.year}-{today.month:02d}"
    start_date = start_date or f"{int(end_date[:4]) - 3}-{end_date[5:]}"
    start_year, start_month = map(int, start_date.split("-"))
    end_year, end_month = map(int, end_date.split("-"))
    params = {
        "seriesid": list(series.values()),
        "startyear": str(start_year),
        "endyear": str(end_year),
        "registrationKey": api_key
    }    
    response = requests.post(url, json=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    if data.get("status") != "REQUEST_SUCCEEDED":
        raise RuntimeError(f"BLS API error: {data}")
    
    df = process_payload(data, series)
    return df

def process_payload(data, series):
    df_list = []
    for s in data["Results"]["series"]:
        series_id = s["seriesID"]
        series_name = [k for k, v in series.items() if v == series_id][0]
        df_series = pd.DataFrame(s["data"])
        if df_series.empty:
            print(f"Empty data for series {series_name} ({series_id})")
            continue
    
        df_series_clean = (
            df_series
            .clean_names()
            .assign(series_name = series_name)
            .assign(year = lambda x: pd.to_numeric(x["year"]))
            .assign(month = lambda x: x["periodname"].str[:3])
            .assign(period = lambda x: pd.to_numeric(x["period"].str.replace("M", "")))
            .assign(date = lambda x: pd.to_datetime(x["year"].astype(str) + "-" + x["period"].astype(str).str.zfill(2) + "-01"))
            .assign(latest = lambda x: x["latest"].replace("true", "1").fillna("0").astype(int))
            .assign(value = lambda x: pd.to_numeric(x["value"]))
            .select(columns=["series_name", "year", "month", "date", "value", "latest"])
        )
        df_list.append(df_series_clean)
    df = pd.concat(df_list)
    df_clean = (
        df
        .pivot(index=["year", "month", "date", "latest"], columns="series_name", values="value")
        .rename_axis(None, axis=1)
        .reset_index()
        .sort_values(by=["date"], ascending=False)
    )
    return df_clean

def get_annualized_rates(df, levels=(1, 3, 6, 12)):
    columns = [c for c in df.columns if c not in ["year", "month", "date", "latest"]]
    df_annualized_rates = df.sort_values(by=["date"], ascending=True)
    for col in columns:
        base = df_annualized_rates[col]
        for k in levels:
            ratio = base / base.shift(k)
            ann = ratio.pow(12.0 / k) - 1.0
            df_annualized_rates[f"{col}_{k}m"] = ann * 100

    return df_annualized_rates
    
if __name__ == "__main__":
    main()