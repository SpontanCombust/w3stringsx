import io

from w3stringsx.lib.logging import get_logger
from w3stringsx.lib.utils import filter_str_keys, guess_file_encoding, sanitize_str_keys


__all__ = [
    "parse_ws_for_str_keys"
]


logger = get_logger()


def parse_ws_for_str_keys(ws_path: str, search: str) -> list[str]:
    if search == "":
        raise Exception("Parsing WitcherScript requires to specify the searched keyword")

    encoding = guess_file_encoding(ws_path)
    logger.info(f"Reading WitcherScript {ws_path}. Detected encoding: {encoding}")

    possible_keys = list[str]()
    with io.open(ws_path, mode='r', encoding=encoding) as f:
        for line in f:
            quoted = line.split('"')[1::2]
            possible_keys.extend(quoted)

    possible_keys = filter_str_keys(sanitize_str_keys(possible_keys), search)

    logger.info(f"Found {len(possible_keys)} string keys in {ws_path}")
    return possible_keys
