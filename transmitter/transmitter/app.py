from flask import Flask, render_template
from routes import family, member, entry, transmit, token   # __init__.py 內註冊 blueprint
from flask_cors import CORS

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "SuperSecretKey"
CORS(app, supports_credentials=True)  # 讓 cookie 能跨域

# 藍圖
app.register_blueprint(transmit.bp, url_prefix="/api/transmit")
app.register_blueprint(family.bp, url_prefix="/api/family")
app.register_blueprint(member.bp, url_prefix="/api/member")
app.register_blueprint(entry.bp,  url_prefix="/api/entry")
app.register_blueprint(token.bp, url_prefix="/api/token")

# ---------- 頁面 ----------
@app.route("/")
def root():          return render_template("login.html")
@app.route("/register")
def register_page(): return render_template("register.html")
@app.route("/members")
def members_page():  return render_template("members.html")
@app.route("/logs")
def logs_page():     return render_template("logs.html")
@app.route("/userlogin")
def userlogin(): return render_template("userlogin.html")
@app.route('/choose')
def choose_member():return render_template("choosemember.html")
@app.route("/transmit")
def transmit(): return render_template("transmit.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)