from functools import wraps
from flask import Blueprint,render_template,request,redirect,url_for,session,flash
from werkzeug.security import generate_password_hash,check_password_hash
from .db import get_db
auth_bp=Blueprint("auth",__name__)
def login_required(view):
    @wraps(view)
    def wrapped(*a,**kw):
        return view(*a,**kw) if "user_id" in session else redirect(url_for("auth.login"))
    return wrapped
@auth_bp.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        n=request.form.get("name","").strip();e=request.form.get("email","").strip().lower();p=request.form.get("password","")
        if not n or not e or len(p)<8:
            flash("Name, email and password of 8+ characters are required.");return render_template("register.html")
        try:
            cur=get_db().execute("INSERT INTO users(name,email,password_hash) VALUES(?,?,?)",(n,e,generate_password_hash(p)))
            get_db().commit();session.clear();session["user_id"]=cur.lastrowid;session["user_name"]=n
            return redirect(url_for("main.dashboard"))
        except Exception: flash("That email is already registered.")
    return render_template("register.html")
@auth_bp.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        r=get_db().execute("SELECT * FROM users WHERE email=?",(request.form.get("email","").strip().lower(),)).fetchone()
        if r and check_password_hash(r["password_hash"],request.form.get("password","")):
            session.clear();session["user_id"]=r["id"];session["user_name"]=r["name"];return redirect(url_for("main.dashboard"))
        flash("Invalid email or password.")
    return render_template("login.html")
@auth_bp.route("/logout")
def logout():
    session.clear();return redirect(url_for("auth.login"))
