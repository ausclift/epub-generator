from pathlib import Path

class Paths:
    
    
  ROOT = Path("EPUB")
  META = ROOT / "META-INF"
  OEBPS = ROOT / "OEBPS"
  MIM = ROOT / "mimetype"
  IMAGES = OEBPS / "images"
  HTML = OEBPS / "html"