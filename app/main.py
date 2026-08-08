import io,sqlite3,numpy as np,pandas as pd
from flask import Blueprint,render_template,request,redirect,url_for,session,flash,Response
from .db import get_db
from .auth import login_required
main_bp=Blueprint("main",__name__)
COLS=["order_id","order_date","customer_id","product_id","warehouse_id","supplier_id","category","quantity","unit_price","unit_cost","promised_date","delivery_date","stock_units","defect_rate","transport_cost"]
def uid(): return session["user_id"]
def audit(a,d=""):
    db=get_db();db.execute("INSERT INTO audit_log(user_id,action,details) VALUES(?,?,?)",(uid(),a,d));db.commit()
def df():
    rows=get_db().execute("SELECT order_id,order_date,customer_id,product_id,warehouse_id,supplier_id,category,quantity,unit_price,unit_cost,promised_date,delivery_date,stock_units,defect_rate,transport_cost FROM orders WHERE user_id=? ORDER BY order_date",(uid(),)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])
def kpis(x):
    if x.empty:return dict(revenue=0,profit=0,margin=0,orders=0,units=0,inventory=0,otif=0,stockout=0,lead=0)
    for c in ["quantity","unit_price","unit_cost","stock_units","transport_cost"]:x[c]=pd.to_numeric(x[c],errors="coerce").fillna(0)
    rev=(x.quantity*x.unit_price).sum();profit=rev-(x.quantity*x.unit_cost).sum()-x.transport_cost.sum()
    p=pd.to_datetime(x.promised_date,errors="coerce");d=pd.to_datetime(x.delivery_date,errors="coerce");v=p.notna()&d.notna()
    lead=(d-pd.to_datetime(x.order_date,errors="coerce")).dt.days.dropna()
    return dict(revenue=round(float(rev),2),profit=round(float(profit),2),margin=round(float(profit/rev*100),2) if rev else 0,
      orders=int(x.order_id.nunique()),units=round(float(x.quantity.sum()),2),inventory=round(float((x.stock_units*x.unit_cost).sum()),2),
      otif=round(float(((d<=p)&v).sum()/max(v.sum(),1)*100),2),stockout=round(float((x.stock_units<=0).mean()*100),2),
      lead=round(float(lead.mean()),2) if len(lead) else 0)
def charts(x):
    if x.empty:return {k:[] for k in ["monthly","category","warehouse","supplier","inventory","delay","scatter"]}
    x=x.copy();x["revenue"]=x.quantity*x.unit_price;x["month"]=pd.to_datetime(x.order_date,errors="coerce").dt.to_period("M").astype(str)
    x["delay"]=(pd.to_datetime(x.delivery_date,errors="coerce")-pd.to_datetime(x.promised_date,errors="coerce")).dt.days.fillna(0)
    z={
      "monthly":x.groupby("month",as_index=False).revenue.sum(),
      "category":x.groupby("category",as_index=False).revenue.sum().sort_values("revenue",ascending=False),
      "warehouse":x.groupby("warehouse_id",as_index=False).revenue.sum(),
      "supplier":x.groupby("supplier_id",as_index=False).revenue.sum().sort_values("revenue",ascending=False).head(10),
      "inventory":x.groupby("category",as_index=False).stock_units.sum().sort_values("stock_units",ascending=False),
      "delay":x.groupby("supplier_id",as_index=False).delay.mean().sort_values("delay",ascending=False),
      "scatter":x[["quantity","revenue"]].head(500)}
    return {k:v.replace({np.nan:None}).to_dict("records") for k,v in z.items()}
@main_bp.route("/")
def index():return redirect(url_for("main.dashboard") if "user_id" in session else url_for("auth.login"))
@main_bp.route("/dashboard")
@login_required
def dashboard():return render_template("dashboard.html",kpi=kpis(df()),charts=charts(df()),name=session["user_name"])
@main_bp.route("/analytics")
@login_required
def analytics():
    x=df();risk=[]
    if not x.empty:
        for s,g in x.groupby("supplier_id"):
            p=pd.to_datetime(g.promised_date,errors="coerce");d=pd.to_datetime(g.delivery_date,errors="coerce");v=p.notna()&d.notna()
            late=((d>p)&v).sum()/max(v.sum(),1);defect=pd.to_numeric(g.defect_rate,errors="coerce").fillna(0).mean();stock=(pd.to_numeric(g.stock_units,errors="coerce").fillna(0)<=0).mean()
            score=min(100,round(late*45+min(defect/10,1)*30+stock*25,1));risk.append({"supplier":str(s),"risk":score,"late":round(late*100,1),"defect":round(defect,2)})
    return render_template("advanced.html",risk=sorted(risk,key=lambda r:r["risk"],reverse=True),charts=charts(x))
