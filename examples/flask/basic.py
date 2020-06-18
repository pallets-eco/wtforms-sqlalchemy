from wtforms_sqlalchemy.orm import model_form

from flask import Flask
from flask import render_template
from flask import request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sample_db.sqlite"
app.config["SQLALCHEMY_ECHO"] = True

db = SQLAlchemy(app)


class Car(db.Model):
    __tablename__ = "cars"
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(50))
    model = db.Column(db.String(50))


CarForm = model_form(Car)


@app.route("/", methods=["GET", "POST"])
def create_car():
    car = Car()
    success = False

    if request.method == "POST":
        form = CarForm(request.form, obj=car)
        if form.validate():
            form.populate_obj(car)
            db.session.add(car)
            db.session.commit()
            success = True
    else:
        form = CarForm(obj=car)

    return render_template("create.html", form=form, success=success)


if __name__ == "__main__":
    db.create_all()

    app.run(debug=True)
