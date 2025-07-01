from flask import Blueprint, render_template, request, redirect, url_for, flash
from . import db
from .models import Ingredient

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