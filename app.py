from flask import Flask, jsonify
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Configuration de la base de données
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'postgres'),
    'port': os.environ.get('DB_PORT', '5432'),
    'database': os.environ.get('DB_NAME', 'demo'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'admin123')
}

def get_db_connection():
    """Établit une connexion à la base de données"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Erreur de connexion à la DB: {e}")
        return None

@app.route('/')
def hello():
    version = os.environ.get('VERSION', '1.0')
    return f'''
    <html>
        <head>
            <title>Hello World</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }}
                .container {{
                    text-align: center;
                    padding: 40px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 20px;
                    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                }}
                h1 {{
                    font-size: 3em;
                    margin-bottom: 20px;
                }}
                .version {{
                    font-size: 1.2em;
                    opacity: 0.8;
                }}
                .links {{
                    margin-top: 30px;
                }}
                .links a {{
                    display: inline-block;
                    margin: 10px;
                    padding: 12px 24px;
                    background: rgba(255, 255, 255, 0.2);
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                    transition: all 0.3s;
                }}
                .links a:hover {{
                    background: rgba(255, 255, 255, 0.3);
                    transform: translateY(-2px);
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎉 Hello World from Kubernetes! 🎉</h1>
                <p class="version">Version: {version}</p>
                <p>Déployé avec ArgoCD</p>
                <div class="links">
                    <a href="/api/stats">📊 Stats DB</a>
                    <a href="/api/users">👥 Utilisateurs</a>
                    <a href="/api/products">🛍️ Produits</a>
                    <a href="/api/orders">📦 Commandes</a>
                </div>
            </div>
        </body>
    </html>
    '''

@app.route('/health')
def health():
    # Vérifier aussi la connexion DB
    conn = get_db_connection()
    db_status = 'healthy' if conn else 'unhealthy'
    if conn:
        conn.close()
    
    return {
        'status': 'healthy',
        'database': db_status
    }, 200

@app.route('/api/stats')
def stats():
    """Statistiques de la base de données"""
    conn = get_db_connection()
    if not conn:
        return {'error': 'Impossible de se connecter à la base de données'}, 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Compter les différentes entités
        cursor.execute('SELECT COUNT(*) as count FROM users')
        users_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM products')
        products_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM orders')
        orders_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT COUNT(*) as count FROM categories')
        categories_count = cursor.fetchone()['count']
        
        cursor.execute('SELECT SUM(total_amount) as total FROM orders')
        total_sales = cursor.fetchone()['total']
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'database': 'demo',
            'statistics': {
                'users': users_count,
                'products': products_count,
                'orders': orders_count,
                'categories': categories_count,
                'total_sales': float(total_sales) if total_sales else 0
            }
        })
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/api/users')
def users():
    """Liste des utilisateurs"""
    conn = get_db_connection()
    if not conn:
        return {'error': 'Impossible de se connecter à la base de données'}, 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT id, username, email, full_name, created_at FROM users ORDER BY id')
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'users': users})
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/api/products')
def products():
    """Liste des produits avec leurs catégories"""
    conn = get_db_connection()
    if not conn:
        return {'error': 'Impossible de se connecter à la base de données'}, 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('''
            SELECT p.id, p.name, p.price, p.stock, c.name as category
            FROM products p
            JOIN categories c ON p.category_id = c.id
            ORDER BY p.id
        ''')
        products = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'products': products})
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/api/orders')
def orders():
    """Liste des commandes avec détails"""
    conn = get_db_connection()
    if not conn:
        return {'error': 'Impossible de se connecter à la base de données'}, 500
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM order_details ORDER BY order_id DESC')
        orders = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'orders': orders})
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
