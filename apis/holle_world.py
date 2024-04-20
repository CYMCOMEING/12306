from flask import render_template

from apis import app

@app.route("/", endpoint="hello_world")
def hello_world():
    # return "<p>Hello, World!</p>"
    return render_template('index.html')