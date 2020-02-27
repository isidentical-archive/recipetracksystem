import pytest

from recipetracksystem import Ingredient, IngredientParser


@pytest.fixture
def ingredient_parser():
    return IngredientParser()


@pytest.mark.parametrize(
    "test",
    [
        (
            "1 teaspoon water",
            Ingredient(name="water", unit="teaspoon", quantity="1"),
        ),
        (
            "1.5 teaspoon water",
            Ingredient(name="water", unit="teaspoon", quantity="1.5"),
        ),
        (
            "1 1/2 teaspoon water",
            Ingredient(name="water", unit="teaspoon", quantity="(1, 1/2)"),
        ),
        (
            "1/3 cup water",
            Ingredient(name="water", unit="cup", quantity="1/3"),
        ),
        (
            "10-20 teaspoon water",
            Ingredient(name="water", unit="teaspoon", quantity="10-20"),
        ),
        (
            "1/2 teaspoon water",
            Ingredient(name="water", unit="teaspoon", quantity="1/2"),
        ),
        (
            "10 1/2 teaspoon water",
            Ingredient(name="water", unit="teaspoon", quantity="(10, 1/2)"),
        ),
        (
            "1/3 cup confectioners’ sugar",
            Ingredient(
                name="confectioners’ sugar", unit="cup", quantity="1/3"
            ),
        ),
        ("1 cup water", Ingredient(name="water", unit="cup", quantity="1")),
        (
            "1 gallon water",
            Ingredient(name="water", unit="gallon", quantity="1"),
        ),
        (
            "1 ounce water",
            Ingredient(name="water", unit="ounce", quantity="1"),
        ),
        (
            "1 (14.5 oz) can tomatoes",
            Ingredient(name="can tomatoes", unit="(14.5 oz)", quantity="1"),
        ),
        (
            "1 (16 oz) box pasta",
            Ingredient(name="box pasta", unit="(16 oz)", quantity="1"),
        ),
        (
            "1 slice cheese",
            Ingredient(name="cheese", unit="slice", quantity="1"),
        ),
    ],
)
def test_ingredient(test, ingredient_parser):
    ingredient, expected = test
    (result,) = ingredient_parser.parse(ingredient)
    assert result == expected
