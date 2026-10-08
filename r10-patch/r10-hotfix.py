from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
p=root/"Pages/PosPage.xaml.cs"
s=p.read_text(encoding="utf-8-sig")
old="        CategoriesPanel.IsEnabled = !locked;"
new="        CategoriesPanel.IsHitTestVisible = !locked;\n        CategoriesPanel.Opacity = locked ? 0.65 : 1.0;"
if old not in s: raise SystemExit("R10 hotfix anchor missing")
p.write_text(s.replace(old,new,1),encoding="utf-8-sig")
print("R10 WinUI StackPanel hotfix applied")
