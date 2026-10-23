*This project has been created as part of the 42 curriculum by syokota, atajima.*

[English](README.md) | **日本語**

# A-Maze-ing

## 概要

設定ファイルを読んで迷路を作り、ファイルに書き出して、端末に表示する
プログラムです。

`PERFECT` の値で、2 種類の迷路を作れます。

* `PERFECT=True` なら完全迷路になります。入口から出口までの道は 1 本
  だけで、ループはありません。
* `PERFECT=False`（`config.txt` の設定）なら、Pac-Man のようなゲームで
  使える盤になります。どの通路にも行けて、四隅と中央は通路になって
  います。ループが 2 つ以上あり、行き止まりが残らないように壁を開けています。

どちらの場合も、迷路の中に（11×9 以上なら）閉じたセルで「42」を描き、入口から出口までの
最短経路も出力します。

迷路を作る部分は `mazegen/` というパッケージに分けてあり、
`mazegen-1.0.0-py3-none-any.whl` を `pip install` すれば別のプロジェクト
からも使えます。

## 実行方法

Python 3.10 以上が必要です。プログラム自体は標準ライブラリだけで動きます。
`make install` で入れるのは開発用のツール（flake8、mypy、pytest、build）
だけです。

```bash
# 開発用のツールを .venv に入れる
make install

# config.txt で迷路を作って表示する（python3 a_maze_ing.py config.txt と同じ）
make run

# 別の設定ファイルを使う
python3 a_maze_ing.py my_config.txt
make run CONFIG=my_config.txt

# デバッガ（pdb）で動かす
make debug

# flake8 と mypy（subject で指定されたオプション）
make lint
make lint-strict     # flake8 と mypy --strict

# テスト（tests/ は提出物に含めていないので、手元にあるときだけ動く）
make test

# wheel を作り直す（make install のあとで）
make build

# subject の maze_analyzer.py で迷路を確かめる
# （maze_analyzer.py を Makefile と同じ場所に置いておく）
make analyze

make clean     # キャッシュとビルドで出たファイルを消す
make fclean    # clean に加えて .venv と maze.txt も消す
make help      # ルールの一覧
```

### メニュー

迷路を表示したあと、標準入力と標準出力がどちらも端末ならメニューが出ます
（そうでなければ迷路を表示して終わります）。

```
=== A-Maze-ing ===
1. Re-generate a new maze
2. Show / Hide the shortest path
3. Rotate the wall colours
4. Quit
```

色は 256 色の ANSI コードで付けています。出力先がファイルやパイプの
ときや、端末が `██` を表示できないときは、色なしの文字で
描きます（壁 `##`、入口 `EE`、出口 `XX`、「42」`%%`、経路 `..`）。

## 設定ファイル

1 行に `KEY=VALUE` を 1 つ書きます。`#` で始まる行と空行は読み飛ばします。
`=` の前後の空白は無視し、キーの大文字・小文字は区別しません。決められて
いないキー、同じキーの重複、必須のキーの不足、書式の間違い、作れない迷路の
ときは、エラーメッセージを出して終了ステータス 1 で終わります。

### 必須のキー

| キー          | 内容                                 | 例                      |
| ------------- | ------------------------------------ | ----------------------- |
| `WIDTH`       | 迷路の幅（セル数、2 以上）           | `WIDTH=19`              |
| `HEIGHT`      | 迷路の高さ（セル数、2 以上）         | `HEIGHT=11`             |
| `ENTRY`       | 入口の座標 `x,y`                     | `ENTRY=0,0`             |
| `EXIT`        | 出口の座標 `x,y`（入口とは別のセル） | `EXIT=18,10`            |
| `OUTPUT_FILE` | 迷路を書き出すファイル               | `OUTPUT_FILE=maze.txt`  |
| `PERFECT`     | 完全迷路なら `True`、Pac-Man 用の盤なら `False` | `PERFECT=False` |

### 省略できるキー

| キー   | 省略したとき | 内容                                         |
| ------ | ------------ | -------------------------------------------- |
| `SEED` | ランダム     | 整数のシード。同じシードなら同じ迷路になる   |

`PERFECT` は `True` か `False` です（大文字・小文字は問いません）。迷路の
大きさは 1000×1000 までです。2×2 だとループが 1 つしか作れないので、
`PERFECT=False` で 2×2 の迷路は作れません。

`config.txt` はこうなっています。

```ini
WIDTH=19
HEIGHT=11
ENTRY=0,0
EXIT=18,10
OUTPUT_FILE=maze.txt
PERFECT=False
SEED=42
```

## 出力ファイル

1 セルを 16 進数 1 桁で、迷路の 1 行をファイルの 1 行に書きます。各桁の
4 ビットが、閉じている壁を表します。

