import os
import pandas as pd


def load_csv_candles(symbol, interval, folder="scalping", limit=1440):
    # Caminho baseado na raiz do projeto
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    path = os.path.join(base_dir, "data", "historical", folder, interval)

    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ Caminho não encontrado: {path}")

    all_files = sorted(os.listdir(path))
    df_list = []

    for filename in all_files:
        if not filename.endswith(".csv"):
            continue
        file_path = os.path.join(path, filename)
        df = pd.read_csv(file_path, header=None)
        df.columns = [
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_asset_volume",
            "num_trades",
            "taker_buy_base",
            "taker_buy_quote",
            "ignore",
        ]
        df_list.append(df[["open_time", "open", "high", "low", "close", "volume"]])
        if sum(len(x) for x in df_list) >= limit:
            break

    df_all = pd.concat(df_list, ignore_index=True)
    df_all = df_all.head(limit)

    for col in ["open", "high", "low", "close", "volume"]:
        df_all[col] = pd.to_numeric(df_all[col], errors="coerce")

    df_all.dropna(inplace=True)

    return df_all.to_dict("records")
