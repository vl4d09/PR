from flask import Flask, request, jsonify
import sqlite3
import os

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
            link TEXT,
            description TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Create a product
@app.route('/products', methods=['POST'])
def create_product():
    data = request.json
    name = data['name']
    price_mdl = data['price_mdl']
    price_eur = data['price_eur']
    link = data['link']
    description = data['description']
    timestamp = data['timestamp']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (name, price_mdl, price_eur, link, description, timestamp) VALUES (?, ?, ?, ?, ?, ?)", 
                   (name, price_mdl, price_eur, link, description, timestamp))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Product created!'}), 201

@app.route('/products', methods=['GET'])
def get_products():
    # Get pagination parameters from query
    offset = request.args.get('offset', default=0, type=int)
    limit = request.args.get('limit', default=5, type=int)

    conn = get_db_connection()
    
    # Get total count of products
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products")
    total_count = cursor.fetchone()[0]
    
    # Fetch paginated products
    cursor.execute("SELECT * FROM products LIMIT ? OFFSET ?", (limit, offset))
    products = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        'total_count': total_count,
        'products': [dict(product) for product in products]
    }), 200

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
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    save_path = os.path.join('uploads', file.filename)  
    file.save(save_path)

    return jsonify({'message': f'File {file.filename} uploaded successfully!'}), 201

if __name__ == '__main__':
    create_table()  
    app.run(debug=True)
