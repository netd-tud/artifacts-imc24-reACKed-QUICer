import sys

with open(sys.argv[1], "r") as file:
    with open(sys.argv[2], "w") as out:
        print("ip,sni,port,scid", file=out)
        lines = file.readlines()
        for i, line in enumerate(lines):
            print(f"0.0.0.0,{line.strip().split(',')[1]},443,{i:016x}", file=out)
