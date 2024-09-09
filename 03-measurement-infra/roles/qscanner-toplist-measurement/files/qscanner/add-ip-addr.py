import pandas as pd
import sys
import socket

targets = pd.read_csv(sys.argv[1]).drop(columns=["ip"])
targets["ip"] = socket.gethostbyname("cloudflare.com")

targets[["ip", "sni", "port", "scid"]].dropna(subset="ip").to_csv(
    sys.argv[2], index=False
)