| ビット  | 値 | 向き |
| ------- | -- | ---- |
| 0 (LSB) | 1  | 北   |
| 1       | 2  | 東   |
| 2       | 4  | 南   |
| 3       | 8  | 西   |

たとえば `3`（`0011`）は北と東が閉じていて、`A`（`1010`）は東と西が
閉じています。`F` は 4 方向とも閉じたセルで、「42」はこれで描かれます。

迷路の行のあとに空行を 1 行入れ、入口の座標、出口の座標、最短経路
（`N`、`E`、`S`、`W`）を 1 行ずつ書きます。どの行も `\n` で終わります。

```
9139395539113915553
AC46C439406C46A9552
...
C546C5556C6C5545556

0,0
18,10
EESENESENEEESENEEESENESSEEESSESSSSWSES
```

壁は `Grid.open_wall()` と `Grid.close_wall()` でしか書き換えず、この 2 つは
必ず隣のセルの壁も一緒に書き換えるので、隣どうしで壁の情報が食い違うことは
ありません。

## 迷路の作り方

### 使ったアルゴリズム

迷路は再帰的バックトラッカー（ランダムな深さ優先探索）で掘っています。
再帰ではなくスタックで書いているので、1000×1000 でも Python の再帰の
上限に引っかかりません。バックトラッカーで作られるのは通路セルの全域木で、
これがそのまま完全迷路になります。

迷路は次の 4 段階で作ります。

1. 「42」の配置。4×7 の字形を 2 文字並べて（全体で 9×7 セル）、入口・
   出口・四隅・中央にかからず、残りのセルがつながったままになる場所に
   置きます。「42」と外周の壁の間には 1 セルの通路を必ず残すので、迷路は
   11×9 以上必要です。それより小さいときや、入口と出口の位置のせいで
   置けないときは、「42」を描かずにエラーメッセージを出します。
2. 全域木の生成。「42」以外のすべてのセルをバックトラッカーで掘ります。
   木にはループがないので、壁のない 3×3 の区画（2×2 も）はできません。
3. 編み込み（`PERFECT=False` のときだけ）。行き止まり（開いた壁が 1 枚の
   セル）の壁をもう 1 枚開けることを、開けられなくなるまで繰り返します。
   それでもループが 2 つ未満なら、2 つになるまで壁を開けます（試した範囲
   では、2×3 や 12×2 のような、ごく小さいか細長い迷路だけでした）。開けると壁のない 3×3 の区画が
   できる壁は開けないので、通路の幅は 2 セルまでに収まります。
4. 最短経路の探索。幅優先探索で入口から出口までの最短経路を求めます。

### この方法にした理由

* バックトラッカーは長く曲がりくねった通路を作るので、迷路らしい見た目に
  なります。Prim や Kruskal も比べましたが、短い枝が多い迷路になりやすい
  です。バックトラッカーは仕組みも単純で、コードを追いやすいので、こちらに
  しました。
* バックトラッカーの処理時間は、セルの数に比例します。
* 全域木を作ってから編み込むので、2 つのモードを同じ流れで作れます。

### 要件を満たしているかの確認

`MazeGenerator.check()` で、作った迷路が subject の要件を満たしているかを
調べています。調べるのは、外周が閉じていること、隣どうしの壁が合って
いること、全体がつながっていること、「42」のセルが閉じていること、壁の
ない 3×3 の区画がないことです。完全迷路ならループがないこと、Pac-Man 用の
盤ならループが 2 つ以上あること、四隅と中央が開いていること、行き止まりが
2 つ以下であることも調べます。迷路を作るたびに実行して、問題があれば警告を出します。

### subject の maze_analyzer.py での確認

subject に付いている `maze_analyzer.py` でも確かめています。このファイルは
subject のものなのでリポジトリには入れていません。使うときは `Makefile` と
同じ場所に置いてください。

```bash
make analyze
# または
python3 maze_analyzer.py maze.txt
```

どちらのモードでも、期待どおりの判定になります。

```
# PERFECT=False
Verdict: Pac-Man-USABLE: fully connected, corners and centre reachable,
         21 independent routes; ...

# PERFECT=True
Verdict: PERFECT maze: a single path, no loop -> matches PERFECT=True ...
```

ここでの "independent routes" は、このプロジェクトでいう「ループ」の
数です。

手元のテスト（`tests/`）でも、いくつかの大きさとシードの迷路をこの
スクリプトで判定しています。subject に「テストは提出も採点もされない」と
あるので、テストはコミットしていません。

## 再利用できる部分

迷路を作る部分は [`mazegen/`](mazegen/) パッケージにまとめてあります。
標準ライブラリしか使っておらず、設定ファイルや表示の処理は入っていません。
wheel にしてリポジトリ直下に置いています。

* `mazegen-1.0.0-py3-none-any.whl`

