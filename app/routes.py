from datetime import date, timedelta, datetime
from collections import defaultdict

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import db
from .models import (
    Ingredient, Recipe, RecipeIngredient, Target, TargetBreakdown, Users, PlannerEntry, LogEntry, KetoneLogEntry)
from .forms import (
    RecipeForm, CalculatedRecipeForm, TargetForm, LoginForm, RegistrationForm, IngredientForm, PlannerForm, 
    PlannerSlotForm, LogForm, LogSlotForm)
from .seed_db import seed_ingredients

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
    all_ingredients = Ingredient.query.filter_by(unmeasured_ingredient=False).all()
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
            unmeasured_ingredient=False,
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
    
    latest_target = Target.query.order_by(Target.date.desc(), Target.id.desc()).first()

    return render_template('new_recipe.html', form=form, nutrition_data=nutrition_data, target=latest_target)

@main.route('/recipes/new_calculated', methods=['GET', 'POST'])
@login_required
def new_calculated_recipe():
    form = CalculatedRecipeForm()
    form.set_ingredient_choices()

    if form.validate_on_submit():
        recipe = Recipe(
            name=form.name.data,
            author=form.author.data,
            meal_type=form.meal_type.data,
            notes=form.notes.data,
            user_id=current_user.id,
            total_fat=form.total_fat.data,
            total_carbs=form.total_carbs.data,
            total_protein=form.total_protein.data,
            total_calories=form.total_calories.data,
            ratio=form.ratio.data if form.ratio.data else (
                form.total_fat.data / (form.total_carbs.data + form.total_protein.data)
                if (form.total_carbs.data + form.total_protein.data) > 0 else None
            )
        )

        for ingredient_form in form.ingredients.entries:
            ingredient_id = ingredient_form.ingredient_id.data
            amount = ingredient_form.amount.data
            if ingredient_id and amount:
                ri = RecipeIngredient(
                    ingredient_id=ingredient_id,
                    amount=amount,
                    fat=None,
                    carbs=None,
                    protein=None,
                    calories=None
                )
                recipe.ingredients.append(ri)

        db.session.add(recipe)
        db.session.commit()
        flash('Calculated Recipe created successfully!', 'success')
        return redirect(url_for('main.recipes'))

    return render_template('new_calculated_recipe.html', form=form)

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
        
        user = Users.query.filter_by(childsname=childsname).first()
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
        user = Users(
            childsname=form.childsname.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        seed_ingredients(user.id)

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('main.login'))

    return render_template('signup.html', form=form)

