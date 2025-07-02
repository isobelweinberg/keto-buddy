from flask import Blueprint, render_template, request, redirect, url_for, flash
from . import db
from .models import Ingredient, Recipe, RecipeIngredient
from .forms import RecipeForm

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return redirect(url_for('main.ingredients'))

@main.route('/ingredients', methods=['GET'])
def ingredients():
    all_ingredients = Ingredient.query.all()
    return render_template('ingredients.html', ingredients=all_ingredients)

@main.route('/ingredients', methods=['POST'])
def add_ingredient():
    name = request.form.get('name')
    type_ = request.form.get('type')
    units = request.form.get('units')
    percent_fat = float(request.form.get('percent_fat', 0))
    percent_carbs = float(request.form.get('percent_carbs', 0))
    percent_protein = float(request.form.get('percent_protein', 0))
    source = request.form.get('source')  # New field
    total_calories = float(request.form.get('total_calories', 0))

    new_ingredient = Ingredient(
        name=name,
        type=type_,
        units=units,
        percent_fat=percent_fat,
        percent_carbs=percent_carbs,
        percent_protein=percent_protein,
        total_calories=total_calories,
        source=source  # Set source here
    )

    db.session.add(new_ingredient)
    db.session.commit()

    flash(f'Added ingredient: {name}', 'success')
    return redirect(url_for('main.ingredients'))

@main.route('/recipes/new', methods=['GET', 'POST'])
def new_recipe():
    form = RecipeForm()
    nutrition_data = {}
    form.set_ingredient_choices()

    # Gather nutritional info to pass to JS
    all_ingredients = Ingredient.query.order_by(Ingredient.name).all()
    nutrition_data = {
        ing.id: {
            'name': ing.name,
            'percent_fat': ing.percent_fat,
            'percent_carbs': ing.percent_carbs,
            'percent_protein': ing.percent_protein,
            'total_calories': ing.total_calories
        }
        for ing in all_ingredients
    }

    if form.validate_on_submit():
        # Create recipe object
        recipe = Recipe(
            name=form.name.data,
            notes=form.notes.data,
            ratio=form.ratio.data
        )

        total_fat = total_carbs = total_protein = total_calories = 0.0

        for ingredient_form in form.ingredients.entries:
            ingredient = Ingredient.query.get(ingredient_form.ingredient_id.data)
            amount = ingredient_form.amount.data

            # Calculate nutrition for this ingredient amount
            fat = ingredient.percent_fat * amount / 100
            carbs = ingredient.percent_carbs * amount / 100
            protein = ingredient.percent_protein * amount / 100
            calories = ingredient.total_calories * amount / 100

            total_fat += fat
            total_carbs += carbs
            total_protein += protein
            total_calories += calories

            ri = RecipeIngredient(
                ingredient_id=ingredient.id,
                amount=amount,
                fat=fat,
                carbs=carbs,
                protein=protein,
                calories=calories
            )
            recipe.ingredients.append(ri)

        # Save totals in recipe
        recipe.total_fat = total_fat
        recipe.total_carbs = total_carbs
        recipe.total_protein = total_protein
        recipe.total_calories = total_calories

        db.session.add(recipe)
        db.session.commit()

        flash('Recipe created successfully!', 'success')
        return redirect(url_for('main.recipes'))

    return render_template('new_recipe.html', form=form, nutrition_data=nutrition_data)

@main.route('/recipes')
def recipes():
    all_recipes = Recipe.query.order_by(Recipe.name).all()
    
    grouped = {
        'breakfast': [],
        'main': [],
        'snack': []
    }
    for recipe in all_recipes:
        if recipe.meal_type in grouped:
            grouped[recipe.meal_type].append(recipe)

    return render_template('recipes.html', recipes_by_type=grouped)