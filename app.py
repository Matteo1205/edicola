from flask import Flask, redirect, url_for
from config import Config

# Crea l'app Flask e carica la configurazione
app = Flask(__name__)
app.config.from_object(Config)

# Registra blueprints
from routes.prodotti import bp as bp_prodotti
from routes.vendite import bp as bp_vendite
from routes.inventario import bp as bp_inventario
from routes.report import bp as bp_report

app.register_blueprint(bp_prodotti)
app.register_blueprint(bp_vendite)
app.register_blueprint(bp_inventario)
app.register_blueprint(bp_report)


# Rotta principale che reindirizza alla pagina dell'inventario
@app.route('/')
def index():
    return redirect(url_for('inventario.index'))


# Avvia l'app Flask in modalità debug se configurato
if __name__ == '__main__':
    app.run(debug=app.config.get('FLASK_DEBUG', False))
