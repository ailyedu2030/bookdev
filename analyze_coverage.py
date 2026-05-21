import json

with open("coverage.json") as f:
    data = json.load(f)

files = data.get("files", {})
results = []

for filepath, filedata in files.items():
    missing = filedata.get("missing_lines", [])
    executed = filedata.get("executed_lines", [])
    if "/src/" in filepath and "test_" not in filepath and missing:
        total = len(executed) + len(missing)
        results.append((filepath, len(missing), total, sorted(missing)[:20]))

results.sort(key=lambda x: -x[1])
for fp, miss, total, lines in results[:30]:
    fname = fp.replace("/Volumes/Coding/工商学院/bookdop/src/", "")[:70]
    print(fname)
    print("  Missing: %d/%d, Lines: %s" % (miss, total, lines))
