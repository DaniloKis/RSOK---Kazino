# Kazino

Web aplikacija online kazina napravljena u **Pythonu (Flask)**. Korisnici se registruju,
uplaćuju/isplaćuju novac (simulacija kartice) i igraju više igara na sreću.

# Igre

- 🃏 **Blackjack**
- 🎰 **Slot**
- 🎡 **Rulet**
- 🎯 **Plinko**
- 🐍 **Zmija (Snake)**

# Mogućnosti

- Registracija sa proverom punoletstva (18+) i brojem kreditne kartice
- Prijava/odjava korisnika (lozinke se čuvaju heširane)
- Novčanik: uplata i isplata (simulacija transfera sa kartice)
- Balans po korisniku, istorija igara i rang lista (top 5)

# Tehnologije

- Flask
- Flask-SQLAlchemy (SQLite baza)
- Flask-Login


# Struktura

```
server.py            # Flask server, rute i model baze
templates/           # HTML sabloni (igre + stranice)
static/              # Staticki fajlovi (favicon)
requirements.txt     # Python zavisnosti
```

# Licenca

MIT — vidi [LICENSE](LICENSE).
