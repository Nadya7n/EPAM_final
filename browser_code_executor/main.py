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
path_to_config = os.path.join(os.path.dirname(__file__), "config/config.ini")
config.read(path_to_config)


def return_timeout(config, new_value=0):
    timeout = int(config["timeout"]["timeout"])
    return timeout if new_value == 0 or int(new_value) > timeout else new_value


class Table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Text, nullable=False)
    stdin = db.Column(db.String(300), nullable=True)
    stderr = db.Column(db.Text, nullable=True)
    stdout = db.Column(db.Text, nullable=True)
    timeout = db.Column(db.Integer, default=return_timeout(config))

    def __repr__(self):
        return "<Table %r>" % self.id


db.create_all()


def create_file(code):
    temp_dir = tempfile.gettempdir()
    temp_file = f"{temp_dir}/exec.py"
    with open(temp_file, "a+") as fh:
        fh.write(code)
    return temp_file


def read_check_security_file():
    path_to_file = os.path.join(os.path.dirname(__file__), "config/check_security.txt")
    with open(path_to_file) as fh:
        return fh.read()


def run_script(code, stdin, timeout, config):
    code_with_security_check = read_check_security_file() + code
    script = create_file(code_with_security_check)
    args = [
        "python",
        script,
        config["black_list"]["functions"],
        config["black_list"]["imports"],
    ]
    process = Popen(args=args, stdin=PIPE, stdout=PIPE, stderr=PIPE, encoding="utf-8")

    try:
        stdout, stderr = process.communicate(stdin, timeout=timeout)
    except TimeoutExpired as to:
        stdout, stderr = "", f"TimeoutExpired: {to}"
    except Exception as ex:
        stdout, stderr = "", f"Error: {ex}"
    finally:
        table = Table(code=code, stdin=stdin, stdout=stdout, stderr=stderr)
        os.remove(script)
    return table


@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        code = request.form["code"]
        stdin = request.form["stdin"]
        input_timeout = request.form["timeout"] if request.form["timeout"] else 0
        timeout = return_timeout(config, new_value=int(input_timeout))
        table = run_script(code, stdin, timeout, config)

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
        input_timeout = request.form["timeout"] if request.form["timeout"] else 0
        table.timeout = return_timeout(config, new_value=int(input_timeout))
        new_table = run_script(table.code, table.stdin, table.timeout, config)

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
    app.run(debug=True, host="0.0.0.0")
