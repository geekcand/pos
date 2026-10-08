from pathlib import Path
import gzip, sys

gz_path = Path(sys.argv[1]).resolve()
out_path = Path(sys.argv[2]).resolve()
script = gzip.decompress(gz_path.read_bytes()).decode("utf-8")
script = script.replace("root=Path('/mnt/data/v301src')", "import sys\nroot=Path(sys.argv[1]).resolve()")
out_path.write_text(script, encoding="utf-8")
