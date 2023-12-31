from app import app, db
from flask import render_template, request, redirect, url_for, flash, session
from .forms import PokemonForm, SignUpForm, LogInForm, EditProfileForm, CatchPokemonForm
import requests as r
from .models import User, CatchPokemon
from flask_login import login_user, logout_user, current_user, login_required


@app.route("/")
def index():
    return render_template('index.html')


# for /pokemoninfo
def get_pokemon(poke_name):
        poke_name = poke_name.lower()
        url = f"https://pokeapi.co/api/v2/pokemon/{poke_name}"
        response = r.get(url)
        if response.ok:
            data = response.json()
            return {
                 'name': data['name'],
                 'base hp stat': data['stats'][0]['base_stat'],
                 'base defense': data['stats'][2]['base_stat'],
                 'base attack': data['stats'][1]['base_stat'],
                 'image': data['sprites']['front_shiny'],
                 'ability': data['abilities'][0]['ability']['name']
            }

@app.route("/pokemoninfo", methods=["GET", "POST"], endpoint='pokemoninfo')
@login_required
def get_poke_info():
    form = PokemonForm()
    poke_dict = {}

    if request.method == 'POST':
        if form.validate():
            poke_name = form.poke_name.data
            poke_dict = get_pokemon(poke_name)

            if not poke_dict:
                flash('Pokemon not found. Please try again.', 'danger')
                return redirect(url_for('pokemoninfo'))
        else:
            flash('INVALID FORM', 'danger')
            return redirect(url_for('pokemoninfo'))

    return render_template('pokeinfo.html', form=form, pokemon_info=poke_dict)


