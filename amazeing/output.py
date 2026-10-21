"""迷路の出力ファイルの書き出し。"""

from __future__ import annotations

from typing import List

from mazegen import MazeGenerator


class OutputError(Exception):
    """迷路をディスクに書き出せないときに送出する。"""


def build_lines(generator: MazeGenerator) -> List[str]:
    """出力ファイルの内容を、1 行ずつのリストとして組み立てる。

    並びは subject が指定するとおり。格子の 1 行をファイルの 1 行にし
    （1 セルにつき 16 進数 1 桁）、空行のあとに入口、出口、最短経路が続く。

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
    # どのキーを直せばよいか分かるよう、エラーのメッセージは OUTPUT_FILE で
    # 始める。
    try:
        with open(path, "w", encoding="utf-8") as stream:
            stream.write(payload)
    except IsADirectoryError:
        raise OutputError(
            f"OUTPUT_FILE: {path!r} is a directory, not a file"
        ) from None
    except PermissionError:
        raise OutputError(
            f"OUTPUT_FILE: no permission to write {path!r}"
        ) from None
    except FileNotFoundError:
        raise OutputError(
            f"OUTPUT_FILE: the directory of {path!r} does not exist"
        ) from None
    except OSError as error:
        raise OutputError(
            f"OUTPUT_FILE: cannot write {path!r}: {error.strerror}"
        ) from None
    except ValueError:  # ファイル名に NUL 文字が含まれているなど
        raise OutputError(
            f"OUTPUT_FILE: {path!r} is not a valid file name"
        ) from None
