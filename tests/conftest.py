"""pytest の設定。リポジトリのフォルダを import の検索先に加える。

これで PYTHONPATH=. を付けずに、`pytest tests` だけでテストを実行できる。
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
