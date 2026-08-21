*This project has been created as part of the 42 curriculum by syokota, atajima.*

[English](README.md) | **日本語**

> **提出前の TODO:** 上の 1 行目の `<login1>`（チームで取り組んだ場合は
> `, <login2>, <login3>` も）を実際の 42 のログイン名に置き換え、末尾の
> *チームとプロジェクト管理* の節を自分たちの回答で埋めること。

# A-Maze-ing

## 概要

**A-Maze-ing** は、プレーンテキストの設定ファイルから迷路を生成し、
壁をコンパクトな 16 進数で符号化してディスクに書き出し、さらに端末上で
色付き・対話メニュー付きで表示するプログラムです。

同じ格子から、性格の異なる 2 種類の迷路を作れます。

* `PERFECT=True` — **完全迷路**。入口と出口の間の経路がちょうど 1 本
  だけで、ループはどこにもありません。教科書どおりの迷路です。
* `PERFECT=False`（既定）— **遊べる Pac-Man 盤**。すべての通路に到達
  でき、四隅と中央が開いていて、独立した経路が多数あり、**行き止まりが
  1 つもない**ため、追われているプレイヤーが袋小路に陥りません。

どちらのモードでも、完全に閉じたセルを使って大きな **「42」** を迷路の
中に描き、入口から出口への最短経路を計算して出力します。

生成ロジックそのものは独立した 1 つのモジュール
[`mazegen.py`](mazegen.py) にまとまっており、
`mazegen-1.0.0-py3-none-any.whl` としてパッケージ化されています。後続の
プロジェクト（たとえば Pac-Man 風のゲーム）は `pip install` するだけで
再利用できます。

## 実行方法

必要環境: **Python 3.10 以降**。プログラム自体に**実行時の依存関係は
ありません** — インストールが必要なのは開発ツール（flake8、mypy、
pytest、build）だけです。

```bash
# 開発ツールをローカルの仮想環境 (.venv) に入れる
make install

# config.txt を使って迷路を生成・保存・表示する
make run
# ... これは次と同じ:
python3 a_maze_ing.py config.txt

# 別の設定ファイルを使う
python3 a_maze_ing.py my_config.txt
make run CONFIG=my_config.txt

# Python デバッガ上で実行する
make debug

# subject が要求するフラグ付きの flake8 + mypy
make lint
make lint-strict     # flake8 + mypy --strict

# ユニットテスト（テストは手元で開発するもので、subject の言うとおり
# 提出物には含めない）
make test

# pip パッケージを再ビルドし、リポジトリ直下のものを更新する
make build

# 迷路を生成し、subject の解析スクリプトで検査する
# (subject に付属する maze_analyzer.py を Makefile の隣に置くこと)
make analyze

# 任意: グラフィカル表示用の MiniLibX ラッパーを入れる (Linux)
# (subject に付属する mlx-2.2.tgz を Makefile の隣に置くこと)
make install-mlx

# キャッシュとビルド生成物、さらに venv と maze.txt も消す
make clean
make fclean
```

### 表示方法

描画は 2 種類あり、設定ファイルの `DISPLAY` キーで選びます。

* `DISPLAY=terminal`（既定）— 端末上での ANSI カラー描画。番号付きの
  メニューが付きます。
* `DISPLAY=mlx` — キーボードで操作する **MiniLibX ウィンドウ**。

MiniLibX は *任意機能* であり、プロジェクトの依存関係ではありません。
`mlx` パッケージがない場合や、利用できるディスプレイがない場合は、警告を
表示したうえで端末描画に切り替わります。そのせいで失敗することは
ありません。

```bash
# subject に付属する mlx-2.2.tgz をリポジトリ直下に置いた状態で
make install-mlx     # 展開し、環境に合った wheel をインストールする
# そのうえで config.txt に DISPLAY=mlx を設定する
```

`mlx-2.2.tgz` に入っているのは Linux 用 wheel だけ（`fedora/` と
`ubuntu/`）なので、ウィンドウ表示が動くのは学校のクラスタ上です。macOS
ではフォールバックが働きます。このアーカイブはリポジトリに含めていま
せん。私たちのものではなく、subject に付属するものだからです。

