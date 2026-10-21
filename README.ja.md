*This project has been created as part of the 42 curriculum by syokota, atajima.*

[English](README.md) | **日本語**

# A-Maze-ing

## 概要

**A-Maze-ing** は、プレーンテキストの設定ファイルから迷路を生成し、
壁をコンパクトな 16 進数で符号化してディスクに書き出し、さらに端末上で
色付き・対話メニュー付きで表示するプログラムです。

同じ格子から、性格の異なる 2 種類の迷路を作れます。

* `PERFECT=True` — **完全迷路**。入口と出口の間の経路がちょうど 1 本
  だけで、ループはどこにもありません。教科書どおりの迷路です。
* `PERFECT=False`（`config.txt` の値）— **遊べる Pac-Man 盤**。すべての通路に到達
  でき、四隅と中央が開いていて、独立したループが 2 つ以上あり、行き止まり
  を取り除いてあるので、追われているプレイヤーには常に逃げ道があります。

どちらのモードでも、完全に閉じたセルを使って **「42」** を迷路の
中に描き、入口から出口への最短経路を計算して出力します。

生成ロジックそのものは独立した 1 つのパッケージ
[`mazegen/`](mazegen/) にまとまっており、
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

# キャッシュとビルド生成物、さらに venv と maze.txt も消す
make clean
make fclean

# Makefile のルールを一覧にする
make help
```

### 対話メニュー

迷路は端末に表示します。標準入力が端末であれば、そのあとにメニューが
出ます。

```
=== A-Maze-ing ===
1. Re-generate a new maze
2. Show / Hide the shortest path
3. Rotate the wall colours
4. Quit
```

色は 256 色の ANSI コードです。出力をファイルやパイプにリダイレクト
したときは自動的に無効になり、素の ASCII 描画（壁 `##`、入口 `EE`、出口 `XX`、
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

`PERFECT` は `True` か `False` を受け付けます（大文字小文字は問いません）。
迷路は最大 1000×1000 セルです。また `PERFECT=False` の盤は 2×2 にできま
せん。2×2 の格子にはループが 1 つしか作れず、遊べる盤には 2 つ必要だから
です。

既定のファイルは [`config.txt`](config.txt) です。

```ini
WIDTH=25
HEIGHT=17
ENTRY=0,0
EXIT=24,16
OUTPUT_FILE=maze.txt
PERFECT=False
SEED=42
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
`A`（`1010`）は東と西が閉じていることを表します。`F` はセルが完全に
閉じていることを表し、「42」のパターンはこの形で保存されます。

各行のあとに空行が 1 つ入り、さらに 3 行が続きます。入口の座標、出口の
座標、そして `N`、`E`、`S`、`W` の文字で表した最短経路です。すべての行は
`\n` で終わります。

```
9515153955155555513911513
A945692C3943955156AAAC3AA
...
C6C456C56C6C55545556C5456

0,0
24,16
SSSSEESSEEEEESSWWSSENEESSENESSESENESENEESSSWSEEEENESEEEE
```

隣り合うセルは、共有する壁について常に一致します。壁の変更は必ず両側を
同時に書き込む `Grid.open_wall()` / `Grid.close_wall()` だけを通すので、
矛盾したデータは構造上ありえません。

## 迷路の生成アルゴリズム

### どれを選んだか

迷路は **ランダム化した深さ優先探索**、いわゆる **再帰的
バックトラッカー**で掘ります。明示的なスタックを使って反復的に実装して
いるので、1000×1000 の迷路でも Python の再帰上限に達しません。これは
通路セルの *全域木* を作るもので、それはまさに完全迷路の定義そのもの
です。

生成は 4 段階で進みます。

1. **「42」を配置する。** 数字は 4×7 のビットマップフォントから描き
   （全体で 9×7 セル）、外周に触れず、入口・出口・四隅・中央を覆わない
   位置に置きます。選んだ配置は、残りのセルすべてが連結したままである
   ことを満たす必要があります。これらの
   セルは `F`（完全に閉じた状態）のまま残り、迷路はその *周りを* 掘って
   作られます。迷路が小さすぎてパターンが入らない場合（11×9 セル未満）や、
   入口と出口のせいで置ける場所がない場合は描画を諦め、コンソールに
   エラーメッセージを出します。
2. **全域木を掘る。** 再帰的バックトラッカーで、パターン以外のすべての
   セルに全域木を掘ります。この時点で迷路は完全迷路であり、
   `PERFECT=True` なら手順 3 は飛ばします。木にはループがないので、
   3×3（2×2 でも）の壁のない区画はできません。
3. **編み込む**（`PERFECT=False` のときだけ）。開いた壁が 1 枚しかない
   セルがある限り、そのセルの壁をもう 1 枚開け、さらにループが 2 つ以上に
   なるまで壁を開けます。壁を開けるのは 3×3 の完全な開放区画ができない
   場合だけなので、通路の幅が 2 セルを超えることはありません。これに
   よって、subject の求めるとおり行き止まりはごくわずかになります。
4. 幅優先探索で迷路を **解きます**。幅優先探索なので、得られる経路は
   本当に *最短* です。

### なぜこれを選んだか

* 再帰的バックトラッカーは分岐が少なく **長く曲がりくねった通路** を
  作るので、見て楽しく、解くのも本当に難しい迷路になります。Prim や
  Kruskal は短く枝分かれの多い形になりがちです。また定番のアルゴリズム
  の中でも動きを追いやすく、これは評価で自分のコードを説明しなければならない
  ときに効いてきます。
* 時間・メモリともに **セル数に対して O(n)** で、任意のグラフ上で動く
  ので、「42 のパターン以外のすべてのセル」に対象を限っても何のコストも
  かかりません。パターンのセルは単に有効な隣接セルにならないだけです。
* 先に全域木を作ってから編み込むことで、**1 本のコードパスから必要な
  2 つのモード**が得られます。完全迷路は、遊べる盤のちょうど中間状態に
  なっているわけです。

代償として、素のバックトラッカー迷路は行き止まりが *非常に* 多くなり
ます。だからこそ Pac-Man モードでは編み込みの段階が重要になります。

### 正しさ

`MazeGenerator.check()` は、生成した迷路を subject のあらゆる要件に照ら
して再検証します。外周が閉じていること、共有する壁が整合していること、
完全に連結していること、パターンのセルが完全に閉じていること、3×3 の
開放区画がないこと、完全迷路ならループがないこと、遊べる盤ならループが
あり四隅と中央が開いていて行き止まりがごくわずかであること。プログラムは生成のたび
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
# あるいは直接:
python3 maze_analyzer.py maze.txt
```