wheel のビルド設定（[`pyproject.toml`](pyproject.toml)）もリポジトリに
入っているので、`make build` で作り直せます。

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install mazegen-1.0.0-py3-none-any.whl

# 上の行の代わりに、ソースから作り直してインストールする場合
# （wheel は dist/ にできる）
pip install build && python -m build --wheel
pip install dist/mazegen-1.0.0-py3-none-any.whl
```

[`a_maze_ing.py`](a_maze_ing.py) と [`amazeing/`](amazeing/)（設定、
出力ファイル、表示、メニュー）はこのプログラム用の部分で、パッケージには
入っていません。

パッケージの中では、セルと壁は `Grid` が管理していて、`generation/`
（作る）と `analysis/`（調べる）の関数がそれを使います。生成の流れは
`MazeGenerator.generate()` を見ると分かります。

### 迷路を作る

```python
from mazegen import MazeGenerator

gen = MazeGenerator(width=25, height=17, seed=42)
gen.generate()
```

### 引数を指定する

```python
gen = MazeGenerator(
    width=31,            # 列数（2〜1000）
    height=21,           # 行数（2〜1000）
    entry=(0, 0),        # 入口 (x, y)。省略すると (0, 0)
    exit=(30, 20),       # 出口 (x, y)。省略すると右下
    perfect=False,       # False（省略時）なら Pac-Man 用の盤
    seed=1234,           # 省略するとランダム。使った値は gen.seed_used
)
gen.generate()
```

`generate()` は自分自身を返すので、`MazeGenerator(...).generate()` のように
続けて書けます。`generate(seed=...)` で、別のシードで作り直すこともでき
ます。

大きさが範囲外のとき、入口や出口が迷路の外にあるとき、入口と出口が同じ
セルのとき、2×2 で Pac-Man 用の盤を作ろうとしたとき、型が違う値（`"20"` や
`[0, 0]` など）を渡したときは、`mazegen.MazeError` になります。

### 結果を読む

```python
from mazegen import EAST

gen.grid              # grid[y][x] が閉じている壁のビット（List[List[int]]）
gen.grid[4][3] & EAST # セル (3, 4) の東の壁が閉じていれば 0 以外

gen.pattern_cells     # 「42」のセルの集合
gen.pattern_warning   # 「42」を描けなかった理由（描けたら None）
gen.seed_used         # 使ったシード。これで同じ迷路を作り直せる

gen.solution          # 入口から出口までの最短経路 [(0, 0), (1, 0), ...]
gen.directions        # 同じ経路を文字で表したもの "EEESSEES..."