@app.route("/signup", methods=["POST", "GET"])
def signup():
    form = SignUpForm()
    if request.method == 'POST':
        print("POST REQUEST MADE")
        if form.validate():
            first_name = form.first_name.data.title()
            last_name = form.last_name.data.title()
            email = form.email.data 
            password = form.password.data

            # check if email already exists
            user_exists = User.query.filter_by(email=email).first()

            if user_exists:
                print("USER EXISTS")
                flash("A user with this email already exists. Please use a different email.", 'danger')
                return redirect(url_for('signup'))
            
            else:
                new_user = User(first_name=first_name, last_name=last_name, email=email, password=password)
                db.session.add(new_user)
                db.session.commit()

                flash('Account created successfully!', 'success')
                return redirect(url_for('login'))
        
        else:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('signup'))
    
    return render_template('signup.html', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LogInForm()
    if request.method == 'POST':
        if form.validate():
            email = form.email.data
            password = form.password.data

            # check if user exists
            user = User.query.filter_by(email=email).first()

            if user and user.password == password:
                login_user(user)
                flash("Login Successful", 'success')
                return redirect(url_for('index'))
            
            else:
                flash('Invalid email or password. Please try again.', 'danger')
                return redirect(url_for('login'))

        else:
            flash('Invalid Form. Please try again.', 'danger')
            return redirect(url_for('login'))
    
    return render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route("/editprofile", methods=['GET', 'POST'])
@login_required
def editprofile():
    form = EditProfileForm()
    if request.method == 'POST':
        if 'delete_account' in request.form:
            deleted_user = User.query.get(current_user.id)
            CatchPokemon.query.filter_by(user_id=current_user.id).delete()
            db.session.delete(deleted_user)
            db.session.commit()

            logout_user()
            flash('Account successfully deleted.', 'danger')
            return redirect(url_for('login'))

        elif form.validate():
            new_email = form.email.data
            new_password = form.password.data
           
            if new_email:
                user_exists = User.query.filter_by(email=new_email).first()
                if new_email != current_user.email and not user_exists:
                    current_user.email = new_email
                    flash(f'Success! Email changed to: {new_email}', 'success')
                elif form.email.data != form.confirm_email.data:
                    flash("Email's do not match. Please try again.", 'danger')
                else:
                    flash('Please choose a new email.', 'danger')

            if new_password:
                if form.password.data != form.confirm_password.data:
                    flash("Password's do not match. Please try again.", 'danger')
                
                elif new_password != current_user.password:
                    current_user.password = new_password
                    flash('Success! New password created.', 'success')
                else:
                    flash('Please choose a different password.', 'danger')

            db.session.commit()
            return redirect(url_for('editprofile'))

        else:
            flash("Password's or Email's do not match. Please try again", 'danger')
            return redirect(url_for('editprofile'))
 
    return render_template('editprofile.html', form=form)


# for /catchpokemons       
def get_random_pokemon():
        import random
        random_pokemon = random.randint(1, 1292)
        url = f"https://pokeapi.co/api/v2/pokemon?limit=100000&offset=0"
        response = r.get(url)
        if response.ok:
            data = response.json()
            poke_url = data['results'][random_pokemon]['url']
            info_url = poke_url
            new_response = r.get(info_url)
            if new_response.ok:
                rand_poke_info = new_response.json()
    
                return {
                    'name': data['results'][random_pokemon]['name'],
                    'base_hp_stat': rand_poke_info['stats'][0]['base_stat'],
                    'base_defense': rand_poke_info['stats'][2]['base_stat'],
                    'base_attack': rand_poke_info['stats'][1]['base_stat'],
                    'image': rand_poke_info['sprites']['front_shiny'],
                    'ability': rand_poke_info['abilities'][0]['ability']['name']
                }
        

# for /catchpokemons          
def determine_if_caught():
    import random
    # determine whether or not the pokemon was caught
    determiner = random.randint(1,2)
    return determiner

@app.route('/catchpokemons', methods=['GET', 'POST'])
@login_required
def catch_pokemons():
    form = CatchPokemonForm()
    user_id = current_user.id
    rand_pokemon_dict = {}
    
    rand_pokemon_dict = session.get('rand_pokemon_dict')

    if not rand_pokemon_dict:
        rand_pokemon_dict = get_random_pokemon()
        session['rand_pokemon_dict'] = rand_pokemon_dict

    pokemon_name = rand_pokemon_dict.get('name')
    base_hp = rand_pokemon_dict.get('base_hp_stat')
    base_defense = rand_pokemon_dict.get('base_defense')
    base_attack = rand_pokemon_dict.get('base_attack')
    image = rand_pokemon_dict.get('image')
    ability = rand_pokemon_dict.get('ability')
    num_pokemon_caught = CatchPokemon.query.filter_by(user_id=user_id).count()

    if num_pokemon_caught >= 5:
        flash('You can not catch more than 5 Pokemon!', 'warning')
        return redirect(url_for('pokedex'))

    if request.method == 'POST':
        if 'find_pokemon' in request.form:
            # Generate a new rand_pokemon_dict and update it in the session
            rand_pokemon_dict = get_random_pokemon()
            session['rand_pokemon_dict'] = rand_pokemon_dict
            return redirect('catchpokemons')
        
        if 'catch_pokemon' in request.form:
            if not pokemon_name:
                flash('You need to find a pokemon first!', 'danger')
                return redirect(url_for('catch_pokemons'))
            
            caught_or_not = determine_if_caught()

            if caught_or_not == 1:
                # pokemon is caught
                already_caught = CatchPokemon.query.filter_by(user_id=user_id, pokemon_name=pokemon_name).first()

                if already_caught:
                    flash('You already have this pokemon.', 'danger')
                    return redirect(url_for('catch_pokemons'))
                
                else:
                    new_pokemon = CatchPokemon(pokemon_name, base_hp,
                                            base_defense, base_attack, 
                                            image, ability, user_id)
                    db.session.add(new_pokemon)
                    db.session.commit()

                    flash(f'You caught {pokemon_name.title()}!', 'success')
                    session.pop('rand_pokemon_dict', None)
                return redirect('catchpokemons')

            else:
                flash(f'Dang! {pokemon_name.title()} escaped!', 'danger')
                session.pop('rand_pokemon_dict', None)
                return redirect(url_for('catch_pokemons'))

    return render_template('catchpokemons.html', form=form, rand_pokemon_info=rand_pokemon_dict)


# for /pokedex
def get_users_pokemon(user_id):
    try:
        users_pokemon = CatchPokemon.query.filter_by(user_id=user_id).all()
        return users_pokemon
    except Exception:
        return []

@app.route('/pokedex', methods=['GET', 'POST'])
@login_required
def pokedex():
    user_id = current_user.id 
    users_pokemons = get_users_pokemon(user_id)
    
    if request.method == 'POST' and "release" in request.form:
        pokemon_id = request.form.get('pokemon_id')
        print("Received pokemon_id:", pokemon_id)
        released_pokemon = CatchPokemon.query.get(pokemon_id)

        if released_pokemon:
            flash(f'{released_pokemon.pokemon_name.title()} was released!', 'success')
            CatchPokemon.query.filter_by(id=pokemon_id).delete()
            db.session.commit()

        return redirect(url_for('pokedex'))
    
    users_pokemons.sort(key=lambda x: x.base_attack, reverse=True)
    return render_template('pokedex.html', users_pokemons=users_pokemons)


@app.route('/battle', methods=['GET', 'POST'])
@login_required
def battle():
    users = User.query.filter(User.id != current_user.id).all()
    user_pokemons = {}

    for user in users:
        pokemons = CatchPokemon.query.filter_by(user_id=user.id).all()

        user_pokemons[user] = pokemons

    return render_template('battle.html', user_pokemons=user_pokemons)


@app.route('/battle/challenge', methods=['POST'])
@login_required
def challenge():
    challenged_user_id = request.form.get('challenged_user_id')
    challenger_id = current_user.id
    challenged_user = User.query.get(challenged_user_id)
    challenger = User.query.get(challenger_id)

    if request.method == 'POST' and 'battle_again' in request.form:
        return redirect(url_for('battle'))
    
    else:
        challenger_pokemons = get_users_pokemon(challenger_id)
        challenged_user_pokemons = get_users_pokemon(challenged_user_id)

        challenger_power = 0
        for pokemon in challenger_pokemons:
            power = pokemon.base_attack + pokemon.base_defense + pokemon.base_hp
            if power > challenger_power:
                challenger_power = power
                challenger_strongest_pokemon = pokemon

        challenged_user_power = 0
        for pokemon in challenged_user_pokemons:
            power = pokemon.base_attack + pokemon.base_defense + pokemon.base_hp
            if power > challenged_user_power:
                challenged_user_power = power
                challenged_user_strongest_pokemon = pokemon

        if challenger_power > challenged_user_power:
            diff = challenger_power - challenged_user_power
            result = f'{challenger.first_name.upper()} wins by {diff} points!'
            strongest_pokemon = challenger_strongest_pokemon
        elif challenger_power < challenged_user_power:
            diff = challenged_user_power - challenger_power
            result = f'{challenged_user.first_name.upper()} wins by {diff} points!'
            strongest_pokemon = challenged_user_strongest_pokemon
        else:
            result = "It's a tie!"
            strongest_pokemon = None

    return render_template('battleresult.html', result=result, strongest_pokemon=strongest_pokemon)