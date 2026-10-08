from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
p=root/"Pages/PosPage.xaml.cs"
s=p.read_text(encoding="utf-8-sig")
if "using SweetsPOS.Services;" not in s:
    anchor="using SweetsPOS.Models;\n"
    if anchor not in s: raise SystemExit("PosPage using anchor missing")
    s=s.replace(anchor, anchor+"using SweetsPOS.Services;\n", 1)
p.write_text(s, encoding="utf-8-sig")
print("v3.0.1 PricingService namespace hotfix applied")