ウィンドウ内の操作: `1` 再生成、`2` 経路の表示/非表示、`3` 壁の配色を
切り替え、`4` 「42」の配色を切り替え、`5` 保存、`6`/`Esc` 終了。迷路
全体は 1 枚の MiniLibX 画像に描いてから 1 回の呼び出しで転送しており、
配色テーマは端末描画と共有しています（xterm‑256 のパレットを RGB に
変換しています）。

### 対話メニュー

`DISPLAY=terminal` のとき、標準入力が端末であれば、迷路を表示したあとに
メニューが出ます。

```
=== A-Maze-ing ===
1. Re-generate a new maze
2. Show / Hide the shortest path
3. Rotate the wall colours
4. Toggle the "42" colours
5. Save the maze to the output file
6. Quit
```

色は 256 色の ANSI コードです。出力をリダイレクトしたとき、環境変数
`NO_COLOR` が設定されているとき、設定ファイルに `COLOR=False` があるとき
は自動的に無効になり、素の ASCII 描画（壁 `##`、入口 `EE`、出口 `XX`、
「42」は `%%`、経路は `..`）に切り替わります。

## 設定ファイル

1 行につき `KEY=VALUE` を 1 組。`#` で始まる行と空行は無視し、`=` の
前後の空白は取り除き、キーは大文字小文字を区別しません。未知のキー、
重複したキー、書式の壊れた行、実現不可能な迷路は、いずれも分かりやすい
エラーメッセージと終了ステータス `1` になります。不正な入力でプログラム
が異常終了することはありません。

### 必須キー

| キー          | 説明                                       | 例                      |
| ------------- | ------------------------------------------ | ----------------------- |
| `WIDTH`       | 迷路の幅（セル数、2 以上）                 | `WIDTH=25`              |
| `HEIGHT`      | 迷路の高さ（セル数、2 以上）               | `HEIGHT=17`             |
| `ENTRY`       | 入口の座標 `x,y`                           | `ENTRY=0,0`             |
| `EXIT`        | 出口の座標 `x,y`（入口とは別のセル）       | `EXIT=24,16`            |
| `OUTPUT_FILE` | 生成した迷路を書き出すファイル             | `OUTPUT_FILE=maze.txt`  |
| `PERFECT`     | 完全迷路なら `True`、遊べる盤なら `False`  | `PERFECT=False`         |

### 任意キー

| キー        | 既定値         | 説明                                            |
| ----------- | -------------- | ----------------------------------------------- |
| `SEED`      | ランダム       | 整数のシード。同じシードなら常に同じ迷路になる  |
| `ALGORITHM` | `backtracker`  | `backtracker`、`prim`、`kruskal` のいずれか     |
| `PATTERN`   | `True`         | 「42」のパターンを描く                          |
| `COLOR`     | `True`         | 端末描画で ANSI カラーを許可する                |
| `DISPLAY`   | `terminal`     | `terminal` または `mlx`（MiniLibX ウィンドウ）  |

真偽値は `True`/`False`、`yes`/`no`、`on`/`off`、`1`/`0` を受け付けます。

既定のファイルは [`config.txt`](config.txt) です。

```ini
WIDTH=25
HEIGHT=17
ENTRY=0,0
EXIT=24,16
OUTPUT_FILE=maze.txt
PERFECT=False
SEED=42
ALGORITHM=backtracker
PATTERN=True
COLOR=True
DISPLAY=terminal
```

## 出力ファイルの形式

1 セルにつき 16 進数 1 桁、1 行につき格子の 1 行。各桁はそのセルの
**閉じた** 壁のビットマスクです。

| ビット    | 値    | 方向 |
| --------- | ----- | ---- |
| 0 (LSB)   | 1     | 北   |
| 1         | 2     | 東   |
| 2         | 4     | 南   |
| 3         | 8     | 西   |

したがって `3`（`0011`）は北と東が閉じ、南と西が開いていることを表し、
`a`（`1010`）は東と西が閉じていることを表します。`f` はセルが完全に
閉じていることを表し、「42」のパターンはこの形で保存されます。

各行のあとに空行が 1 つ入り、さらに 3 行が続きます。入口の座標、出口の
座標、そして `N`、`E`、`S`、`W` の文字で表した最短経路です。すべての行は
`\n` で終わります。

```
9155551395515555555555393
ac3ff96c2ff83ffffffff946a
...
c555455556c46c456c46c5556

0,0
24,16
EEEEEEESENEEESESSEESSSWWSWSESSSSSSSESENEEESENEESEEEE
```

