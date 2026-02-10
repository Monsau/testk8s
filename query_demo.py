#!/usr/bin/env python3
"""
Script pour afficher les données de la base PostgreSQL demo.
Usage: python query_demo.py [--host HOST] [--port PORT]
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import argparse
import sys


def get_connection(host, port, database, user, password):
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        return conn
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")
        sys.exit(1)


def print_table(title, headers, rows):
    """Affiche un tableau formaté"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

    if not rows:
        print("  (aucune donnée)")
        return

    # Calculer la largeur des colonnes
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))

    # Header
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    print(f"  {header_line}")
    print(f"  {'-+-'.join('-' * w for w in col_widths)}")

    # Rows
    for row in rows:
        line = " | ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row))
        print(f"  {line}")

    print(f"\n  Total: {len(rows)} lignes")


def show_users(cursor):
    cursor.execute("SELECT id, username, email, full_name FROM users ORDER BY id")
    rows = cursor.fetchall()
    print_table("👥 UTILISATEURS", ["ID", "Username", "Email", "Nom complet"],
                [(r['id'], r['username'], r['email'], r['full_name']) for r in rows])


def show_categories(cursor):
    cursor.execute("SELECT id, name, description FROM categories ORDER BY id")
    rows = cursor.fetchall()
    print_table("📂 CATÉGORIES", ["ID", "Nom", "Description"],
                [(r['id'], r['name'], r['description']) for r in rows])


def show_products(cursor):
    cursor.execute("""
        SELECT p.id, p.name, p.price, p.stock, c.name as category
        FROM products p
        JOIN categories c ON p.category_id = c.id
        ORDER BY p.id
    """)
    rows = cursor.fetchall()
    print_table("🛍️  PRODUITS", ["ID", "Nom", "Prix", "Stock", "Catégorie"],
                [(r['id'], r['name'], f"{r['price']}€", r['stock'], r['category']) for r in rows])


def show_orders(cursor):
    cursor.execute("""
        SELECT o.id, u.username, o.total_amount, o.status, o.created_at::date
        FROM orders o
        JOIN users u ON o.user_id = u.id
        ORDER BY o.id
    """)
    rows = cursor.fetchall()
    print_table("📦 COMMANDES", ["ID", "Client", "Montant", "Statut", "Date"],
                [(r['id'], r['username'], f"{r['total_amount']}€", r['status'], r['created_at']) for r in rows])


def show_order_details(cursor):
    cursor.execute("""
        SELECT oi.order_id, p.name, oi.quantity, oi.price
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        ORDER BY oi.order_id, oi.id
    """)
    rows = cursor.fetchall()
    print_table("📋 DÉTAIL DES COMMANDES", ["Commande", "Produit", "Qté", "Prix"],
                [(r['order_id'], r['name'], r['quantity'], f"{r['price']}€") for r in rows])


def show_stats(cursor):
    print(f"\n{'='*60}")
    print(f"  📊 STATISTIQUES")
    print(f"{'='*60}")

    cursor.execute("SELECT COUNT(*) as c FROM users")
    print(f"  Utilisateurs   : {cursor.fetchone()['c']}")

    cursor.execute("SELECT COUNT(*) as c FROM categories")
    print(f"  Catégories     : {cursor.fetchone()['c']}")

    cursor.execute("SELECT COUNT(*) as c FROM products")
    print(f"  Produits       : {cursor.fetchone()['c']}")

    cursor.execute("SELECT COUNT(*) as c FROM orders")
    print(f"  Commandes      : {cursor.fetchone()['c']}")

    cursor.execute("SELECT SUM(total_amount) as total FROM orders")
    total = cursor.fetchone()['total']
    print(f"  Chiffre total  : {total}€")

    cursor.execute("""
        SELECT p.name, SUM(oi.quantity) as total_sold
        FROM products p
        JOIN order_items oi ON p.id = oi.product_id
        GROUP BY p.name
        ORDER BY total_sold DESC
        LIMIT 3
    """)
    rows = cursor.fetchall()
    print(f"\n  🏆 Top 3 produits vendus :")
    for i, r in enumerate(rows, 1):
        print(f"     {i}. {r['name']} ({r['total_sold']} vendus)")

    cursor.execute("""
        SELECT u.username, SUM(o.total_amount) as total
        FROM users u
        JOIN orders o ON u.id = o.user_id
        GROUP BY u.username
        ORDER BY total DESC
        LIMIT 3
    """)
    rows = cursor.fetchall()
    print(f"\n  💰 Top 3 clients :")
    for i, r in enumerate(rows, 1):
        print(f"     {i}. {r['username']} ({r['total']}€)")


def main():
    parser = argparse.ArgumentParser(description="Affiche les données de la base PostgreSQL demo")
    parser.add_argument("--host", default="localhost", help="Hôte PostgreSQL (défaut: localhost)")
    parser.add_argument("--port", type=int, default=30432, help="Port PostgreSQL (défaut: 30432)")
    parser.add_argument("--user", default="postgres", help="Utilisateur (défaut: postgres)")
    parser.add_argument("--password", default="admin123", help="Mot de passe (défaut: admin123)")
    parser.add_argument("--database", default="demo", help="Base de données (défaut: demo)")
    parser.add_argument("--table", choices=["users", "categories", "products", "orders", "details", "stats", "all"],
                        default="all", help="Table à afficher (défaut: all)")
    args = parser.parse_args()

    print(f"\n🐘 Connexion à PostgreSQL {args.host}:{args.port}/{args.database}...")
    conn = get_connection(args.host, args.port, args.database, args.user, args.password)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    print(f"✅ Connecté !")

    table_map = {
        "users": show_users,
        "categories": show_categories,
        "products": show_products,
        "orders": show_orders,
        "details": show_order_details,
        "stats": show_stats,
    }

    if args.table == "all":
        show_stats(cursor)
        show_users(cursor)
        show_categories(cursor)
        show_products(cursor)
        show_orders(cursor)
        show_order_details(cursor)
    else:
        table_map[args.table](cursor)

    cursor.close()
    conn.close()
    print(f"\n{'='*60}")
    print(f"  ✅ Terminé !")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
