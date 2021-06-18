import argparse
from dataclasses import asdict, dataclass
from enum import Enum
import itertools
import json
from typing import Iterator, TypeVar
from urllib import parse, request

T = TypeVar('T')

def chunks(iterator: Iterator[T], n: int) -> Iterator[Iterator[T]]:
    for first in iterator:
        rest_of_chunk = itertools.islice(iterator, 0, n - 1)
        yield itertools.chain([first], rest_of_chunk)

def read_json(path: str) -> str:
    with open(path) as json_file:
        return json.load(json_file)

def write_json(data: str, path: str) -> str:
    with open(path, "w") as json_file:
        return json.dump(data, json_file, sort_keys=False, indent=2)

BASE_URL = "https://min-api.cryptocompare.com/data/pricemulti"

@dataclass
class Erc20Token:
    address: str
    decimals: int
    logo: str
    name: str
    symbol: str
    website: str

class CurrencyType(str, Enum):
    COIN = "COIN"
    ERC20 = "ERC20"
    FIAT = "FIAT"

@dataclass
class Currency:
    symbol: str
    name: str
    type: CurrencyType
    decimals: int

def build_tokens_list(input_file: str) -> Iterator[Erc20Token]:
    all_tokens = read_json(input_file)
    for t in all_tokens:
        yield Erc20Token(**t)

def filter_cryptocompare_supported(tokens: Iterator[Erc20Token]) -> Iterator[Erc20Token]:
    for chunk in chunks(tokens, 50):
        token_map = {t.symbol: t for t in chunk}
        params = {
            "fsyms": ",".join(token_map.keys()),
            "tsyms": "USD"
        }
        url = BASE_URL + "?" + parse.urlencode(params)
        response = request.urlopen(url).read()
        for currency in json.loads(response):
            if currency in token_map:
                yield token_map[currency]

def convert_token_to_currency(token: Erc20Token) -> Currency:
    return Currency(
        symbol=token.symbol, 
        name=token.name, 
        type=CurrencyType.ERC20, 
        decimals=token.decimals
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file", dest="input_file", help="Input file name")
    parser.add_argument("--output-file", dest="output_file", help="Output file name")
    args = parser.parse_args()

    tokens = build_tokens_list(args.input_file)

    supported_tokens = filter_cryptocompare_supported(tokens)
    currencies = [asdict(convert_token_to_currency(t)) for t in supported_tokens]

    print(f"Writing {len(currencies)} currencies to {args.output_file}")
    write_json(currencies, args.output_file)

if __name__ == '__main__':
    main()