隣り合うセルは、共有する壁について常に一致します。壁の変更は必ず両側を
同時に書き込む 1 つの非公開ヘルパーだけを通すので、矛盾したデータは構造
上ありえません。

## 迷路の生成アルゴリズム

### どれを選んだか

既定のアルゴリズムは **ランダム化した深さ優先探索**、いわゆる
**再帰的バックトラッカー**です。明示的なスタックを使って反復的に実装
しているので、1000×1000 の迷路でも Python の再帰上限に達しません。
`ALGORITHM` キーで **ランダム化 Prim** と **ランダム化 Kruskal** も
選べます。3 つとも通路セルの *全域木* を作るもので、それはまさに完全
迷路の定義そのものです。

生成は 4 段階で進みます。

1. **「42」を配置する。** 数字は 4×7 のビットマップフォントから描き、
   格子が許す限り大きく拡大します（セル全体の 30 % を超えない、外周に
   触れない、入口・出口・四隅・中央を覆わない）。選んだ配置は、残りの
   セルすべてが連結したままであることを満たす必要があります。これらの
   セルは `f`（完全に閉じた状態）のまま残り、迷路はその *周りを* 掘って
   作られます。迷路が小さすぎてパターンが入らない場合は描画を諦め、
   コンソールにメッセージを出します。
2. **全域木を掘る。** 選ばれたアルゴリズムで、パターン以外のすべての
   セルに全域木を掘ります。この時点で迷路は完全迷路であり、
   `PERFECT=True` ならここで終わりです。
3. **編み込む**（`PERFECT=False` のときだけ）。開いた壁が 1 枚しかない
   セルがある限り、その壁をもう 1 枚開けます。壁を開けるのは 3×3 の
   完全な開放区画ができない場合だけなので、通路の幅が 2 セルを超える
   ことはありません。これによって **すべての** 行き止まりが消えます。
   これは subject がボーナスとして求めているものです。
4. **少なくとも 2 つのループを保証**し、幅優先探索で迷路を **解き**
   ます。幅優先探索なので、得られる経路は本当に *最短* です。

### なぜこれを選んだか

* 再帰的バックトラッカーは分岐が少なく **長く曲がりくねった通路** を
  作るので、見て楽しく、解くのも本当に難しい迷路になります。Prim や
  Kruskal は短く枝分かれの多い形になりがちです。また 3 つの中で最も
  動きを追いやすく、これは評価で自分のコードを説明しなければならない
  ときに効いてきます。
* 時間・メモリともに **セル数に対して O(n)** で、任意のグラフ上で動く
  ので、「42 のパターン以外のすべてのセル」に対象を限っても何のコストも
  かかりません。パターンのセルは単に有効な隣接セルにならないだけです。
* 先に全域木を作ってから編み込むことで、**1 本のコードパスから必要な
  2 つのモード**が得られます。完全迷路は、遊べる盤のちょうど中間状態に
  なっているわけです。

代償として、素のバックトラッカー迷路は行き止まりが *非常に* 多くなり
ます。だからこそ Pac-Man モードでは編み込みの段階が重要になります。
Prim と Kruskal を残したのは、編み込んだときに少し違う見た目の盤が
できることと、それらを比べることが「検証コードがアルゴリズムに依存して
いない」ことの確認になるからです。

### 正しさ

`MazeGenerator.check()` は、生成した迷路を subject のあらゆる要件に照ら
して再検証します。外周が閉じていること、共有する壁が整合していること、
完全に連結していること、パターンのセルが完全に閉じていること、3×3 の
開放区画がないこと、完全迷路ならループがないこと、遊べる盤ならループが
あり四隅と中央が開いていて行き止まりがないこと。プログラムは生成のたび
にこれを実行し、問題があれば警告として表示します。テストではさらに
**出力ファイル**を読み直し、生成器の内部を使わずに一から検査し直します。

### subject の解析スクリプトによる検査

subject に付属する `maze_analyzer.py` は参照実装のオラクルです。出力
ファイルを読み直し、壁の整合性と、迷路が *perfect* なのか *playable* な
盤なのかを報告します。私たちのものではなく subject に付属するものなので、
リポジトリには含めていません。使うときは `Makefile` の隣に置いてくだ
さい。

```bash
make analyze
# あるいは直接、いちばん厳しいしきい値で（行き止まりゼロのボーナス）:
python3 maze_analyzer.py maze.txt --max-dead-ends 0
```

