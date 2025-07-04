from datetime import date

from flask import Blueprint, render_template, request, redirect, url_for, flash
from . import db
from .models import Ingredient, Recipe, RecipeIngredient, Target, TargetBreakdown
from .forms import RecipeForm, TargetForm

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
            'units': ing.units,
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
            author=form.author.data,
            meal_type=form.meal_type.data,
            notes=form.notes.data
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
        recipe.ratio = total_fat / (total_protein + total_carbs) if (total_protein + total_carbs) > 0 else None

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

@main.route('/targets', methods=['GET', 'POST'])
def targets():
    form = TargetForm()
    if form.validate_on_submit():
        new_target = Target(
            ratio=form.ratio.data,
            calories=form.calories.data,
            fat=form.fat.data,
            protein=form.protein.data,
            carbs=form.carbs.data,
            num_main_meals=form.num_main_meals.data,
            num_snacks=form.num_snacks.data,
            date=date.today()
        )
        db.session.add(new_target)
        db.session.commit()

        # Handle optional meal breakdown
        if any([form.meal_calories.data, form.meal_fat.data, form.meal_protein.data, form.meal_carbs.data]):
            meal_breakdown = TargetBreakdown(
                item='Meal',
                calories=form.meal_calories.data or 0,
                fat=form.meal_fat.data or 0,
                protein=form.meal_protein.data or 0,
                carbs=form.meal_carbs.data or 0,
                date=new_target.date,
                target_id=new_target.id
            )
            db.session.add(meal_breakdown)

        # Handle optional snack breakdown
        if any([form.snack_calories.data, form.snack_fat.data, form.snack_protein.data, form.snack_carbs.data]):
            snack_breakdown = TargetBreakdown(
                item='Snack',
                calories=form.snack_calories.data or 0,
                fat=form.snack_fat.data or 0,
                protein=form.snack_protein.data or 0,
                carbs=form.snack_carbs.data or 0,
                date=new_target.date,
                target_id=new_target.id
            )
            db.session.add(snack_breakdown)

        db.session.commit()
        return redirect(url_for('main.targets'))

    latest_target = Target.query.order_by(Target.date.desc(), Target.id.desc()).first()

    return render_template('targets.html', target=latest_target, form=form)
