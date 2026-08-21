"""迷路の出力ファイルの書き出し。"""

from __future__ import annotations

from typing import List

from mazegen import MazeGenerator


class OutputError(Exception):
    """迷路をディスクに書き出せないときに送出する。"""


def build_lines(generator: MazeGenerator) -> List[str]:
    """出力ファイルの内容を 1 行ずつそのまま組み立てる。

    並びは subject が指定するとおりで、1 セルにつき 16 進数 1 桁、1 行に
    つき 1 行分のセル、空行、続いて入口、出口、最短経路となる。

    Args:
        generator: ``generate()`` を呼び終えた生成器。

    Returns:
        ファイルの各行。末尾の改行は含まない。
    """
    lines = generator.to_hex_lines()
    lines.append("")
    lines.append(f"{generator.entry[0]},{generator.entry[1]}")
    lines.append(f"{generator.exit[0]},{generator.exit[1]}")
    lines.append(generator.directions)
    return lines


def write_maze(path: str, generator: MazeGenerator) -> None:
    """迷路を ``path`` に書き出す。

    Args:
        path: 出力先のファイル。既に存在する場合は上書きする。
        generator: ``generate()`` を呼び終えた生成器。

    Raises:
        OutputError: ファイルを書き出せない場合。
    """
    payload = "".join(f"{line}\n" for line in build_lines(generator))
    try:
        with open(path, "w", encoding="utf-8") as stream:
            stream.write(payload)
    except IsADirectoryError:
        raise OutputError(f"{path!r} is a directory, not a file") from None
    except PermissionError:
        raise OutputError(f"no permission to write {path!r}") from None
    except FileNotFoundError:
        raise OutputError(
            f"the directory of {path!r} does not exist"
        ) from None
    except OSError as error:
        raise OutputError(f"cannot write {path!r}: {error}") from None
