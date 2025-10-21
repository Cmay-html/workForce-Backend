from flask import Flask
from flask_marshmallow import Marshmallow
from marshmallow import schema
from extensions import db

app = Flask(__name__)
ma = Marshmallow(app)
db.init_app(app)



if __name__ == "__main__":
    app.run(debug=True)