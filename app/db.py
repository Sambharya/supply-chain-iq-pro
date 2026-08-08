import sqlite3
from flask import current_app,g
SCHEMA='''
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT NOT NULL UNIQUE,
password_hash TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'analyst',
created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS orders(
id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,order_id TEXT NOT NULL,
order_date TEXT NOT NULL,customer_id TEXT,product_id TEXT,warehouse_id TEXT,supplier_id TEXT,
category TEXT,quantity REAL DEFAULT 0,unit_price REAL DEFAULT 0,unit_cost REAL DEFAULT 0,
promised_date TEXT,delivery_date TEXT,stock_units REAL DEFAULT 0,defect_rate REAL DEFAULT 0,
transport_cost REAL DEFAULT 0,created_at TEXT DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,UNIQUE(user_id,order_id));
CREATE TABLE IF NOT EXISTS audit_log(
id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,action TEXT NOT NULL,details TEXT,
created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS idx_orders_user_date ON orders(user_id,order_date);
'''
def get_db():
    if "db" not in g:
        g.db=sqlite3.connect(current_app.instance_path+"/supply_chain.db")
        g.db.row_factory=sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db
def close_db(e=None):
    db=g.pop("db",None)
    if db: db.close()
def init_db(app):
    with app.app_context():
        get_db().executescript(SCHEMA);get_db().commit()
    app.teardown_appcontext(close_db)
