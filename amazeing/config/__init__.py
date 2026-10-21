"""設定ファイルの読み込み。

外からは load_config() と、その結果の MazeConfig、エラーの ConfigError
を使う。

reader.py    ファイルを読み、KEY=VALUE の組を文字列のまま取り出す
values.py    値を整数・真偽値・座標などに変換する
settings.py  両者を組み合わせ、必須キーがそろっているかを確かめて
                 MazeConfig を作る
"""

from amazeing.config.reader import ConfigError
from amazeing.config.settings import MazeConfig, load_config

__all__ = ["ConfigError", "MazeConfig", "load_config"]
