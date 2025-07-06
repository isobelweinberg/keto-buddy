from datetime import date, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import db
from .models import Ingredient, Recipe, RecipeIngredient, Target, TargetBreakdown, User, PlannerEntry
from .forms import RecipeForm, TargetForm, LoginForm, RegistrationForm, IngredientForm, PlannerForm, PlannerSlotForm

main = Blueprint('main', __name__)

# @main.route('/')
# def home():
#     return redirect(url_for('main.ingredients'))

@main.route('/')
def index():
    return render_template('index.html', user=current_user)

@main.route('/ingredients', methods=['GET'])
@login_required
def ingredients():
    all_ingredients = Ingredient.query.all()
    form = IngredientForm()
    return render_template('ingredients.html', ingredients=all_ingredients, form=form)

@main.route('/ingredients', methods=['POST'])
@login_required
def add_ingredient():
    form = IngredientForm()
    if form.validate_on_submit():
        new_ingredient = Ingredient(
            name=form.name.data,
            type=form.type.data,
            units=form.units.data,
            percent_fat=form.percent_fat.data,
            percent_carbs=form.percent_carbs.data,
            percent_protein=form.percent_protein.data,
            total_calories=form.total_calories.data,
            source=form.source.data,
            user_id=current_user.id,
        )
        db.session.add(new_ingredient)
        db.session.commit()
        flash(f'Added ingredient: {new_ingredient.name}', 'success')
        return redirect(url_for('main.ingredients'))
    else:
        # On validation failure, re-render the ingredients page with errors and form data
        all_ingredients = Ingredient.query.all()
        return render_template('ingredients.html', ingredients=all_ingredients, form=form)

@main.route('/recipes/new', methods=['GET', 'POST'])
@login_required
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
            notes=form.notes.data,
            user_id=current_user.id,
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
@login_required
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
@login_required
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
            date=date.today(),
            user_id=current_user.id,
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
                target_id=new_target.id,
                user_id=current_user.id,
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
                target_id=new_target.id,
                user_id=current_user.id,
            )
            db.session.add(snack_breakdown)

        db.session.commit()
        return redirect(url_for('main.targets'))

    latest_target = Target.query.order_by(Target.date.desc(), Target.id.desc()).first()

    return render_template('targets.html', target=latest_target, form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        childsname = form.childsname.data
        password = form.password.data
        
        user = User.query.filter_by(childsname=childsname).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        else:
            flash('Invalid child\'s name or password', 'danger')

    return render_template('login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            childsname=form.childsname.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('main.login'))

    return render_template('signup.html', form=form)

@main.route('/planner', methods=['GET','POST'])
@login_required
def planner():
    today = date.today()
    days = [today + timedelta(days=i) for i in range(10)]

    # latest targets
    tgt = Target.query.filter_by(user_id=current_user.id).order_by(Target.date.desc()).first()
    if not tgt:
        flash("Please set your daily targets first.", "warning")
        return redirect(url_for('main.targets'))

    # compute slots per day
    slots = []
    for d in days:
        for m in range(1, tgt.num_main_meals + 1):
            label = {1:'Breakfast',2:'Lunch',3:'Dinner'}.get(m, f'Meal {m}')
            slots.append((d, label))
        for s in range(1, tgt.num_snacks + 1):
            slots.append((d, f'Snack {s}'))

    # fetch recipes for dropdown
    recipes = Recipe.query.filter_by(user_id=current_user.id).all()
    recipe_choices = [ (0, '-- Select --') ] + [(r.id, r.name) for r in recipes]

    # existing entries
    existing = PlannerEntry.query.filter(
        PlannerEntry.user_id == current_user.id,
        PlannerEntry.date.in_(days)
    ).all()
    existing_map = { (e.date, e.slot): e for e in existing }

    # build form
    form = PlannerForm()
    for idx, (d, label) in enumerate(slots):
        field = PlannerSlotForm(prefix=f'slot-{idx}')
        field.recipe_id.choices = recipe_choices + [(-1, 'CUSTOM')]
        key = (d, label)
        if key in existing_map:
            e = existing_map[key]
            if e.recipe_id:
                field.recipe_id.data = e.recipe_id
            elif e.free_text:
                field.recipe_id.data = -1
            else:
                field.recipe_id.data = 0
            field.free_text.data = e.free_text
        setattr(form, f'slot_{idx}', field)

    if form.validate_on_submit():
        for idx, (d, label) in enumerate(slots):
            fld = getattr(form, f'slot_{idx}')
            selected_id = fld.recipe_id.data
            key = (d, label)

            if selected_id == -1:
                # Custom input
                r_id = None
                text = fld.free_text.data.strip() if fld.free_text.data else None
            elif selected_id and selected_id > 0:
                # Selected real recipe
                r_id = selected_id
                text = None
            else:
                # Neither selected nor custom
                r_id = None
                text = None

            entry = existing_map.get(key)
            if entry:
                entry.recipe_id = r_id
                entry.free_text = text
            else:
                entry = PlannerEntry(user_id=current_user.id,
                                     date=d, slot=label,
                                     recipe_id=r_id, free_text=text)
                db.session.add(entry)

        db.session.commit()
        flash("Planner saved!", "success")
        return redirect(url_for('main.planner'))

    return render_template('planner.html', form=form, slots=slots, recipe_map={r.id:r for r in recipes})
