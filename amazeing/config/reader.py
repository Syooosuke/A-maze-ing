"""設定ファイルを読み、KEY=VALUE の組を文字列のまま取り出す。"""

from __future__ import annotations

from typing import Dict, List, Tuple

MANDATORY_KEYS: Tuple[str, ...] = (
    "WIDTH",
    "HEIGHT",
    "ENTRY",
    "EXIT",
    "OUTPUT_FILE",
    "PERFECT",
)
OPTIONAL_KEYS: Tuple[str, ...] = ("SEED",)
KNOWN_KEYS: Tuple[str, ...] = MANDATORY_KEYS + OPTIONAL_KEYS


class ConfigError(Exception):
    """設定ファイルを使えないときに送出する。メッセージは利用者向け。"""


def read_pairs(path: str) -> Dict[str, str]:
    """設定ファイルから KEY=VALUE の組を読み取る。値はまだ変換しない。

    空行と "#" で始まる行は読み飛ばす。キーは大文字にそろえる。

    Returns:
        キーから値（前後の空白は除去済み）への対応表。

    Raises:
        ConfigError: ファイルを読めない、または書式が正しくない場合。
    """
    pairs: Dict[str, str] = {}
    for number, line in enumerate(_read_lines(path), start=1):
        where = f"{path}:{number}"
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        if "=" not in text:
            raise ConfigError(f"{where}: {text!r} is not a KEY=VALUE line")
        raw_key, raw_value = text.split("=", 1)
        key = raw_key.strip().upper()
        if not key:
            raise ConfigError(f"{where}: the key is missing")
        if key not in KNOWN_KEYS:
            known = ", ".join(KNOWN_KEYS)
            raise ConfigError(f"{where}: unknown key {key!r} (known: {known})")
        if key in pairs:
            raise ConfigError(f"{where}: {key!r} is defined twice")
        pairs[key] = raw_value.strip()
    return pairs


def _read_lines(path: str) -> List[str]:
    """ファイルの全行を返す。読めない理由は ConfigError で伝える。"""
    try:
        with open(path, "r", encoding="utf-8") as stream:
            return stream.readlines()
    except FileNotFoundError:
        raise ConfigError(f"configuration file {path!r} not found") from None
    except IsADirectoryError:
        raise ConfigError(
            f"configuration file {path!r} is a directory, not a file"
        ) from None
    except PermissionError:
        raise ConfigError(f"no permission to read {path!r}") from None
    except UnicodeDecodeError:
        raise ConfigError(f"{path!r} is not a readable text file") from None
    except OSError as error:
        raise ConfigError(f"cannot read {path!r}: {error.strerror}") from None
