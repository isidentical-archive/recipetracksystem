"""RTS - Recipe Track System

Provides a version control system that specializes for foods
"""
from __future__ import annotations

import ast
import unicodedata
from contextlib import suppress
from dataclasses import dataclass
from functools import lru_cache
from typing import Union


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
                ingredient[0], ingredient[1], " ".join(ingredient[1:])
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


if __name__ == "__main__":
    with open("data/test_data") as f:
        lines = f.readlines()

    test_case = lines[3:50]
    parser = IngredientParser()
    ingredients = parser.parse(" ".join(test_case))
    for ingredient, line in zip(ingredients, test_case):
        print(line.strip(), "=>", ingredient)
