#!/usr/bin/env python3
"""
Script pour afficher les données de la base SQL Server Requests.
Usage: python query_mssql.py [--host HOST] [--port PORT]
"""

import pymssql
import argparse
import sys
import json


def get_connection(host, port, user, password, database):
    try:
        conn = pymssql.connect(
            server=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        return conn
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")
        sys.exit(1)


def print_table(title, headers, rows):
    """Affiche un tableau formaté"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")

    if not rows:
        print("  (aucune donnée)")
        return

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], min(len(str(val)), 50))

    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    print(f"  {header_line}")
    print(f"  {'-+-'.join('-' * w for w in col_widths)}")

    for row in rows:
        line = " | ".join(str(val)[:50].ljust(col_widths[i]) for i, val in enumerate(row))
        print(f"  {line}")

    print(f"\n  Total: {len(rows)} lignes")


def show_all_versions(cursor):
    """Affiche toutes les versions d'entités"""
    cursor.execute("""
        SELECT Id, LogicalId, Version, 
               JSON_VALUE(Properties, '$.type') as Type,
               JSON_VALUE(Properties, '$.title') as Title,
               JSON_VALUE(Properties, '$.status') as Status,
               JSON_VALUE(Properties, '$.priority') as Priority,
               ModifiedBy, ModifiedUtc, Latest
        FROM [data].[EntityVersion]
        ORDER BY Id, Version
    """)
    rows = cursor.fetchall()
    print_table(
        "📋 TOUTES LES VERSIONS D'ENTITÉS",
        ["ID", "LogicalId", "Ver", "Type", "Titre", "Statut", "Priorité", "Modifié par", "Date", "Latest"],
        rows
    )


def show_latest_only(cursor):
    """Affiche uniquement les dernières versions"""
    cursor.execute("""
        SELECT Id, LogicalId, Version,
               JSON_VALUE(Properties, '$.type') as Type,
               JSON_VALUE(Properties, '$.title') as Title,
               JSON_VALUE(Properties, '$.status') as Status,
               JSON_VALUE(Properties, '$.priority') as Priority,
               ModifiedBy, ModifiedUtc
        FROM [data].[EntityVersion]
        WHERE Latest = 1
        ORDER BY Id
    """)
    rows = cursor.fetchall()
    print_table(
        "✅ DERNIÈRES VERSIONS (Latest = 1)",
        ["ID", "LogicalId", "Ver", "Type", "Titre", "Statut", "Priorité", "Modifié par", "Date"],
        rows
    )


def show_history(cursor, logical_id):
    """Affiche l'historique d'une entité"""
    cursor.execute("""
        SELECT Version,
               JSON_VALUE(Properties, '$.status') as Status,
               JSON_VALUE(Properties, '$.priority') as Priority,
               ModifiedBy, ModifiedUtc, Latest,
               ExtensionsData
        FROM [data].[EntityVersion]
        WHERE LogicalId = %s
        ORDER BY Version
    """, (logical_id,))
    rows = cursor.fetchall()
    print_table(
        f"📜 HISTORIQUE DE {logical_id}",
        ["Ver", "Statut", "Priorité", "Modifié par", "Date", "Latest", "Extensions"],
        rows
    )


def show_stats(cursor):
    """Affiche les statistiques"""
    print(f"\n{'='*80}")
    print(f"  📊 STATISTIQUES - Base [Requests].[data].[EntityVersion]")
    print(f"{'='*80}")

    cursor.execute("SELECT COUNT(*) FROM [data].[EntityVersion]")
    print(f"  Total d'enregistrements    : {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(DISTINCT LogicalId) FROM [data].[EntityVersion]")
    print(f"  Entités uniques            : {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM [data].[EntityVersion] WHERE Latest = 1")
    print(f"  Dernières versions         : {cursor.fetchone()[0]}")

    cursor.execute("SELECT AVG(Version * 1.0) FROM [data].[EntityVersion] WHERE Latest = 1")
    avg = cursor.fetchone()[0]
    print(f"  Moyenne versions/entité    : {avg:.1f}")

    cursor.execute("""
        SELECT JSON_VALUE(Properties, '$.status') as Status, COUNT(*) as Cnt
        FROM [data].[EntityVersion]
        WHERE Latest = 1
        GROUP BY JSON_VALUE(Properties, '$.status')
        ORDER BY Cnt DESC
    """)
    rows = cursor.fetchall()
    print(f"\n  📌 Statuts actuels (dernières versions) :")
    for r in rows:
        print(f"     - {r[0]}: {r[1]}")

    cursor.execute("""
        SELECT JSON_VALUE(Properties, '$.type') as Type, COUNT(*) as Cnt
        FROM [data].[EntityVersion]
        WHERE Latest = 1
        GROUP BY JSON_VALUE(Properties, '$.type')
        ORDER BY Cnt DESC
    """)
    rows = cursor.fetchall()
    print(f"\n  📂 Types d'entités :")
    for r in rows:
        print(f"     - {r[0]}: {r[1]}")

    cursor.execute("""
        SELECT JSON_VALUE(Properties, '$.priority') as Priority, COUNT(*) as Cnt
        FROM [data].[EntityVersion]
        WHERE Latest = 1
        GROUP BY JSON_VALUE(Properties, '$.priority')
        ORDER BY Cnt DESC
    """)
    rows = cursor.fetchall()
    print(f"\n  🔥 Priorités :")
    for r in rows:
        print(f"     - {r[0]}: {r[1]}")

    cursor.execute("""
        SELECT TOP 3 ModifiedBy, COUNT(*) as Cnt
        FROM [data].[EntityVersion]
        GROUP BY ModifiedBy
        ORDER BY Cnt DESC
    """)
    rows = cursor.fetchall()
    print(f"\n  👤 Top contributeurs :")
    for i, r in enumerate(rows, 1):
        print(f"     {i}. {r[0]} ({r[1]} modifications)")


def main():
    parser = argparse.ArgumentParser(description="Affiche les données de SQL Server - Base Requests")
    parser.add_argument("--host", default="localhost", help="Hôte SQL Server (défaut: localhost)")
    parser.add_argument("--port", type=int, default=31433, help="Port SQL Server (défaut: 31433)")
    parser.add_argument("--user", default="sa", help="Utilisateur (défaut: sa)")
    parser.add_argument("--password", default="YourStr0ngP@ssw0rd!", help="Mot de passe")
    parser.add_argument("--database", default="Requests", help="Base de données (défaut: Requests)")
    parser.add_argument("--view", choices=["all", "latest", "stats", "history"],
                        default="all", help="Vue à afficher (défaut: all)")
    parser.add_argument("--id", default=None, help="LogicalId pour l'historique (ex: REQ-001)")
    args = parser.parse_args()

    print(f"\n🗄️  Connexion à SQL Server {args.host}:{args.port}/{args.database}...")
    conn = get_connection(args.host, args.port, args.user, args.password, args.database)
    cursor = conn.cursor()
    print(f"✅ Connecté !")

    if args.view == "history":
        if not args.id:
            print("❌ Spécifiez un --id pour l'historique (ex: --id REQ-001)")
            sys.exit(1)
        show_history(cursor, args.id)
    elif args.view == "latest":
        show_latest_only(cursor)
    elif args.view == "stats":
        show_stats(cursor)
    else:
        show_stats(cursor)
        show_latest_only(cursor)
        show_all_versions(cursor)

    cursor.close()
    conn.close()
    print(f"\n{'='*80}")
    print(f"  ✅ Terminé !")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
