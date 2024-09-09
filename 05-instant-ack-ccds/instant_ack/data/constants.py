akamai_as = [16625, 20940]
amazon_as = [14618, 16509]
cloudflare_as = [13335, 209242]
fastly_as = [54113]
google_as = [15169, 19527, 396982]
meta_as = [32934]
microsoft_as = [8075]

cdns = {
    "Akamai": akamai_as,
    "Amazon": amazon_as,
    "Cloudflare": cloudflare_as,
    "Fastly": fastly_as,
    "Google": google_as,
    "Meta": meta_as,
    "Microsoft": microsoft_as,
}

cdn_dict = {}
for key, val in cdns.items():
    for v in val:
        cdn_dict[v] = key
