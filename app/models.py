from datetime import date

from . import db

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # e.g. fat, protein, carb
    units = db.Column(db.String(10), nullable=False)  # g or ml
    percent_fat = db.Column(db.Float)
    percent_carbs = db.Column(db.Float)
    percent_protein = db.Column(db.Float)
    total_calories = db.Column(db.Float)
    source = db.Column(db.String(150))  # New field for source info

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    total_fat = db.Column(db.Float, nullable=True)
    total_carbs = db.Column(db.Float, nullable=True)
    total_protein = db.Column(db.Float, nullable=True)
    total_calories = db.Column(db.Float, nullable=True)
    ratio = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    author = db.Column(db.String)  # new field
    meal_type = db.Column(db.String)  # "breakfast", "main", "snack"
    
    ingredients = db.relationship('RecipeIngredient', back_populates='recipe', cascade='all, delete-orphan')

class RecipeIngredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # in g or ml
    
    fat = db.Column(db.Float, nullable=True)
    carbs = db.Column(db.Float, nullable=True)
    protein = db.Column(db.Float, nullable=True)
    calories = db.Column(db.Float, nullable=True)
    
    recipe = db.relationship('Recipe', back_populates='ingredients')
    ingredient = db.relationship('Ingredient')

class Target(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ratio = db.Column(db.Numeric(4, 2), nullable=False)  # up to 2 decimal places
    calories = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    num_main_meals = db.Column(db.Integer, nullable=False, default=0)
    num_snacks = db.Column(db.Integer, nullable=False, default=0)
    breakdowns = db.relationship('TargetBreakdown', backref='target', lazy=True)

class TargetBreakdown(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item = db.Column(db.String(20), nullable=False)  # e.g. 'Meal' or 'Snack'
    calories = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    target_id = db.Column(db.Integer, db.ForeignKey('target.id'), nullable=True)