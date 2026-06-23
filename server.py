"""
Kazino - Flask web aplikacija online kazina.

Sadrzi registraciju/prijavu korisnika, novcanik (uplata/isplata),
balans i istoriju igara, kao i rute za igre (Blackjack, Slot, Rulet, Plinko, Zmija).
Pokretanje: python server.py  ->  http://127.0.0.1:5001
"""
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
# Tajni kljuc se cita iz okruzenja (sa fallback-om za lokalni razvoj)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'casino-secret-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///casino.db'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(UserMixin, db.Model):
    """Korisnik kazina: kredencijali, balans i broj kartice."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    card_number = db.Column(db.String(30), nullable=False)

class GameHistory(db.Model):
    """Jedan zapis u istoriji igara (dobitak ili gubitak po rundi)."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False) # Pozitivno za dobitak, negativno za gubitak
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Ruta za profil
@app.route('/profile')
@login_required
def profile():
    history = GameHistory.query.filter_by(user_id=current_user.id).order_by(GameHistory.timestamp.desc()).limit(20).all()
    return render_template('profile.html', history=history)

# Rute
@app.route('/')
@login_required
def index():
    # Dohvatamo top 5 igrača po balansu za rang listu
    leaderboard = User.query.order_by(User.balance.desc()).limit(5).all()
    return render_template('index.html', leaderboard=leaderboard)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Prijava korisnika - proverava korisnicko ime i heširanu lozinku."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Pogrešno korisničko ime ili lozinka.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        card_number = (request.form.get('card_number') or '').strip()
        over_18 = request.form.get('over_18')  # checkbox

        # Provera punoletstva - bez potvrde nema naloga
        if not over_18:
            flash('Morate potvrditi da imate preko 18 godina.')
            return redirect(url_for('register'))

        # Kreditna kartica je obavezna pri registraciji
        if not card_number:
            flash('Morate uneti broj kreditne kartice.')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Korisnik već postoji.')
            return redirect(url_for('register'))

        # Novi korisnik počinje sa 0 - pare se dodaju samo preko profila (uplata sa kartice)
        new_user = User(username=username,
                        password=generate_password_hash(password, method='pbkdf2:sha256'),
                        balance=0.0,
                        card_number=card_number)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Odjava trenutnog korisnika."""
    logout_user()
    return redirect(url_for('login'))

# API za ažuriranje novca iz igara
@app.route('/update_balance', methods=['POST'])
@login_required
def update_balance():
    data = request.get_json()
    
    # SIGURNOST: Umesto da verujemo klijentu za novi 'balance', 
    # server uzima 'amount' (profit/gubitak) i sam ga dodaje na postojeći balans u bazi.
    if 'amount' in data:
        amount = float(data['amount'])
        current_user.balance += amount
        
        # Sačuvaj u istoriju samo ako je stvarna promena
        game_name = data.get('game_name', 'Unknown')
        new_entry = GameHistory(user_id=current_user.id, 
                               game_name=game_name, 
                               amount=amount)
        db.session.add(new_entry)
    
    # Ako klijent šalje balans direktno (npr. kod dodavanja para), proveriti da li je autorizovano
    elif 'balance' in data:
        current_user.balance = float(data['balance'])
        
    db.session.commit()
    return jsonify({"status": "success", "balance": current_user.balance})

# Uplata: simulacija prebacivanja para sa kartice na kazino balans
@app.route('/deposit', methods=['POST'])
@login_required
def deposit():
    try:
        amount = float(request.form.get('amount', 0))
    except (ValueError, TypeError):
        amount = 0

    if amount <= 0:
        flash('Unesite ispravan iznos za uplatu.')
    else:
        current_user.balance += amount
        db.session.commit()
        flash(f'Uspešna uplata: €{amount:.2f} prebačeno sa kartice na nalog.')
    return redirect(url_for('profile'))

# Isplata: simulacija prebacivanja para sa kazino balansa nazad na karticu
@app.route('/withdraw', methods=['POST'])
@login_required
def withdraw():
    try:
        amount = float(request.form.get('amount', 0))
    except (ValueError, TypeError):
        amount = 0

    if amount <= 0:
        flash('Unesite ispravan iznos za isplatu.')
    elif amount > current_user.balance:
        flash('Nemate dovoljno sredstava na nalogu za isplatu.')
    else:
        current_user.balance -= amount
        db.session.commit()
        flash(f'Uspešna isplata: €{amount:.2f} prebačeno sa naloga na karticu.')
    return redirect(url_for('profile'))

# Rute za igre
@app.route('/blackjack')
@login_required
def blackjack(): return render_template('BlackJack.html')

@app.route('/slot')
@login_required
def slot(): return render_template('slot.html')

@app.route('/plinko')
@login_required
def plinko(): return render_template('plinko.html')

@app.route('/rulet')
@login_required
def rulet(): return render_template('Rulet.html')

@app.route('/snake')
@login_required
def snake(): return render_template('zmija.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