どちらのモードでも、subject が求める判定になります。

```
# PERFECT=False
Verdict: Pac-Man-USABLE: fully connected, corners and centre reachable, ...

# PERFECT=True
Verdict: PERFECT maze: a single path, no loop -> matches PERFECT=True
```

この解析スクリプトは手元のテストにも組み込んでいます。大きさとシードの
異なる迷路を生成し、これらの判定に達することを要求しています。このテスト一式はコミットしていません（subject がテストプログラム
は「提出も採点もされない」と述べているためです）が、`tests/` ディレクトリ
があれば `make test` で実行できます。

## 何がどう再利用できるか

迷路生成に必要なものはすべて、**独立した 1 つのパッケージ**
[`mazegen/`](mazegen/) に入っています。標準ライブラリ以外への
**依存はなく**、設定ファイルや端末や色のことは何も知りません。これは
リポジトリ直下で pip パッケージとして公開しています。

パッケージの中は役割ごとのモジュールに分かれています。`Grid` が
セルと壁を持ち、`generation/`（作る）と `analysis/`（調べる）の中の
モジュールは、それを引数に受け取る関数です。`MazeGenerator.generate()` は
それらを上から順に呼ぶだけなので、生成の流れはこのメソッドを読めば
追えます。

* `mazegen-1.0.0-py3-none-any.whl`

再ビルドに必要なものはすべてリポジトリに揃っています
（[`pyproject.toml`](pyproject.toml)）。`make build` で wheel を作り直せます。

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
)
gen.generate()
```

不正な組み合わせを渡すと、明示的なメッセージ付きで
`mazegen.MazeError` が送出されます。

### 生成された構造と解にアクセスする

```python
from mazegen import EAST, NORTH, SOUTH, WEST

gen.grid              # List[List[int]]、grid[y][x] = 閉じた壁のビットマスク
gen.grid[4][3] & EAST # セル (3, 4) の東の壁が閉じていれば 0 以外

gen.pattern_cells     # Set[(x, y)] -- 完全に閉じた「42」のセル
gen.pattern_warning   # 「42」を諦めた理由。描けていれば None
gen.seed_used         # このシードを使えば同じ迷路を再現できる

gen.solution          # [(0, 0), (1, 0), ...] 入口 -> 出口の最短経路
gen.directions        # 同じ経路を "ESSEEN..." の文字で表したもの

gen.to_hex_lines()    # ['9155...', ...] 1 セル 16 進数 1 桁
gen.dead_ends()       # 開いた壁が 1 枚しかないセル
gen.loop_count()      # 独立したループの数
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

