"""RTS - Recipe Track System

Provides a version control system that specializes for foods
"""

import ast
import unicodedata
from contextlib import suppress
from functools import lru_cache


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


class IngredientParser:
    def parse(self, raw_data):
        tokens = raw_data.split()
        ingredients = []
        current_ingredient = []

        self.merge_quantities(tokens)

        for token in tokens:
            if (
                self.parse_quantity(token)
                is not None  # we saw a new quantitiy
                and len(current_ingredient)
                > 0  # and there are some ingredients in the current buffer
            ):
                ingredients.append(current_ingredient.copy())
                current_ingredient.clear()
            current_ingredient.append(token)

        else:
            ingredients.append(current_ingredient.copy())

        return ingredients

    def merge_quantities(self, tokens):
        offset = 0
        for n, token in enumerate(tokens.copy()):
            n -= offset
            if (
                self.parse_quantity(token) is not None
                and self.parse_quantity(tokens[n + 1]) is not None
            ):
                tokens[n] = f"({tokens[n]}, {tokens.pop(n + 1)})"
                offset += 1

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
