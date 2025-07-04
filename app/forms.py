from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, FloatField, SelectField, FieldList, FormField, SubmitField, 
    DecimalField, IntegerField)
from wtforms.validators import DataRequired, NumberRange, Optional

from .models import Ingredient

class RecipeIngredientForm(FlaskForm):
    ingredient_id = SelectField('Ingredient', coerce=int, validators=[DataRequired()])
    amount = FloatField('Amount (g or ml)', validators=[DataRequired(), NumberRange(min=0.01)])

class RecipeForm(FlaskForm):
    name = StringField('Recipe Name', validators=[DataRequired()])
    ratio = FloatField('Ketogenic Ratio', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    author = SelectField('Author', choices=[
        ('', '-- Select author --'),
        ('hospital', 'Hospital'),
        ('home', 'Home')
    ], validators=[DataRequired(message="Please select an author.")])
    meal_type = SelectField('Meal Type', choices=[
        ('', '-- Select meal type --'),
        ('breakfast', 'Breakfast'),
        ('main', 'Main'),
        ('snack', 'Snack')
    ], validators=[DataRequired(message="Please select a meal type.")])
    
    ingredients = FieldList(FormField(RecipeIngredientForm), min_entries=1, max_entries=20)
    submit = SubmitField('Save Recipe')
    
    def set_ingredient_choices(self):
        # This method populates the ingredient dropdowns dynamically
        ingredients = Ingredient.query.order_by(Ingredient.name).all()
        choices = [
            (ing.id, f"{ing.name} ({ing.source})" if ing.source else ing.name)
            for ing in ingredients
        ]
        for ingredient_form in self.ingredients:
            ingredient_form.ingredient_id.choices = choices

class TargetForm(FlaskForm):
    ratio = DecimalField('Ratio', places=2, validators=[DataRequired()])
    calories = FloatField('Calories', validators=[DataRequired()])
    fat = FloatField('Fat (g)', validators=[DataRequired()])
    protein = FloatField('Protein (g)', validators=[DataRequired()])
    carbs = FloatField('Carbs (g)', validators=[DataRequired()])
    num_main_meals = IntegerField('Number of main meals', validators=[DataRequired(), NumberRange(min=0)])
    num_snacks = IntegerField('Number of snacks', validators=[DataRequired(), NumberRange(min=0)])

    # Optional breakdown for a Meal
    meal_calories = FloatField('Meal Calories', validators=[Optional()])
    meal_fat = FloatField('Meal Fat (g)', validators=[Optional()])
    meal_protein = FloatField('Meal Protein (g)', validators=[Optional()])
    meal_carbs = FloatField('Meal Carbs (g)', validators=[Optional()])

    # Optional breakdown for a Snack
    snack_calories = FloatField('Snack Calories', validators=[Optional()])
    snack_fat = FloatField('Snack Fat (g)', validators=[Optional()])
    snack_protein = FloatField('Snack Protein (g)', validators=[Optional()])
    snack_carbs = FloatField('Snack Carbs (g)', validators=[Optional()])

    submit = SubmitField('Save')