gen.to_hex_lines()    # 16 進数の行 ['915155...', ...]
gen.dead_ends()       # 行き止まりのセル
gen.loop_count()      # ループの数
gen.check()           # 要件を満たしていれば []
```

ゲームの盤に使うなら、たとえばこうなります。

```python
gen = MazeGenerator(19, 15, perfect=False, seed=7).generate()
board = [
    ["wall" if (x, y) in gen.pattern_cells else "corridor"
     for x in range(gen.width)]
    for y in range(gen.height)
]
```

この説明を短くしたものが、パッケージの docstring にもあります
（`pydoc mazegen` や `help(mazegen)` で読めます）。

## 参考にしたもの

* Jamis Buck, *Maze Generation Algorithms*（バックトラッカー、Prim、
  Kruskal の解説）
  <https://weblog.jamisbuck.org/2011/2/7/maze-generation-algorithm-recap>
* Jamis Buck, *Mazes for Programmers*, Pragmatic Bookshelf, 2015
  （braiding の章を、行き止まりをなくす処理の参考にしました）
* Walter D. Pullen, *Think Labyrinth: Maze Algorithms*（perfect、braided
  などの用語） <https://www.astrolog.org/labyrnth/algrithm.htm>
* Wikipedia: *Maze generation algorithm*、*Spanning tree*
  <https://en.wikipedia.org/wiki/Maze_generation_algorithm>、
  <https://en.wikipedia.org/wiki/Spanning_tree>
* Python のドキュメント:
  [`random`](https://docs.python.org/3/library/random.html)、
  [`typing`](https://docs.python.org/3/library/typing.html)、
  [PEP 257](https://peps.python.org/pep-0257/)、
  [Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
* [Choose a License](https://choosealicense.com/)（ライセンスを MIT に
  決めるときに読みました）
* ANSI エスケープコード（256 色）
  <https://en.wikipedia.org/wiki/ANSI_escape_code#8-bit>

### AI の使い方

AI（Claude）は次のことに使いました。

* アルゴリズムを選ぶときの、バックトラッカー、Prim、Kruskal の比較
* 設定ファイルの読み込み（`amazeing/config/`）、エラー処理、`Makefile`、
  `pyproject.toml` の下書き（読んで直してから使いました）
* 最初の 3×5 の字形だと「42」の中に行き止まりが残る原因の調査（そのあと
  4×7 の字形 `mazegen/generation/glyphs.py` に変えました）
* ファイルを役割ごとに分ける作業（`mazegen/`、`amazeing/`）と、コードと
  README の見直し

## ディレクトリ構成

```
.
├── a_maze_ing.py                     # メインのプログラム
├── mazegen/                          # 再利用できるパッケージ
│   ├── __init__.py                   # 公開しているものと docstring
│   ├── generator.py                  # MazeGenerator（生成の流れ）
│   ├── validation.py                 # 引数のチェック
│   ├── grid.py                       # Grid（セルと壁）
│   ├── constants.py                  # 壁のビット、向き、大きさの範囲など
│   ├── errors.py                     # MazeError
│   ├── generation/                   # 迷路を作る
│   │   ├── pattern.py                # 「42」の置き場所
│   │   ├── glyphs.py                 # 「42」の字形
│   │   ├── backtracker.py            # 再帰的バックトラッカー
│   │   └── braiding.py               # 行き止まりをなくす、ループを足す
│   └── analysis/                     # できた迷路を調べる
│       ├── routes.py                 # 最短経路、ループ、行き止まり
│       └── verify.py                 # 要件のチェック
├── mazegen-1.0.0-py3-none-any.whl    # パッケージ（wheel）
├── amazeing/                         # このプログラム用の部分
│   ├── output.py                     # 出力ファイルを書く
│   ├── config/                       # 設定ファイル
│   │   ├── settings.py               # load_config()
│   │   ├── reader.py                 # KEY=VALUE を読む
│   │   └── values.py                 # 値の変換
│   └── display/                      # 端末への表示
│       ├── canvas.py                 # どこに何を描くか
│       ├── themes.py                 # 配色
│       ├── render.py                 # 端末に出す文字列にする
│       ├── session.py                # 表示中の迷路と表示の設定
│       ├── menu.py                   # メニュー
│       └── terminal.py               # 端末かどうかの判定など
├── config.txt                        # 設定ファイルの例
├── pyproject.toml                    # パッケージのビルド設定
├── Makefile
├── .flake8                           # flake8 で .venv などを見ない設定
├── .gitignore
├── LICENSE.md                        # MIT ライセンス
├── README.md                         # 英語版
└── README.ja.md                      # 日本語版（このファイル）
```

テストと `maze_analyzer.py`（subject に付いているもの）はコミットして
いません。`.flake8` は、`make install` で作った `.venv` を `flake8 .` が
見ないようにするために置いています。

## チームとプロジェクト管理

### 役割

| メンバー  | 役割                                     |
| --------- | ---------------------------------------- |
| `atajima` | 生成アルゴリズムと再利用モジュール       |
| `syokota` | 設定の読み込み、出力ファイル、エラー処理 |

### 計画と実際の進み方

| 手順 | 計画                           | 実際どうなったか |
| ---- | ------------------------------ | ---------------- |
| 1    | 設定の読み込みとエラー処理     | 予定どおり最初に作った。大きさや入口・出口のチェックは、あとで `MazeGenerator` 側（`mazegen/validation.py`）に移した。 |
| 2    | 完全迷路と出力ファイル         | バックトラッカーで作った。 |
| 3    | 「42」                         | 予定より時間がかかった。3×5 の字形では行き止まりが残ったので、4×7 に変えた。 |
| 4    | Pac-Man 用の盤（編み込み）     | 予定どおり完全迷路のあとに作った。3×3 の区画ができないようにする処理と、ループを 2 つ以上にする処理を入れた。 |
| 5    | 端末の表示とメニュー           | 予定どおり作った。 |
| 6    | パッケージ、README、ライセンス | 表示とメニューのあとに wheel、ライセンス、README を用意した。そのあと、ファイルを役割ごとに分け、もう一度全体を見直した。 |

### よかったこと、直したいこと

よかったこと:

* 最初から `mazegen` を表示や設定から切り離していたので、パッケージに
  するのも、単体で試すのも簡単でした。
* `check()` を早めに書いたので、生成のたびに subject の要件を確認でき
  ました。ランダムなシードで試したことで、「42」の字形が原因の行き止まり
  にも気づけました。
* subject の `maze_analyzer.py` をテストに入れたので、Pac-Man 用の盤の
  条件で迷うことがありませんでした。

直したいこと:

* 編み込みでは、開いた壁の少ない隣への壁を優先して開けるだけで、あとは
  ランダムに選んでいます。もっと工夫すれば、Pac-Man らしい盤にできると
  思います。

### 使ったツール

* Git
* make（install、run、debug、lint、test、build をまとめるため）
* flake8、mypy（`--strict` でも通ります）
* pytest
* build、setuptools（wheel を作るため）
* subject の `maze_analyzer.py`
