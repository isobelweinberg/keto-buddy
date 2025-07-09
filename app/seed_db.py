from . import db
from .models import Ingredient

def seed_ingredients(user_id):
    special_ingredients = [
        {
            'user_id': user_id,
            'name': 'Group 1 Vegetables',
            'type': 'vegetables',
            'units': 'g',
            'unmeasured_ingredient': True,
        },
        {
            'user_id': user_id,
            'name': 'Group 2 Vegetables',
            'type': 'vegetables',
            'units': 'g',
            'unmeasured_ingredient': True,
        },
        {
            'user_id': user_id,
            'name': 'Group 3 Vegetables',
            'type': 'vegetables',
            'units': 'g',
            'unmeasured_ingredient': True,
        },
        {
            'user_id': user_id,
            'name': 'Group A Fruit',
            'type': 'fruit',
            'units': 'g',
            'unmeasured_ingredient': True,
        },
        {
            'user_id': user_id,
            'name': 'Group B Fruit',
            'type': 'fruit',
            'units': 'g',
            'unmeasured_ingredient': True,
        },
        {
            'user_id': user_id,
            'name': 'Group C Fruit',
            'type': 'fruit',
            'units': 'g',
            'unmeasured_ingredient': True,
        },
    ]

    for item in special_ingredients:
        exists = Ingredient.query.filter_by(name=item['name']).first()
        if not exists:
            ingredient = Ingredient(**item)
            db.session.add(ingredient)

    db.session.commit()

if __name__ == '__main__':
    seed_ingredients()