@main.route('/planner', methods=['GET', 'POST'])
@login_required
def planner():
    today = date.today()
    days = [today + timedelta(days=i) for i in range(10)]

    # Latest targets
    tgt = Target.query.filter_by(user_id=current_user.id).order_by(Target.date.desc()).first()
    if not tgt:
        flash("Please set your daily targets first.", "warning")
        return redirect(url_for('main.targets'))

    # Compute slots
    slots = []
    for d in days:
        for m in range(1, tgt.num_main_meals + 1):
            label = {1:'Breakfast', 2:'Lunch', 3:'Dinner'}.get(m, f'Meal {m}')
            slots.append((d, label))
        for s in range(1, tgt.num_snacks + 1):
            slots.append((d, f'Snack {s}'))

    grouped_slots = defaultdict(list)
    for d, label in slots:
        grouped_slots[d].append(label)
    slots_by_day = sorted(grouped_slots.items())

    # Map for slot index lookup in template (to get idx by (date, slot_label))
    slot_index_map = {key: idx for idx, key in enumerate(slots)}

    # Fetch recipes for dropdown
    recipes = Recipe.query.filter_by(user_id=current_user.id).all()
    recipe_choices = [(0, '-- Select --')] + [(r.id, r.name) for r in recipes] + [(-1, 'CUSTOM')]

    # Existing entries keyed by (date, slot)
    existing = PlannerEntry.query.filter(
        PlannerEntry.user_id == current_user.id,
        PlannerEntry.date.in_(days)
    ).all()
    existing_map = {(e.date, e.slot): e for e in existing}

    # Create form
    form = PlannerForm()

    # formdata for binding submitted data on POST
    formdata = request.form if request.method == 'POST' else None

    # Dynamically create subforms with prefixes and initial data or POST data
    for idx, (d, label) in enumerate(slots):
        prefix = f'slot-{idx}'
        data = {}
        key = (d, label)
        if key in existing_map:
            e = existing_map[key]
            if e.recipe_id:
                data['recipe_id'] = e.recipe_id
                data['free_text'] = ''
            elif e.free_text:
                data['recipe_id'] = -1
                data['free_text'] = e.free_text
            else:
                data['recipe_id'] = 0
                data['free_text'] = ''
            data['notes'] = e.notes if e.notes else ''
        else:
            data['recipe_id'] = 0
            data['free_text'] = ''
            data['notes'] = ''

        subform = PlannerSlotForm(formdata=formdata, prefix=prefix, data=data)
        subform.recipe_id.choices = recipe_choices

        setattr(form, f'slot_{idx}', subform)

    if form.validate_on_submit():
        for idx, (d, label) in enumerate(slots):
            fld = getattr(form, f'slot_{idx}')
            selected_id = fld.recipe_id.data
            key = (d, label)

            if selected_id == -1:
                r_id = None
                text = fld.free_text.data.strip() if fld.free_text.data else None
            elif selected_id and selected_id > 0:
                r_id = selected_id
                text = None
            else:
                r_id = None
                text = None
            
            notes = fld.notes.data.strip() if fld.notes.data else None

            entry = existing_map.get(key)
            if entry:
                entry.recipe_id = r_id
                entry.free_text = text
                entry.notes = notes
            else:
                entry = PlannerEntry(user_id=current_user.id,
                                     date=d, slot=label,
                                     recipe_id=r_id, free_text=text, notes=notes)
                db.session.add(entry)

        db.session.commit()
        flash("Planner saved!", "success")
        return redirect(url_for('main.planner'))
    
    # Aggregate ingredients for all selected (non-custom) recipes in the form
    ingredient_totals = defaultdict(float)  # key: (ingredient_name, units), value: total_amount
    ingredient_notes = defaultdict(set)    # key: (ingredient_name, units), value: list of notes

    for idx, (d, label) in enumerate(slots):
        fld = getattr(form, f'slot_{idx}')
        selected_id = fld.recipe_id.data

        # Only aggregate if selected recipe is valid and not custom or empty
        if selected_id and selected_id > 0:
            recipe = next((r for r in recipes if r.id == selected_id), None)
            if recipe:
                for ri in recipe.ingredients:
                    key = (ri.ingredient.name, ri.ingredient.units)
                    ingredient_totals[key] += ri.amount
                    # If unmeasured, collect the slot's notes field
                    if ri.ingredient.unmeasured_ingredient:
                        note = fld.notes.data.strip() if fld.notes.data else None
                        if note:
                            ingredient_notes[key].add(note)

    used_notes = set()
    shopping_list = []

    for (name, units), amount in sorted(ingredient_totals.items(), key=lambda x: x[0][0].lower()):
        notes_for_ingredient = []

        for note in sorted(ingredient_notes[(name, units)]):
            if note not in used_notes:
                notes_for_ingredient.append(note)
                used_notes.add(note)

        shopping_list.append({
            'name': name,
            'units': units,
            'amount': amount,
            'notes': "; ".join(notes_for_ingredient) if notes_for_ingredient else None
        })

    return render_template('planner.html',
                           form=form,
                           slots=slots,
                           slots_by_day=slots_by_day,
                           recipe_map={r.id: r for r in recipes},
                           slot_index_map=slot_index_map,
                           shopping_list=shopping_list,)


