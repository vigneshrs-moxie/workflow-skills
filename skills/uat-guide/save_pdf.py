"""Write the PDF from a Claude Docs `export` result to a file.

Usage: python3 -I save_pdf.py <export result> <output.pdf>

The export result is the JSON the connector returns (or the file the client
saved it to when it was too large to show); its PDF is base64 in
data.bytes_b64.
"""
import base64
import json
import sys

if len(sys.argv) != 3:
    sys.exit("usage: save_pdf.py <export result> <output.pdf>")

with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)["data"]
if data.get("format") != "pdf":
    sys.exit(f"not a PDF export: format is {data.get('format')!r}")

pdf = base64.b64decode(data["bytes_b64"])
if len(pdf) != data["bytes"]:
    sys.exit(f"decoded {len(pdf)} bytes, expected {data['bytes']}")
with open(sys.argv[2], "wb") as f:
    f.write(pdf)
print(f"{sys.argv[2]}: {data.get('pages')} pages, {len(pdf)} bytes")
