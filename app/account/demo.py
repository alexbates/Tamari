from flask import render_template
from app import app, db
from app.models import User, Recipe, NutritionalInfo, Category, Shoplist, Listitem, MealRecipe
import os
from config import Config

# This python file is used to reconstruct the data in the Demo account.
# In Tamari instances, a Demo account can be created using the email address 'demo@tamariapp.com'.
# When creating the demo account, be aware that the password cannot easily be changed.
# At time of creation, there will be no recipes.
# However, after 30 minutes, account data including 12 recipes will be added and replaced every 30 minutes.
# To provide a banner with the Demo credentials on the Login page, modify the login.html template.
# Find the HTML comment in the template and uncomment it.

def reset_demo_account():
    with app.app_context():
        # Get user and handle if user doesn't exist
        user = User.query.filter_by(email='demo@tamariapp.com').first()
        if user:
            # Delete all recipes belonging to the current user
            recipes = Recipe.query.filter_by(user_id=user.id).all()
            # When deleting photos from recipe-photos directory, the photos are only deleted
            # if not one of the defaults
            defaults = ['default01.png', 'default02.png', 'default03.png', 'default04.png', 'default05.png', 'default06.png', 'default07.png',
                'default08.png', 'default09.png', 'default10.png', 'default11.png', 'default12.png', 'default13.png', 'default14.png',
                'default15.png', 'default16.png', 'default17.png', 'default18.png', 'default19.png', 'default20.png', 'default21.png',
                'default22.png', 'default23.png', 'default24.png', 'default25.png', 'default26.png', 'default27.png', 'demo1.jpg', 'demo2.jpg',
                'demo3.jpg', 'demo4.jpg', 'demo5.jpg', 'demo6.jpg', 'demo7.jpg', 'demo8.jpg', 'demo9.jpg', 'demo10.jpg', 'demo11.jpg',
                'demo12.jpg']
            for recipe in recipes:
                fullpath = app.config['UPLOAD_FOLDER'] + '/' + recipe.photo
                if recipe.photo not in defaults:
                    try:
                        os.remove(fullpath)
                    except:
                        pass
                db.session.delete(recipe)
            # Delete all other records belonging to the demo user
            nutritional_infos = NutritionalInfo.query.filter_by(user_id=user.id).all()
            for nutritional_info in nutritional_infos:
                db.session.delete(nutritional_info)
            categories = Category.query.filter_by(user_id=user.id).all()
            for category in categories:
                db.session.delete(category)
            shoplists = Shoplist.query.filter_by(user_id=user.id).all()
            for shoplist in shoplists:
                db.session.delete(shoplist)
            listitems = Listitem.query.filter_by(user_id=user.id).all()
            for listitem in listitems:
                db.session.delete(listitem)
            mealrecipes = MealRecipe.query.filter_by(user_id=user.id).all()
            for mealrecipe in mealrecipes:
                db.session.delete(mealrecipe)
            # Commit deleted data
            db.session.commit()
            # Add three categories
            cats = ['Miscellaneous', 'Entrees', 'Sides']
                for cat in cats:
                    hex_valid = 0
                    while hex_valid == 0:
                        hex_string = secrets.token_hex(4)
                        hex_exist = Category.query.filter_by(hex_id=hex_string).first()
                        if hex_exist is None:
                            hex_valid = 1
                    new_cat = Category(hex_id=hex_string, label=cat, user=user)
                    db.session.add(new_cat)
            # Add shopping lists
            lists = ['Miscellaneous', 'Publix']
                for list in lists:
                    hex_valid2 = 0
                    while hex_valid2 == 0:
                        hex_string2 = secrets.token_hex(4)
                        hex_exist2 = Shoplist.query.filter_by(hex_id=hex_string2).first()
                        if hex_exist2 is None:
                            hex_valid2 = 1
                    new_list = Shoplist(hex_id=hex_string2, label=list, user=user)
                    db.session.add(new_list)
            # Commit new categories and shopping lists
            db.session.commit()
            # Add Recipe 1 to Demo account
            recipe_1_title = 'Balsamic Bacon Brussel Sprouts'
            recipe_1_description = 'Elevate your Brussels sprouts game with this mouthwatering recipe that combines the rich flavors of balsamic vinegar and savory bacon with a touch of sweetness from honey. Perfect as a side dish or a standalone delight, these Balsamic Bacon Brussels Sprouts will have everyone coming back for seconds. Inspired by Trader Joes shaved brussel sprouts recipe.'
            recipe_1_ingredients = '1 package of whole brussel sprouts\n3 pieces bacon\nolive oil\n1/3 cup balsamic vinegar\n1/3 cup water\nsalt and pepper\nhoney'
            recipe_1_instructions = 'Cook 3 pieces of bacon in medium frying pan. Remove and break into small pieces.\nCut brussel sprouts into halves or thirds, depending on the size. Cook brussel sprouts in bacon grease with olive oil.\nAfter browned, season with salt and pepper. Add water and vinegar, cook covered for about 5 minutes.\nMix in bacon pieces. Drizzle with honey and serve.'
            recipe_1 = Recipe(hex_id='01c7a9', title=recipe_1_title, category='Sides', photo='demo1.jpg', description=recipe_1_description,
                url='', servings=4, prep_time=5, cook_time=30, total_time=35, ingredients=recipe_1_ingredients, instructions=recipe_1_instructions,
                favorite=0, public=0, user_id=user.id)
            db.session.add(recipe_1)
            # Add Recipe 2 to Demo account
            recipe_2_title = 'Carrabba’s-Style Spiedino Di Mare Scallops'
            recipe_2_description = 'Transport yourself to the vibrant flavors of Italy with this exquisite recipe inspired by Carrabba’s Spiedino Di Mare. Featuring succulent wild-caught scallops, seasoned breadcrumbs, zesty lemon butter, and fragrant Italian herbs, each bite is a symphony of Mediterranean flavors.'
            recipe_2_ingredients = '1.5 lb wild caught scallops\n1/3 cup breadcrumbs\n1 Tbsp Italian seasoning\nOlive oil\nSalt & pepper\nParsley\n2 oz melted lemon butter'
            recipe_2_instructions = 'Place scallops on small wooden skewers. Sprinkle salt and pepper on both sides of scallops. Mix bread crumbs, Italian seasoning, and parsley in glass baking dish. Coat scallops with olive oil. Dip scallop skewers in bread crumb mix.\nCook scallops for 2 minutes on each side in skillet on medium-high heat. Likely have to do two batches.'
            recipe_2 = Recipe(hex_id='02c7a9', title=recipe_2_title, category='Entrees', photo='demo2.jpg', description=recipe_2_description,
                url='', servings=4, prep_time=20, cook_time=8, total_time=28, ingredients=recipe_2_ingredients, instructions=recipe_2_instructions,
                favorite=0, public=0, user_id=user.id)
            db.session.add(recipe_2)
            # Add Recipe 3 to Demo account
            recipe_3_title = 'Cheesy Broccoli Cassrole'
            recipe_3_description = 'Low carb broccoli casserole with cheese and almond flour.'
            recipe_3_url = 'https://www.flavcity.com/broccoli-casserole/'
            recipe_3_ingredients = '7 oz broccoli florets\n5 green onions sliced\n1 cup almond flour\n¼ cup tapioca starch\n1 teaspoon salt\nA few cracks black pepper\n1 teaspoon baking powder\n½ cup almond milk\n¼ cup extra virgin olive oil\n2 eggs\n1 tablespoon chopped dill optional\n1 cup finely grated parmesan'
            recipe_3_instructions = 'Preheat oven to 375F.\nBring a small pot of water to boil, and add a pinch of salt. Add the broccoli florets and once the water is boiling again cook for 1 minute. Drain the broccoli and set aside to cool.\nIn a small pot or pan, sauté 5 green onions with a little olive oil and a pinch of salt for 3 minutes. Set aside to cool.\nIn a large bowl add the almond flour, tapioca starch, salt, pepper, baking powder and mix well with a whisk. Add the milk, olive oil, and mix well. Set aside for 5 minutes to hydrate.\nLightly whisk the eggs and add to the four mixture, mix well.. Roughly chop the blanched broccoli and add to the flour mixture together with the sautéed green onions, dill and a cup of finely grated parmesan cheese.\nStir everything together, and pour into a greased baking dish (the one I used is about 8.5 x 6.5 inches). Top off with some more parmesan and bake at 375F for about 45-50 minutes, until the top looks golden brown. Let cool down for 15-25 minutes and enjoy!'
            recipe_3 = Recipe(hex_id='03c7a9', title=recipe_3_title, category='Sides', photo='demo3.jpg', description=recipe_3_description,
                url=recipe_3_url, servings=4, prep_time=15, cook_time=50, total_time=65, ingredients=recipe_3_ingredients, instructions=recipe_3_instructions,
                favorite=0, public=0, user_id=user.id)
            db.session.add(recipe_3)
            # Add Recipe 4 to Demo account
            recipe_4_title = 'Chicken Divan'
            recipe_4_description = 'A cheesy chicken casserole dish that makes for a tasty and quick dinner.'
            recipe_4_ingredients = '3 cups pulled chicken\nbroccoli\n1 can cream of chicken soup\nmayonnaise about equivalent in volume to cream of chicken soup\ncurry powder\nsalt & pepper\ncheddar cheese'
            recipe_4_instructions = 'Spread chicken in glass baking dish. Cut and steam broccoli. Pour over chicken. Mix cream of chicken soup, mayo, salt, pepper, and curry powder in bowl. Pour over broccoli. Cover top with shredded cheddar cheese.\nCook at 350 to 400 for 25 minutes.'
            recipe_4 = Recipe(hex_id='04c7a9', title=recipe_4_title, category='Entrees', photo='demo4.jpg', description=recipe_4_description,
                url='', servings=4, prep_time=20, cook_time=25, total_time=45, ingredients=recipe_4_ingredients, instructions=recipe_4_instructions,
                favorite=0, public=0, user_id=user.id)
            db.session.add(recipe_4)
            # Add Recipe 5 to Demo account
            recipe_5_title = 'Cilantro Lime Sauce for Tacos'
            recipe_5_description = 'Perfect for shrimp, chicken, tacos, carrots, celery, and wings. Alternatively, it can be used as a salad dressing.'
            recipe_5_ingredients = '1/2 cup nonfat greek yogurt\n6 tablespoons fresh cilantro leaves chopped\n1 teaspoon lime zest (zest of one lime)\n1 tablespoon lime juice\n1/2 tablespoon olive oil\n1/2 teaspoon pepper\n1/2 teaspoon salt'
            recipe_5_instructions = 'In a food processor or blender, puree all ingredients until smooth.'
            recipe_5 = Recipe(hex_id='05c7a9', title=recipe_5_title, category='Miscellaneous', photo='demo5.jpg', description=recipe_5_description,
                url='', servings=4, prep_time=5, total_time=5, ingredients=recipe_5_ingredients, instructions=recipe_5_instructions,
                favorite=0, public=0, user_id=user.id)
            db.session.add(recipe_5)
            # Add Recipe 6 to Demo account
            recipe_6_title = 'Crab Cakes'
            recipe_6_description = 'Golden brown crab cakes with almond flour breadcrumb. Low carb and keto crab crab cakes.'
            recipe_6_ingredients = '1 pound lump crab meat (3 cans)\n3/4 cup almond flour\n1/4 cup avocado oil mayo\n1.5 teaspoons stone ground or dijon mustard\nZest and juice of half a lemon\n1 tablespoon fresh chives (finely sliced)\nUnrefined salt & pepper\nGhee or avocado oil'
            recipe_6_instructions = 'For the crab cakes, add the mayo, mustard, lemon zest & juice, chives, ¼ teaspoon salt, and a few cracks of pepper to a large bowl. Add the lump crab meat, ½ teaspoon salt, couple cracks of pepper, and the almond flour. Gently mix and let the crab cake mixture sit for 15-30 minutes in the fridge to firm up.\nTo cook the crab cakes, preheat a non-stick ceramic pan over medium heat with enough ghee or avocado oil to cover the bottom of the pan. Once hot, form the crab cakes and cook until deep golden brown on each side, about 4-5 minutes per side.\nServe the crab cakes optionally with tartar sauce and enjoy!'
            recipe_6 = Recipe(hex_id='06c7a9', title=recipe_6_title, category='Entrees', photo='demo6.jpg', description=recipe_6_description,
                url='', servings=4, prep_time=20, cook_time=10, total_time=30, ingredients=recipe_6_ingredients, instructions=recipe_6_instructions,
                favorite=1, public=0, user_id=user.id)
            db.session.add(recipe_6)
            # Add Recipe 7 to Demo account
            recipe_7_title = 'Honey & Coconut Granola'
            recipe_7_description = 'Surprise! This recipe is secretly paleo. There are no oats. Instead there are a ton of nuts and seeds to compensate, meaning the granola is crunchier, more satisfying, and filled with healthy fats.'
            recipe_7_ingredients = '(Use half these amounts)\n1 cup almonds\n1 cup pecans\n1 cup dried cranberries\n½ cup pumpkin seeds\n½ cup unsweetened coconut flakes\n¼ cup flax seeds\n¼ cup sunflower seeds\n¼ cup sesame seeds\n1 teaspoon kosher salt\n1 teaspoon ground cinnamon\n½ teaspoon ground nutmeg\n3 tablespoons melted coconut oil\n¼ cup honey\n1 teaspoon pure vanilla extract'
            recipe_7_instructions = 'In a large bowl, combine almonds, pecans, cranberries, pumpkin seeds, coconut, flax seeds, sunflower seeds, sesame seeds, salt, cinnamon, and nutmeg.\nIn a small bowl, whisk together oil, honey, and vanilla. Pour over seeds and toss to coat.\nLine air fryer basket with parchment paper, then add one-third to one-half of mixture (depending on the size of your air fryer). Cook at 350°, stirring halfway through, until granola is golden and crispy, 12 to 14 minutes.\nRepeat with remaining granola mixture.'
            recipe_7 = Recipe(hex_id='07c7a9', title=recipe_7_title, category='Sides', photo='demo7.jpg', description=recipe_7_description,
                url='', servings=4, prep_time=20, cook_time=13, total_time=33, ingredients=recipe_7_ingredients, instructions=recipe_7_instructions,
                favorite=0, public=0, user_id=user.id)
            db.session.add(recipe_7)
            # Add Recipe 8 to Demo account
            recipe_8_title = 'Creamy Chicken Tortilla Bake Casserole'
            recipe_8_description = ''
            recipe_8_ingredients = '1 tablespoon butter\n½ cup chopped onion\n1 (10.75 ounce) can condensed cream of chicken soup\n1 cup sour cream\n¼ teaspoon ground cumin\n8 (6 inch) corn tortillas\n2 (4 ounce) cans chopped green chiles, drained\n3 cups cubed, cooked chicken\n1 (8 ounce) package shredded Cheddar cheese\n1 (8 ounce) package shredded Monterey Jack cheese'
            recipe_8_instructions = 'Melt butter in a large skillet over medium heat; cook and stir onion until tender and translucent, about 5 minutes.\nMix in cream of chicken soup, sour cream, and cumin.\nGrease a 9x12-inch microwave-safe baking dish and place 4 tortillas in a layer into the bottom of the dish.\nTop with 1 can green chilies, half the chicken, half the soup mix, half the Cheddar cheese, and half the Monterey Jack cheese.\nRepeat layers, ending with Monterey Jack cheese.\nCook uncovered in oven at 375 F for 30 minutes.'
            recipe_8 = Recipe(hex_id='08c7a9', title=recipe_8_title, category='Entrees', photo='demo8.jpg', description=recipe_8_description,
                url='', servings=4, prep_time=25, cook_time=30, total_time=55, ingredients=recipe_8_ingredients, instructions=recipe_8_instructions,
                favorite=1, public=0, user_id=user.id)
            db.session.add(recipe_8)
            # Add Recipe 9 to Demo account
            recipe_9_title = 'Ground Turkey Skillet with Green Beans'
            recipe_9_description = 'A gluten-free and low-carb Ground Turkey Skillet with Green Beans recipe that is definitely easy-to-make and a tasty meal for your family dinner.'
            recipe_9_ingredients = '2 tablespoons extra virgin olive oil\n1 pound free-range extra-lean ground turkey\n1 teaspoon garlic (minced)\n½ cup onions (diced)\n½ cup yellow bell pepper (diced)\n1½ cup green beans (chopped)\n¾ cup homemade tomato sauce or any other sauce of your preference\nSalt and ground fresh black pepper\nA pinch of crushed red pepper'
            recipe_9_instructions = 'Melt butter in a large skillet over medium heat; cook and stir onion until tender and translucent, about 5 minutes.\nMix in cream of chicken soup, sour cream, and cumin.\nGrease a 9x12-inch microwave-safe baking dish and place 4 tortillas in a layer into the bottom of the dish.\nTop with 1 can green chilies, half the chicken, half the soup mix, half the Cheddar cheese, and half the Monterey Jack cheese.\nRepeat layers, ending with Monterey Jack cheese.\nCook uncovered in oven at 375 F for 30 minutes.'
            recipe_9 = Recipe(hex_id='09c7a9', title=recipe_9_title, category='Entrees', photo='demo9.jpg', description=recipe_9_description,
                url='', servings=4, prep_time=5, cook_time=20, total_time=25, ingredients=recipe_9_ingredients, instructions=recipe_9_instructions,
                favorite=0, public=0, user_id=user.id)
            db.session.add(recipe_9)
            # Add Recipe 10 to Demo account
            recipe_10_title = 'Green Bean Casserole'
            recipe_10_description = 'The recipe on back of crispy fried onion container calls for 2 ounces (~2 cans) of green beans. It is too watery like that, so we used 3 cans.'
            recipe_10_ingredients = '3 cans of green beans\n1 can Campbell’s cream of mushroom soup\n3/4 cup Milk\n1/8 tsp Black Pepper\n1 1/3 cups Frenchs Fried onions'
            recipe_10_instructions = 'Preheat oven to 350°F\nMix soup, milk and pepper in mixing bowl. Stir in beans and 2/3 cup Crispy Fried Onions.\nPour mixture into 1 1/2 quart baking dish. Top with remaining 2/3 cup Onions.\nBake for 30 minutes or until hot. Then stir.\nBake 5 minutes or until onions are golden brown.'
            recipe_10 = Recipe(hex_id='10c7a9', title=recipe_10_title, category='Sides', photo='demo10.jpg', description=recipe_10_description,
                url='', servings=4, prep_time=15, cook_time=35, total_time=50, ingredients=recipe_10_ingredients, instructions=recipe_10_instructions,
                favorite=0, public=0, user_id=user.id)
            db.session.add(recipe_10)
            # Add Recipe 11 to Demo account
            recipe_11_title = 'Parmesan Zucchini Fries'
            recipe_11_description = ''
            recipe_11_ingredients = 'cooking spray\n2 eggs\n3/4 cup grated Parmesan cheese\n1 tablespoon dried mixed herbs\n1 1/2 teaspoons garlic powder\n1 teaspoon paprika\n1/2 teaspoon ground black pepper\n2 pounds zucchinis, cut into 1/2-inch French fry strips'
            recipe_11_instructions = 'Preheat oven to 425 degrees F. Line a baking sheet with aluminum foil and spray with cooking spray.\nWhisk eggs in a shallow bowl. Combine Parmesan cheese, mixed herbs, garlic powder, paprika, and pepper in a separate shallow bowl; mix well.\nDip zucchini fries into beaten eggs, in batches; shake to remove excess, and roll in Parmesan mixture until fully coated. Place on the prepared baking sheet.\nBake in the preheated oven, turning once, until golden and crispy, 30 to 35 minutes.'
            recipe_11 = Recipe(hex_id='11c7a9', title=recipe_11_title, category='Sides', photo='demo11.jpg', description=recipe_11_description,
                url='', servings=4, prep_time=15, cook_time=30, total_time=45, ingredients=recipe_11_ingredients, instructions=recipe_11_instructions,
                favorite=0, public=0, user_id=user.id)
            db.session.add(recipe_11)
            # Add Recipe 12 to Demo account
            recipe_12_title = 'Perfect Steak Butter'
            recipe_12_description = 'Easy and delicious steak butter (also known as compound butter) takes just minutes to prepare and takes hamburger steak, t-bones, strips, rib-eyes, porterhouse and filet mignon to an all new high.'
            recipe_12_ingredients = '1 stick of butter softened\n2 cloves garlic crushed (optional)\n2 tablespoons fresh Italian parsley minced\nDill weed to taste\n1/4 teaspoon sea salt\n1/4 teaspoon fresh ground black pepper\n1 teaspoon lemon zest (or lemon juice)'
            recipe_12_instructions = 'Soften butter in the microwave, dont melt it completely.\nMix ingredients in small bowl.'
            recipe_12 = Recipe(hex_id='12c7a9', title=recipe_12_title, category='Miscellaneous', photo='demo12.jpg', description=recipe_12_description,
                url='', servings=4, prep_time=5, total_time=5, ingredients=recipe_12_ingredients, instructions=recipe_12_instructions,
                favorite=0, public=0, user_id=user.id)
            db.session.add(recipe_12)
            # Add 12 recipes to database
            db.session.commit()
            # Add items to shopping lists
            try:
                list_1 = user.shop_lists.filter_by(label='Miscellaneous').first()
                list_2 = user.shop_lists.filter_by(label='Publix').first()
                item_1 = Listitem(hex_id='01d924ee', item='Honey', user_id=user.id, complete=0, list_id=list_1.id)
                db.session.add(item_1)
                item_2 = Listitem(hex_id='02d924ee', item='1 pound lump crab meat (3 cans)', user_id=user.id, complete=0, list_id=list_1.id)
                db.session.add(item_2)
                item_3 = Listitem(hex_id='03d924ee', item='Almond Flour', user_id=user.id, complete=0, list_id=list_1.id)
                db.session.add(item_3)
                item_4 = Listitem(hex_id='04d924ee', item='Avocado oil', user_id=user.id, complete=0, list_id=list_1.id)
                db.session.add(item_4)
                item_5 = Listitem(hex_id='05d924ee', item='Grated Parmesan', user_id=user.id, complete=0, list_id=list_1.id)
                db.session.add(item_5)
                item_6 = Listitem(hex_id='06d924ee', item='(3) Lemons', user_id=user.id, complete=0, list_id=list_1.id)
                db.session.add(item_6)
                item_7 = Listitem(hex_id='07d924ee', item='Brussel sprouts', user_id=user.id, complete=1, list_id=list_1.id)
                db.session.add(item_7)
                item_8 = Listitem(hex_id='08d924ee', item='Balsamic vinegar', user_id=user.id, complete=1, list_id=list_1.id)
                db.session.add(item_8)
                item_9 = Listitem(hex_id='09d924ee', item='Bacon', user_id=user.id, complete=1, list_id=list_1.id)
                db.session.add(item_9)
                item_10 = Listitem(hex_id='10d924ee', item='Boxed brown rice', user_id=user.id, complete=0, list_id=list_2.id)
                db.session.add(item_10)
                item_11 = Listitem(hex_id='11d924ee', item='1.5 lb chicken cutlets', user_id=user.id, complete=0, list_id=list_2.id)
                db.session.add(item_11)
                item_12 = Listitem(hex_id='12d924ee', item='paprika', user_id=user.id, complete=0, list_id=list_2.id)
                db.session.add(item_12)
                item_13 = Listitem(hex_id='13d924ee', item='Cauliflower', user_id=user.id, complete=1, list_id=list_2.id)
                db.session.add(item_13)
                db.session.commit()
            except:
                pass