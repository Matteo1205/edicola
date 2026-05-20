import os
from dotenv import load_dotenv, find_dotenv

# Carica le variabili d'ambiente dal file .env se esiste
_dotenv_path = find_dotenv()
if _dotenv_path:
    load_dotenv(_dotenv_path)


# Configurazione dell'applicazione Flask e del database
class Config:

    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-cambia-in-produzione')

    DATABASE_HOST = os.environ.get('DATABASE_HOST', '')
    DATABASE_PORT = os.environ.get('DATABASE_PORT', '')
    DATABASE_NAME = os.environ.get('DATABASE_NAME', '')
    DATABASE_USER = os.environ.get('DATABASE_USER', '')
    DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD', '')
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', '')

    DB_PARAMS = {
        'host': DATABASE_HOST,
        'port': DATABASE_PORT,
        'dbname': DATABASE_NAME,
        'user': DATABASE_USER,
        'password': DATABASE_PASSWORD,
    }
