from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('products.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price_mdl REAL NOT NULL,
            price_eur REAL NOT NULL,
            link TEXT,  -- Allow NULL values by default
            description TEXT,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()



from datetime import datetime

@app.route('/products', methods=['POST'])
def create_product():
    data = request.json
    name = data['name']
    price_mdl = data['price_mdl']
    price_eur = data['price_eur']
    link = data.get('link', None)  
    timestamp = datetime.utcnow().isoformat() + 'Z'  

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (name, price_mdl, price_eur, link, timestamp) VALUES (?, ?, ?, ?, ?)", (name, price_mdl, price_eur, link, timestamp))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Product created!'}), 201




@app.route('/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    
    return jsonify([dict(product) for product in products]), 200

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    data = request.json
    name = data['name']
    price_mdl = data['price_mdl']  
    price_eur = data['price_eur']    

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET name = ?, price_mdl = ?, price_eur = ? WHERE id = ?", (name, price_mdl, price_eur, id))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Product updated!'}), 200


@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Product deleted!'}), 200

if __name__ == '__main__':
    app.run(debug=True)