どちらのモードでも、可能な限り最良の判定になります。

```
# PERFECT=False
Dead-ends        : 0 real + 0 enclosed by the '42' (tolerated)
Corners + centre : all reachable
Wall coherence   : OK (all shared walls match)
Verdict: Pac-Man-USABLE: fully connected, corners and centre reachable,
         33 independent routes; no real dead-end -> bonus-grade
         (perfectly braided).

# PERFECT=True
Verdict: PERFECT maze: a single path, no loop -> matches PERFECT=True
```

この解析スクリプトは手元のテストにも組み込んでいます。大きさ・シード・
アルゴリズムの異なる迷路を何十個も生成し、`--min-loops 2
--max-dead-ends 0` を付けたうえでこれらの判定に達することを要求して
います。このテスト一式はコミットしていません（subject がテストプログラム
は「提出も採点もされない」と述べているためです）が、`tests/` ディレクトリ
があれば `make test` で実行できます。

## 何がどう再利用できるか

迷路生成に必要なものはすべて、**独立した 1 つのモジュール**
[`mazegen.py`](mazegen.py) に入っています。標準ライブラリ以外への
**依存はなく**、設定ファイルや端末や色のことは何も知りません。これは
リポジトリ直下で pip パッケージとして公開しています。

* `mazegen-1.0.0-py3-none-any.whl`

再ビルドに必要なものはすべてリポジトリに揃っています
（[`pyproject.toml`](pyproject.toml)）。`make build` で両方を作り直せます。

```bash
python3 -m venv venv && source venv/bin/activate
pip install mazegen-1.0.0-py3-none-any.whl
# あるいはソースから:
pip install build && python -m build
```

残りのコード — [`a_maze_ing.py`](a_maze_ing.py) と
[`amazeing/`](amazeing/) パッケージ（設定、出力ファイル、描画、メニュー）
— はアプリケーション層であり、パッケージには *含まれません*。

### 生成器を作って使う

```python
from mazegen import MazeGenerator

gen = MazeGenerator(width=25, height=17, seed=42)
gen.generate()
```

### パラメータを指定する

```python
gen = MazeGenerator(
    width=31,            # 列数、2 以上
    height=21,           # 行数、2 以上
    entry=(0, 0),        # (x, y)、迷路の内側であること
    exit=(30, 20),       # (x, y)、入口とは別のセル
    perfect=False,       # False -> 編み込んだ、遊べる盤
    seed=1234,           # None -> ランダム。ただし必ず記録される
    algorithm="prim",    # "backtracker"、"prim"、"kruskal"
    pattern=True,        # 「42」を描く
    pattern_text="42",   # 何を描くか
)
gen.generate()
```

不正な組み合わせを渡すと、明示的なメッセージ付きで
`mazegen.MazeError` が送出されます。

### 生成された構造と解にアクセスする

```python
from mazegen import EAST, NORTH, SOUTH, WEST

gen.grid              # List[List[int]]、grid[y][x] = 閉じた壁のビットマスク
gen.walls_at(3, 4)    # 同じ値をメソッド経由で読む
gen.is_open(3, 4, EAST)          # 東へ進めるなら True
list(gen.open_neighbours(3, 4))  # 1 歩で行けるセル
gen.degree(3, 4)                 # 開いている壁の枚数

gen.pattern_cells     # Set[(x, y)] -- 完全に閉じた「42」のセル
gen.pattern_warning   # 「42」を諦めた理由。描けていれば None
gen.seed_used         # このシードを使えば同じ迷路を再現できる

gen.solution          # [(0, 0), (1, 0), ...] 入口 -> 出口の最短経路
gen.directions        # 同じ経路を "ESSEEN..." の文字で表したもの
gen.solve((3, 3), (7, 9))        # 任意の 2 セル間の最短経路

gen.to_hex_lines()    # ['9155...', ...] 1 セル 16 進数 1 桁
gen.dead_ends()       # 開いた壁が 1 枚しかないセル
gen.loop_count()      # 独立した経路の数
gen.check()           # すべての要件を満たしていれば []
```

ゲーム盤への最小限の組み込み例:

```python
gen = MazeGenerator(19, 15, perfect=False, seed=7).generate()
board = [
    ["wall" if (x, y) in gen.pattern_cells else "corridor"
     for x in range(gen.width)]
    for y in range(gen.height)
]
```

