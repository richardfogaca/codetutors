from flask import Flask
from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)

@app.route('/')
def main():
    return 'Hello World!'

if __name__ == '__main__':
    app.run()

from app import routes
