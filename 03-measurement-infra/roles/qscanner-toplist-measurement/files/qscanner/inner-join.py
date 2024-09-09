import pandas as pd
import sys

targ = pd.read_csv(sys.argv[2]).drop(columns=["ip"])
res = pd.read_csv(sys.argv[1], names=["ip", "sni"]).drop_duplicates("sni")

targets = targ.merge(res, how="inner", validate="1:1", on="sni")
targets["port"] = targets["port"].astype("Int64")

targets[["ip", "sni", "port", "scid"]].dropna(subset="ip").to_csv(
    sys.argv[3], index=False
)