@main.route('/log', methods=['GET', 'POST'])
@login_required
def log():
    today = date.today()
    days = [today + timedelta(days=i) for i in range(10)]

    tgt = Target.query.filter_by(user_id=current_user.id).order_by(Target.date.desc()).first()
    if not tgt:
        flash("Please set your daily targets first.", "warning")
        return redirect(url_for('main.targets'))

    # Load existing LogEntry records for days
    existing = LogEntry.query.filter(
        LogEntry.user_id == current_user.id,
        LogEntry.date.in_(days)
    ).all()
    existing_map = {(e.date, e.slot): e for e in existing}

    # Load existing KetoneLogEntry records for days
    existing_ketones = KetoneLogEntry.query.filter(
        KetoneLogEntry.user_id == current_user.id,
        KetoneLogEntry.date.in_(days)
    ).order_by(KetoneLogEntry.date, KetoneLogEntry.time).all()

    # Group ketone entries by date for display
    ketones_by_day = defaultdict(list)
    for k in existing_ketones:
        ketones_by_day[k.date].append(k)
    print(f"Ketones by day existing: {ketones_by_day}")

    # for day, ketone_list in ketones_by_day.items():
    #     for ketone in ketone_list:
    #         print(ketone.date)
    #         print((type(ketone.time)))

    # Compute default slots for meals/snacks
    slots = []
    for d in days:
        for m in range(1, tgt.num_main_meals + 1):
            label = {1: 'Breakfast', 2: 'Lunch', 3: 'Dinner'}.get(m, f'Meal {m}')
            slots.append((d, label))
        for s in range(1, tgt.num_snacks + 1):
            slots.append((d, f'Snack {s}'))
    # print(f"Default slots: {slots}")

    # Add any existing extra meal/snack slots
    for e in existing:
        if e.slot.startswith("Extra Meal") or e.slot.startswith("Extra Snack"):
            slots.append((e.date, e.slot))

    grouped_slots = defaultdict(list)
    for d, label in slots:
        grouped_slots[d].append(label)
    slots_by_day = sorted(grouped_slots.items())
    slot_index_map = {key: idx for idx, key in enumerate(slots)}

    # Recipes for choices
    recipes = Recipe.query.filter_by(user_id=current_user.id).all()
    recipe_choices = [(0, '-- Select --')] + [(r.id, r.name) for r in recipes] + [(-1, 'CUSTOM')]

    def get_latest_planner_entry(user_id, date_, slot):
        return PlannerEntry.query.filter(
            PlannerEntry.user_id == user_id,
            PlannerEntry.slot == slot,
            PlannerEntry.date <= date_
        ).order_by(PlannerEntry.date.desc()).first()

    # Instantiate meal log form
    form = LogForm()
    formdata = request.form if request.method == 'POST' else None
    print(f"Form data: {formdata}")

    # Create meal slot subforms dynamically
    for idx, (d, label) in enumerate(slots):
        prefix = f'slot-{idx}'
        if formdata:
            subform = LogSlotForm(formdata=formdata, prefix=prefix)
        else:
            key = (d, label)
            data = {}
            if key in existing_map:
                e = existing_map[key]
                if e.recipe_id:
                    data['recipe_id'] = e.recipe_id
                    data['free_text'] = ''
                elif e.free_text:
                    data['recipe_id'] = -1
                    data['free_text'] = e.free_text
                else:
                    data['recipe_id'] = 0
                    data['free_text'] = ''
                data['percent_eaten'] = e.percent_eaten or 100
                data['notes'] = e.notes or ''
            else:
                planner = get_latest_planner_entry(current_user.id, d, label)
                if planner:
                    if planner.recipe_id:
                        data['recipe_id'] = planner.recipe_id
                        data['free_text'] = ''
                    elif planner.free_text:
                        data['recipe_id'] = -1
                        data['free_text'] = planner.free_text
                data['percent_eaten'] = 100
                data['notes'] = ''
            subform = LogSlotForm(prefix=prefix, data=data)

        subform.recipe_id.choices = recipe_choices
        setattr(form, f'slot_{idx}', subform)

    # On POST: handle adding extra meal/snack button clicks
    if request.method == 'POST':
        action = request.form.get('action')
        if action:
            if action.startswith('add_meal_') or action.startswith('add_snack_'):
                date_str = action.split('_')[-1]
                d = date.fromisoformat(date_str)
                prefix = 'Extra Meal' if 'meal' in action else 'Extra Snack'
                existing_slots = [slot for (day, slot) in existing_map if day == d and slot.startswith(prefix)]
                next_idx = len(existing_slots) + 1
                slot_label = f'{prefix} {next_idx}'

                if (d, slot_label) not in existing_map:
                    new_entry = LogEntry(
                        user_id=current_user.id,
                        date=d,
                        slot=slot_label,
                        recipe_id=None,
                        free_text=None,
                        percent_eaten=100,
                        notes=''
                    )
                    db.session.add(new_entry)
                    db.session.commit()
                return redirect(url_for('main.log'))

        # Handle "Save Log" submission including ketones
        print("Got to save log")
        print(f"Form errors: {form.errors}")
        print(f"Request method: {request.method}")
        print(f"Form is submitted: {form.is_submitted()}")
        print(f"Request form data: {request.form}")
        print("Manual validation:", form.validate())
        # for ketone_entry in form.ketone_entries:
        #     print(f"Ketone entry data: {ketone_entry.form.data}")

        from flask_wtf.csrf import CSRFError
        try:
            valid = form.validate()
        except CSRFError as e:
            print("CSRF validation error:", e.description)
            valid = False
        print("Form validate() result:", valid)
        print("Form errors:", form.errors)

        for i in range(10):
            print(request.form.get(f'ketone_entries-{i}-time'))

        if form.validate_on_submit():
            print(f"form data 2: {formdata}")
            print(f"form ketone entries: {form.ketone_entries.entries}")
            # Save meal log entries
            for idx, (d, label) in enumerate(slots):
                fld = getattr(form, f'slot_{idx}')
                selected_id = fld.recipe_id.data
                key = (d, label)

                if selected_id == -1:
                    r_id = -1
                    text = fld.free_text.data.strip() if fld.free_text.data else None
                elif selected_id and selected_id > 0:
                    r_id = selected_id
                    text = None
                else:
                    r_id = None
                    text = None

                percent = fld.percent_eaten.data if fld.percent_eaten.data is not None else 100
                notes = fld.notes.data.strip() if fld.notes.data else None

                entry = existing_map.get(key)
                if entry:
                    entry.recipe_id = r_id
                    entry.free_text = text
                    entry.percent_eaten = percent
                    entry.notes = notes
                else:
                    entry = LogEntry(
                        user_id=current_user.id,
                        date=d,
                        slot=label,
                        recipe_id=r_id,
                        free_text=text,
                        percent_eaten=percent,
                        notes=notes
                    )
                    db.session.add(entry)

            ketone_entries = []
            for entry in form.ketone_entries.entries:
                d = date.fromisoformat(entry.form.date.data)
                t = entry.form.time.data

                ketones = entry.form.ketone_level.data
                glucose = entry.form.glucose_level.data

                if ketones is None and glucose is None:
                    continue

                ketone_entries.append((d, t, ketones, glucose))


            print(f"ketone_entries: {ketone_entries}")

            # Save ketone log entries, overwrinting existing ones that have the same date and time
            for d, t, ketones, glucose in ketone_entries:
                existing_entry = KetoneLogEntry.query.filter_by(
                    user_id=current_user.id,
                    date=d,
                    time=t
                ).first()
                print(f"Existing entry: {existing_entry}")
                if ketones is None and glucose is None:
                    continue
                if existing_entry:
                    existing_entry.ketone_level = ketones
                    existing_entry.glucose_level = glucose
                else:
                    new_k = KetoneLogEntry(
                        user_id=current_user.id,
                        date=d,
                        time=t,
                        ketone_level=ketones,
                        glucose_level=glucose
                    )
                    db.session.add(new_k)

            # Handle deletion of ketone entries not submitted in the form (due to the remove button)
            submitted_pairs = set()
            idx = 0

            # Collect all (date, time) pairs submitted
            while True:
                date_key = f'ketone_entries-{idx}-date'
                time_key = f'ketone_entries-{idx}-time'
                if date_key not in request.form or time_key not in request.form:
                    break

                date_str = request.form.get(date_key)
                time_str = request.form.get(time_key)
                if not (date_str and time_str):
                    idx += 1
                    continue

                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                time_obj = datetime.strptime(time_str, '%H:%M').time()
                submitted_pairs.add((date_obj, time_obj))

                idx += 1

            # Now fetch all existing entries for the user
            existing_entries = KetoneLogEntry.query.filter_by(user_id=current_user.id).all()

            # Delete any existing entries NOT in submitted form
            for entry in existing_entries:
                if (entry.date, entry.time) not in submitted_pairs:
                    db.session.delete(entry)

            db.session.commit()
            flash("Log saved!", "success")
            return redirect(url_for('main.log'))

    return render_template('log.html',
                           form=form,
                           slots=slots,
                           slots_by_day=slots_by_day,
                           recipe_map={r.id: r for r in recipes},
                           slot_index_map=slot_index_map,
                           ketones_by_day=ketones_by_day)

@main.route('/fruit_substitutions', methods=['GET'])
@login_required
def fruit_substitutions():
    return render_template('fruit_substitutions.html')

@main.route('/veg_substitutions', methods=['GET'])
@login_required
def veg_substitutions():
    return render_template('veg_substitutions.html')