完全なドキュメントはモジュールの docstring そのものなので、パッケージを
インストールしたあとは `pydoc mazegen` や `help(mazegen)` で読めます。
docstring には英語版と日本語版の両方が入っています。

## 発展的な機能

* **3 つの生成アルゴリズム** — 再帰的バックトラッカー、ランダム化 Prim、
  ランダム化 Kruskal。`ALGORITHM` キーで選択します。
* **行き止まりゼロの編み込み盤** — subject が求めるボーナス。
  `PERFECT=False` モードでは、通路の幅を最大 2 セルに保ったまま、生成器
  が *すべての* 行き止まりを取り除きます。
* **拡大縮小する「42」パターン** — 数字はビットマップフォントから描き、
  格子が収められる最大の大きさへ自動的に拡大します。
* **2 つの表示方法** — ANSI の端末描画と、任意機能の **MiniLibX**
  ウィンドウ。同じキャンバスと同じ配色テーマを共有しています。
* **5 つの配色テーマ** をメニューから実行中に切り替えられます。「42」の
  配色は別途切り替えられ、素の ASCII への自動フォールバックもあります。
* **自己検証** — `check()` が生成のたびに subject のすべての規則を
  検査します。
* **再現性** — シードを指定せずに生成した迷路でも、使ったシードを記録
  しているので、いつでも同じものを作り直せます。

## 参考資料

このプロジェクトに取り組むうえで参照した古典的な資料:

* Jamis Buck, *Maze Generation Algorithms* シリーズ —
  <https://weblog.jamisbuck.org/2011/2/7/maze-generation-algorithm-recap>
  （バックトラッカー、Prim、Kruskal の定番の解説）。
* Jamis Buck, *Mazes for Programmers*, Pragmatic Bookshelf, 2015 —
  **braiding（編み込み）** の章が、行き止まりを取り除く発想の出どころ
  です。
* Walter D. Pullen, *Think Labyrinth: Maze Algorithms* —
  <https://www.astrolog.org/labyrnth/algrithm.htm>（perfect、braided、
  unicursal といった用語）。
* Wikipedia, *Maze generation algorithm* および *Spanning tree* —
  <https://en.wikipedia.org/wiki/Maze_generation_algorithm>
