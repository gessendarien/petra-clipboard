import urllib.request, json
req = urllib.request.urlopen("https://pypi.org/pypi/PyQt6/6.7.1/json")
data = json.loads(req.read())
for url in data["urls"]:
    fname = url["filename"]
    if "manylinux" in fname and ("x86_64" in fname or "aarch64" in fname) and "cp3" in fname:
        print(f"{fname} | {url['url']} | {url['digests']['sha256']}")