def values(f):
    return (f["order_id"],f["order_date"],f.get("customer_id"),f.get("product_id"),f.get("warehouse_id"),f.get("supplier_id"),f.get("category"),
      float(f.get("quantity") or 0),float(f.get("unit_price") or 0),float(f.get("unit_cost") or 0),f.get("promised_date"),f.get("delivery_date"),
      float(f.get("stock_units") or 0),float(f.get("defect_rate") or 0),float(f.get("transport_cost") or 0))
@main_bp.route("/data")
@login_required
def data():return render_template("data.html",rows=get_db().execute("SELECT * FROM orders WHERE user_id=? ORDER BY order_date DESC,id DESC LIMIT 1000",(uid(),)).fetchall())
@main_bp.route("/data/add",methods=["GET","POST"])
@login_required
def add_data():
    if request.method=="POST":
        try:
            get_db().execute("INSERT INTO orders(user_id,"+",".join(COLS)+") VALUES("+",".join(["?"]*(len(COLS)+1))+")",(uid(),)+values(request.form));get_db().commit();audit("ADD_ORDER",request.form["order_id"]);flash("Record saved.");return redirect(url_for("main.data"))
        except Exception as e:flash("Could not save: "+str(e))
    return render_template("form.html",row=None,title="Add Supply Chain Record")
@main_bp.route("/data/edit/<int:rid>",methods=["GET","POST"])
@login_required
def edit_data(rid):
    row=get_db().execute("SELECT * FROM orders WHERE id=? AND user_id=?",(rid,uid())).fetchone()
    if not row:return "Not found",404
    if request.method=="POST":
        setq=",".join(c+"=?" for c in COLS);get_db().execute("UPDATE orders SET "+setq+" WHERE id=? AND user_id=?",values(request.form)+(rid,uid()));get_db().commit();audit("EDIT_ORDER",request.form["order_id"]);flash("Updated.");return redirect(url_for("main.data"))
    return render_template("form.html",row=row,title="Edit Supply Chain Record")
@main_bp.route("/data/delete/<int:rid>",methods=["POST"])
@login_required
def delete_data(rid):
    r=get_db().execute("SELECT order_id FROM orders WHERE id=? AND user_id=?",(rid,uid())).fetchone();get_db().execute("DELETE FROM orders WHERE id=? AND user_id=?",(rid,uid()));get_db().commit()
    if r:audit("DELETE_ORDER",r["order_id"])
    flash("Deleted.");return redirect(url_for("main.data"))
@main_bp.route("/upload",methods=["GET","POST"])
@login_required
def upload():
    if request.method=="POST":
        f=request.files.get("file")
        if not f or not f.filename.lower().endswith(".csv"):flash("Upload CSV.");return redirect(url_for("main.upload"))
        try:
            x=pd.read_csv(io.BytesIO(f.read()));missing=[c for c in COLS if c not in x.columns]
            if missing:flash("Missing: "+", ".join(missing));return redirect(url_for("main.upload"))
            db=get_db();n=sk=0
            for _,r in x[COLS].iterrows():
                try:db.execute("INSERT INTO orders(user_id,"+",".join(COLS)+") VALUES("+",".join(["?"]*(len(COLS)+1))+")",(uid(),)+tuple(str(r[c]) if c not in ["quantity","unit_price","unit_cost","stock_units","defect_rate","transport_cost"] else float(r[c] or 0) for c in COLS));n+=1
                except sqlite3.IntegrityError:sk+=1
            db.commit();audit("UPLOAD_CSV",f"{n} inserted, {sk} duplicates");flash(f"Upload complete: {n} inserted, {sk} skipped.");return redirect(url_for("main.dashboard"))
        except Exception as e:flash("CSV error: "+str(e))
    return render_template("upload.html",columns=COLS)
@main_bp.route("/load-demo",methods=["POST"])
@login_required
def demo():
    x=pd.read_csv("data/sample/demo_orders.csv");db=get_db();n=0
    for _,r in x.iterrows():
        try:db.execute("INSERT INTO orders(user_id,"+",".join(COLS)+") VALUES("+",".join(["?"]*(len(COLS)+1))+")",(uid(),)+tuple(r[c] for c in COLS));n+=1
        except sqlite3.IntegrityError:pass
    db.commit();audit("LOAD_DEMO",str(n));flash(f"Demo data loaded: {n} records.");return redirect(url_for("main.dashboard"))
@main_bp.route("/export.csv")
@login_required
def export_csv():
    out=io.StringIO();df().to_csv(out,index=False);return Response(out.getvalue(),mimetype="text/csv",headers={"Content-Disposition":"attachment; filename=supply_chain_export.csv"})
