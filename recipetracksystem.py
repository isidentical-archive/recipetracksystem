"""RTS - Recipe Track System

Provides a version control system that specializes for foods
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import unicodedata
from contextlib import suppress
from dataclasses import asdict, dataclass, field
from datetime import datetime
from functools import lru_cache, partial
from pathlib import Path

DEFAULT_BRANCH = "main"


class ConstantMerger(ast.NodeTransformer):
    """Handles a common case of constant expressions in division format
    E.g: 1/2 1/3 1/4 or 1/2 + 1/4
    """

    def merge(self, source):
        result = self.visit(ast.parse(source)).body[0].value
        if isinstance(result, (float, str)):
            return result
        else:
            raise ValueError("Malformed node")

    def visit_Constant(self, node):
        return node.value

    def visit_BinOp(self, node):
        self.generic_visit(node)
        if type(node.op) is ast.Div:
            # 1/3 cup water
            return node.left / node.right
        elif type(node.op) is ast.Sub:
            # 5-6 teaspoon sugar
            return f"{node.left}-{node.right}"

        return node

    def visit_Tuple(self, node):
        return "(" + ",".join(map(str, node.elts)) + ")"


QUANTITY_PARSERS = (
    ast.literal_eval,  # can handle integers, floats
    unicodedata.numeric,  # can handle unicodes e.g: ½
    ConstantMerger().merge,
)

QUANTITY_PARSER_ERRORS = (ValueError, TypeError, SyntaxError)


@dataclass
class Ingredient:
    name: str
    unit: str
    quantity: Quantity

    def __str__(self):
        return f"{self.quantity} {self.unit} {self.name}"


class IngredientParser:
    def parse(self, raw_data):
        tokens = raw_data.split()
        ingredients = []
        current_ingredient = []

        self.merge_parens(tokens)
        self.merge_quantities(tokens)

        for token in tokens:
            if (
                self.parse_quantity(token) is not None
                and len(current_ingredient) > 0
            ):
                ingredients.append(current_ingredient.copy())
                current_ingredient.clear()
            current_ingredient.append(token)

        else:
            ingredients.append(current_ingredient.copy())

        for ingredient in ingredients.copy():
            yield Ingredient(
                " ".join(ingredient[2:]), ingredient[1], ingredient[0]
            )
        return ingredients

    def merge_quantities(self, tokens):
        # e.g: 10 1/2 lettuces
        offset = 0
        for n, token in enumerate(tokens.copy()):
            n -= offset
            if (
                self.parse_quantity(token) is not None
                and self.parse_quantity(tokens[n + 1]) is not None
            ):
                tokens[n] = f"({tokens[n]}, {tokens.pop(n + 1)})"
                offset += 1

    def merge_parens(self, tokens):
        # e.g: 1 (16 oz) box pasta
        start = None
        parentheses = []
        for n, token in enumerate(tokens.copy()):
            if token.startswith("("):
                start = n
            elif start is not None and token.endswith(")"):
                parentheses.append((start, n + 1))
                start = None

        offset = 0
        for start, end in parentheses:
            matched_tokens = slice(start - offset, end - offset)
            tokens[matched_tokens] = (" ".join(tokens[matched_tokens]),)
            offset += end - start - 1

    @lru_cache
    def parse_quantity(self, quantity):
        for parser in QUANTITY_PARSERS:
            try:
                return parser(quantity)
            except QUANTITY_PARSER_ERRORS:
                continue


def as_md5(name):
    hash_obj = hashlib.md5(name.encode())
    return hash_obj.hexdigest()


json.dump = partial(json.dump, default=str)


@lru_cache
def _get_base_dir():
    path = Path(os.environ.get("XDG_CACHE_HOME", "~/.cache"))
    path = path.expanduser() / "recipetracksystem"
    if not path.exists():
        path.mkdir()
    return path


@dataclass
class Session:
    recipe: str


@dataclass
class Metadata:
    name: str
    branch: str = DEFAULT_BRANCH
    creation_date: datetime = field(default_factory=datetime.now)


def read_session():
    path = _get_base_dir() / "session.json"
    if path.exists():
        with open(path) as f:
            session = json.load(f)
        return Session(**session)
    else:
        raise ValueError("No session file has been created!")


def update_session(**kwargs):
    path = _get_base_dir() / "session.json"
    if path.exists():
        with open(path) as f:
            session = json.load(f)
    else:
        session = asdict(Session(**kwargs))
    session.update(kwargs)
    with open(path, "w") as f:
        json.dump(session, f)


def create_repo(name, update=False):
    path = _get_base_dir() / as_md5(name)
    path.mkdir(exist_ok=update)

    metadata = Metadata(name)
    with open(path / "metadata.json", "w") as f:
        json.dump(asdict(metadata), f)
    update_session(recipe=name)


def add(raw_ingredients):
    parser = IngredientParser()
    ingredients = tuple(map(asdict, parser.parse(" ".join(raw_ingredients))))
    print(ingredients)


def main():
    options = parse_args()
    run_args(options)


def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action")
    command_groups = {}

    for subparser in ("create", "add", "recipe", "switch", "commit"):
        command_groups[subparser] = subparsers.add_parser(subparser)

    command_groups["create"].add_argument("name")
    command_groups["create"].add_argument(
        "--update", action="store_true", default=False
    )

    command_groups["add"].add_argument("ingredients", nargs="+")

    command_groups["switch"].add_argument("to")

    options = parser.parse_args()

    if options.action is None:
        parser.print_help()
        raise SystemExit(1)

    return options


def run_args(options):
    if options.action == "create":
        create_repo(name=options.name, update=options.update)
    elif options.action == "add":
        add(raw_ingredients=options.ingredients)
    elif options.action == "recipe":
        print(read_session().recipe)
    elif options.action == "switch":
        update_session(recipe=options.to)
    else:
        raise ValueError("Unknown action!")


if __name__ == "__main__":
    main()
