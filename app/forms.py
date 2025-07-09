from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, FloatField, SelectField, FieldList, FormField, SubmitField, 
    DecimalField, IntegerField, PasswordField, EmailField, RadioField, TimeField, HiddenField)
from wtforms.validators import DataRequired, NumberRange, Optional, Email, EqualTo, ValidationError

from .models import Ingredient, User

class RecipeIngredientForm(FlaskForm):
    ingredient_id = SelectField('Ingredient', coerce=int, validators=[DataRequired()])
    amount = FloatField('Amount (g or ml)', validators=[DataRequired(), NumberRange(min=0.01)])

class IngredientForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    source = StringField('Source', validators=[Optional()])
    type = SelectField('Type', choices=[
        ('', 'Choose...'),
        ('vegetables', 'Vegetables'),
        ('fruit', 'Fruit'),
        ('nuts_seeds', 'Nuts and seeds'),
        ('dairy', 'Dairy'),
        ('fats_oils', 'Fats and oils'),
        ('carbohydrates', 'Carbohydrates'),
        ('meats_fishes', 'Meats and fishes')
    ], validators=[DataRequired()])
    units = RadioField('Units', choices=[
        ('g', 'Grams (g)'),
        ('ml', 'Milliliters (ml)')
    ], validators=[DataRequired()])
    percent_fat = FloatField('Fat %', validators=[DataRequired()])
    percent_carbs = FloatField('Carbohydrate %', validators=[DataRequired()])
    percent_protein = FloatField('Protein %', validators=[DataRequired()])
    total_calories = FloatField('Calories per 100g or ml', validators=[DataRequired()], render_kw={'readonly': True})

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
        ingredients = Ingredient.query.filter_by(unmeasured_ingredient=False).order_by(Ingredient.name).all()
        choices = [
            (ing.id, f"{ing.name} ({ing.source})" if ing.source else ing.name)
            for ing in ingredients
        ]
        for ingredient_form in self.ingredients:
            ingredient_form.ingredient_id.choices = choices

class CalculatedRecipeForm(FlaskForm):
    name = StringField('Recipe Name', validators=[DataRequired()])
    notes = TextAreaField('Notes')
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
    ingredients = FieldList(FormField(RecipeIngredientForm), min_entries=1)
    
    total_fat = FloatField('Total Fat (g)', validators=[DataRequired()])
    total_carbs = FloatField('Total Carbs (g)', validators=[DataRequired()])
    total_protein = FloatField('Total Protein (g)', validators=[DataRequired()])
    total_calories = FloatField('Total Calories', validators=[DataRequired()])
    ratio = FloatField('Ketogenic Ratio', validators=[DataRequired()])
    
    submit = SubmitField('Create Recipe')

    def set_ingredient_choices(self):
        choices = [(ing.id, ing.name) for ing in Ingredient.query.order_by(Ingredient.name).all()]
        for entry in self.ingredients.entries:
            entry.form.ingredient_id.choices = choices

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

class LoginForm(FlaskForm):
    childsname = StringField('Child\'s Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    childsname = StringField('Child\'s Name', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email is already registered.')
        
class PlannerSlotForm(FlaskForm):
    recipe_id = SelectField('Recipe', coerce=int, validators=[Optional()])
    free_text = StringField('Or enter custom', validators=[Optional()])
    notes = TextAreaField('Notes', render_kw={"rows":2, "cols":30}, validators=[Optional()])

class PlannerForm(FlaskForm):
    submit = SubmitField('Save Planner')

class LogSlotForm(FlaskForm):
    recipe_id = SelectField('Recipe', coerce=int)
    free_text = StringField('Custom meal')
    percent_eaten = FloatField('% eaten', default=100)
    notes = TextAreaField('Notes', render_kw={"rows":2, "cols":30})

class KetoneEntryForm(FlaskForm):
    date = HiddenField('Date')  # store date as ISO string
    time = TimeField('Time')
    ketone_level = FloatField('Ketones (mmol/L)', validators=[Optional()])
    glucose_level = FloatField('Glucose (mmol/L)', validators=[Optional()])

class LogForm(FlaskForm):
    submit = SubmitField('Save Log')
    # slot_N will be added dynamically in the view
    ketone_entries = FieldList(FormField(KetoneEntryForm), min_entries=0)