このドキュメントの短い版はモジュールの docstring（ほかの docstring と
同じく日本語）にもあるので、パッケージをインストールしたあとは
`pydoc mazegen` や `help(mazegen)` で読めます。

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
├── mazegen/                          # 再利用パッケージ: MazeGenerator
│   ├── __init__.py                   # 公開 API とモジュール docstring
│   ├── generator.py                  # MazeGenerator: 生成の手順
│   ├── validation.py                 # コンストラクタ引数の検証
│   ├── grid.py                       # Grid: セルとその壁
│   ├── constants.py                  # 壁ビット、向き、大きさの上限
│   ├── errors.py                     # MazeError
│   ├── generation/                   # 迷路を作る
│   │   ├── pattern.py                # "42" の置き場所
│   │   ├── glyphs.py                 # "42" のビットマップ字形
│   │   ├── backtracker.py            # 再帰的バックトラッカー
│   │   └── braiding.py               # 行き止まりの除去とループの追加
│   └── analysis/                     # できた迷路を調べる
│       ├── routes.py                 # 最短経路、ループ、行き止まり
│       └── verify.py                 # subject の要件の自己検証
├── mazegen-1.0.0-py3-none-any.whl    # ビルド済み pip パッケージ
├── amazeing/                         # アプリケーション（パッケージ外）
│   ├── output.py                     # 出力ファイルの書き出し
│   ├── config/                       # 設定ファイル
│   │   ├── settings.py               # load_config(): MazeConfig を作る
│   │   ├── reader.py                 # KEY=VALUE の行を読む
│   │   └── values.py                 # 値の変換（整数、真偽値、x,y）
│   └── display/                      # 端末への表示
│       ├── canvas.py                 # 何をどこに描くか（色は持たない）
│       ├── themes.py                 # 配色テーマ
│       ├── render.py                 # キャンバス -> 端末の文字列
│       ├── session.py                # 表示中の迷路と表示設定
│       └── menu.py                   # 端末の対話メニュー
├── config.txt                        # 既定の設定
├── pyproject.toml                    # パッケージのビルド設定
├── Makefile
├── .flake8                           # flake8 の除外設定（.venv、build など）
├── LICENSE.md                        # MIT と、その理由
├── README.md                         # 英語版
└── README.ja.md                      # 日本語版（このファイル）
```

コミットしているのは subject が要求するファイルと、`.gitignore`、
`.flake8` だけです。キャッシュもビルドの残骸もありません。`.flake8` は
`make install` が作る仮想環境を flake8 の検査から外すためのもので、
subject のとおり素の `flake8 .` を実行しても、私たちのソースだけが
検査されます。テストプログラムは意図的に含めていません
（「提出も採点もされない」ため）。私たちのものではなく subject に *付属
する* `maze_analyzer.py` も同様です。`make analyze` を使うときは、
`Makefile` の隣にコピーしてください。

## チームとプロジェクト管理

### 役割

| メンバー   | 役割                                                          |
| ---------- | ------------------------------------------------------------- |
| `atajima` | *生成アルゴリズムと再利用モジュール*                    |
| `syokota` | *設定の解析、出力ファイル、エラー処理*                  |

### 当初の計画と、その変化

| 手順 | 計画                                        | 実際にどうなったか |
| ---- | ------------------------------------------- | ------------------ |
| 1    | 設定の解析とエラー処理                      | 計画どおり最初に完成。範囲チェック（サイズ、入口と出口）は後から `MazeGenerator` 側（`mazegen/validation.py`）に移し、設定ファイルを通さずに使っても安全で、規則が 1 か所にまとまるようにした。 |
| 2    | 完全迷路の生成と出力ファイル                | 最初は再帰的バックトラッカーだけで作った。`check()` で全アルゴリズムを自動検証できるようになってから、ボーナスとして Prim と Kruskal を追加した。 |
| 3    | 「42」パターン                              | 予定より時間がかかった。最初の 3×5 フォントでは、編み込みで開けられない 1 セル幅のくぼみができた。4×7 フォントに替え、残りの迷路がつながったままになる位置に置くようにした。 |
| 4    | Pac-Man モードのための編み込み              | 計画どおり、完全迷路の後に実装した。編み込みで行き止まりを消し、3×3 の広い空間ができない場合にだけ壁を開ける。最後に 2 つ以上のループを保証する処理を加えた。subject の `maze_analyzer.py` をテストに組み込んで確かめた。 |
| 5    | 端末描画とメニュー                          | 端末描画とメニューは計画どおりに完成した。同じキャンバスと配色を使う MiniLibX のウィンドウを後から追加した。subject の wheel は Linux 専用なので、`mlx` が使えないときは端末表示に切り替わる。 |
| 6    | パッケージング、README、ライセンス          | 計画どおり最後に wheel、MIT ライセンス、README を用意した。その後、読みやすさの整理と日本語 README の追加を行い、公開 API を変えずに `mazegen.py` を層構造のパッケージに分割した（使われていない公開メソッドと再公開は、その後に削除した）。最後に、提出物を小さくしてレビューしやすくするため、ボーナス（Prim、Kruskal）と任意機能（MiniLibX ウィンドウ、保存メニュー、追加の設定キー）を取り除いた。 |

### うまくいったこと、改善できること

* **うまくいった:** 初日から `mazegen` をアプリケーション層から完全に
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
* ペアプログラミングの相棒として **Claude**。上の *参考資料* を参照。
