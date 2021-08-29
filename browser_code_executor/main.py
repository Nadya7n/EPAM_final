import configparser
import os
import tempfile
from subprocess import PIPE, Popen, TimeoutExpired

from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///sqlite.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

config = configparser.ConfigParser()
config.read("config/config.ini")


class Table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Text, nullable=False)
    stdin = db.Column(db.String(300), nullable=True)
    stderr = db.Column(db.Text, nullable=True)
    stdout = db.Column(db.Text, nullable=True)

    def __repr__(self):
        # table object plus its id will be given out
        return "<Table %r>" % self.id


def create_file(code):
    temp_dir = tempfile.gettempdir()
    temp_file = f"{temp_dir}/exec.py"
    with open(temp_file, "a+") as fh:
        fh.write(code)
    return temp_file


def run_script(code, stdin, config):
    file = create_file(code)
    args = [
        "python3",
        file,
        config["blocked"]["imports"],
        config["blocked"]["functions"],
    ]
    process = Popen(args=args, stdin=PIPE, stdout=PIPE, stderr=PIPE, encoding="utf-8")

    try:
        stdout, stderr = process.communicate(
            stdin, timeout=int(config["timeout"]["timeout"])
        )
    except TimeoutExpired as timeout:
        stdout, stderr = "", f"TimeoutExpired: {timeout}"
    finally:
        table = Table(code=code, stdin=stdin, stdout=stdout, stderr=stderr)
        os.remove(file)

    return table


@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        code = request.form["code"]
        stdin = request.form["stdin"]
        table = run_script(code, stdin, config)

        try:
            db.session.add(table)
            db.session.commit()
            return redirect(f"/database/{table.id}")
        except Exception as ex:
            return f"Error: {ex}"
    else:
        return render_template("index.html")


@app.route("/database")
def database():
    # desc - reverse sort
    tables = Table.query.order_by(Table.id.desc()).all()
    return render_template("db.html", tables=tables)


@app.route("/database/<int:id>")
def individual(id):
    table = Table.query.get(id)
    return render_template("individual.html", table=table)


@app.route("/database/<int:id>/delete")
def request_delete(id):
    table = Table.query.get_or_404(id)
    try:
        db.session.delete(table)
        db.session.commit()
        return redirect("/database")
    except Exception as ex:
        return f"Error: {ex}"


@app.route("/database/<int:id>/update", methods=["POST", "GET"])
def request_update(id):
    table = Table.query.get(id)
    if request.method == "POST":
        table.code = request.form["code"]
        table.stdin = request.form["stdin"]

        new_table = run_script(table.code, table.stdin, config)

        table.stdout = new_table.stdout
        table.stderr = new_table.stderr
        try:
            db.session.commit()
            return redirect(f"/database/{table.id}")
        except Exception as ex:
            return f"Error: {ex}"
    else:
        return render_template("request_update.html", table=table)


if __name__ == "__main__":
    app.run(debug=True)