* Python 公式ドキュメント:
  [`random`](https://docs.python.org/3/library/random.html)、
  [`typing`](https://docs.python.org/3/library/typing.html)、
  [PEP 257](https://peps.python.org/pep-0257/)（docstring）、
  [Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)。
* [Choose a License](https://choosealicense.com/) — 再利用可能なモジュール
  に MIT を選ぶために使いました。
* 256 色端末描画のための ANSI エスケープコード —
  <https://en.wikipedia.org/wiki/ANSI_escape_code#256-colour_mode>

### AI をどう使ったか

<!-- TODO: この節は、実際に自分たちがやったことに合わせて直すこと。 -->

AI（Claude）はペアプログラミングの相棒として、次の作業に使いました。

* **アルゴリズムの検討** — 選ぶ前に再帰的バックトラッカー、Prim、
  Kruskal の比較を尋ね、「通路セルの全域木はそのまま完全迷路である」と
  いう主張を確かめました。
* **定型部分の下書き** — `KEY=VALUE` のパーサ、引数とエラーの処理、
  `Makefile`、`pyproject.toml` は AI の助けを借りて下書きし、そのあと
  1 行ずつ読み直しました。
* **「42」パターンのデバッグ** — 最初のビットマップフォント（3×5）は
  数字の内側に幅 1 セルのくぼみを作ってしまい、編み込みでは開けられず、
  避けようのない行き止まりが 3 つ残りました。原因の特定は AI との議論
  から出てきたもので、修正（穴の厚みが必ず 2 セル以上になる 4×7 の
  フォント）を実装し、何百通りもの迷路サイズを対象にしたランダムな
  ストレステストで検証しました。
* **docstring とこの README のレビュー**。

AI をブラックボックスとして使うことは **しませんでした**。生成された
断片はすべて読み、コードの他の部分に合わせて書き直し、テストで覆い
ました。検証ロジック（`check()` と、テスト側の独立した出力ファイル
パーサ）は、AI が提案した近道が気づかれずに通ってしまわないように、
意図してそう書いています。

## ディレクトリ構成

```
.
├── a_maze_ing.py                     # メインプログラム（エントリポイント）
├── mazegen.py                        # 再利用モジュール: MazeGenerator
├── mazegen-1.0.0-py3-none-any.whl    # ビルド済み pip パッケージ
├── amazeing/
│   ├── config.py                     # KEY=VALUE の解析と検証
│   ├── output.py                     # 出力ファイルの書き出し
│   ├── render.py                     # 端末描画、配色テーマ
│   ├── ui.py                         # 対話メニュー
│   └── mlxview.py                    # 任意機能の MiniLibX ウィンドウ
├── config.txt                        # 既定の設定
├── pyproject.toml                    # パッケージのビルド設定
├── Makefile
├── LICENSE.md                        # MIT と、その理由
├── README.md                         # 英語版
└── README.ja.md                      # 日本語版（このファイル）
```

コミットしているのは subject が要求するファイルだけです。独自のツール
設定ファイルも、キャッシュも、ビルドの残骸もありません。開発ツールと
flake8 の除外設定は `Makefile` の中に置いてあるので、この一覧の外にある
ものを追跡する必要はありません。テストプログラムは意図的に含めていません
（「提出も採点もされない」ため）。私たちのものではなく subject に *付属
する* 2 つのファイル、`maze_analyzer.py` と `mlx-2.2.tgz` も同様です。
`make analyze` と `make install-mlx` を使うときは、`Makefile` の隣に
コピーしてください。

## チームとプロジェクト管理

<!-- TODO: この節は、自分たちのチームと計画を書くこと。 -->

### 役割

| メンバー   | 役割                                                          |
| ---------- | ------------------------------------------------------------- |
| `<login1>` | *(例: 生成アルゴリズムと再利用モジュール)*                    |
| `<login2>` | *(例: 設定の解析、出力ファイル、エラー処理)*                  |
| `<login3>` | *(例: 端末描画、対話メニュー、パッケージング)*                |

### 当初の計画と、その変化

| 手順 | 計画                                        | 実際にどうなったか |
| ---- | ------------------------------------------- | ------------------ |
| 1    | 設定の解析とエラー処理                      | *(記入する)*       |
| 2    | 完全迷路の生成と出力ファイル                | *(記入する)*       |
| 3    | 「42」パターン                              | *(記入する)*       |
| 4    | Pac-Man モードのための編み込み              | *(記入する)*       |
| 5    | 端末描画とメニュー                          | *(記入する)*       |
| 6    | パッケージング、README、ライセンス          | *(記入する)*       |

### うまくいったこと、改善できること

* **うまくいった:** 初日から `mazegen.py` をアプリケーション層から完全に
  独立させたこと。おかげでパッケージのビルドは造作もなく、モジュール単体
  でのテストも簡単になりました。
* **うまくいった:** `check()` を早い段階で書いたこと。subject のすべての
  要件がそのままアサーションになり、ランダムなストレステストが、手で
  選んだ迷路 1 つでは隠れていたはずのパターン由来の行き止まりバグを
  捕まえてくれました。
* **改善できる:** 編み込みが貪欲法なので、どの壁を開けるかについて
  もっと賢くできるはずです。そうすればより整った、より Pac-Man らしい
  盤になります。
* **うまくいった:** subject の `maze_analyzer.py` をテストに組み込んだ
  こと。これはプロジェクトが採点されるまさにそのオラクルなので、Pac-Man
  モードの規則について推測の余地がなくなりました。
* **改善できる:** MiniLibX ビューアは、本物のウィンドウではなく差し込んだ
  テスト用の代役を通してテストしています。subject に付属する wheel が
  Linux 専用だからです。描画ロジックは覆えていますが、実際の X11
  ウィンドウはクラスタの機械上で手作業で確認する必要があります。

### 使ったツール

* バージョン管理に **Git**。
* インストール / 実行 / デバッグ / lint / テスト / ビルドを揃えるために
  **`make`**。
* 静的検査に **flake8**（PEP 8）と **mypy**（`--strict` でプロジェクト
  全体が通ります）。
* ユニットテストに **pytest**。ランダムなストレステストも含みます。
* pip パッケージに **`build` + setuptools**。
* 参照実装の検証器として **`maze_analyzer.py`**（subject に付属）。
  `make analyze` からもテストからも使っています。
* 任意機能のグラフィカル表示に **MiniLibX**（`mlx-2.2.tgz`、subject に
  付属）。
* ペアプログラミングの相棒として **Claude**。上の *参考資料* を参照。
