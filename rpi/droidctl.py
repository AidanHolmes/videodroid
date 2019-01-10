from flask import render_template
import connexion as cx

app = cx.App(__name__,specification_dir="./")
app.add_api("apiconfig.yml")
# open /droid/ui to see doc

@app.route("/")
def home():
    return render_template("home.html")

if __name__ == "__main__":
    app.run(debug=False)
