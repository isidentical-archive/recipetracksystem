"""RTS - Recipe Track System

Provides a version control system that specializes for foods
"""

import ast
import unicodedata
from contextlib import suppress


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

        for token in tokens:
            if self.parse_quantity(token) and len(current_ingredient) > 0:
                ingredients.append(current_ingredient.copy())
                current_ingredient.clear()
            current_ingredient.append(token)

        else:
            ingredients.append(current_ingredient.copy())

        return ingredients

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
