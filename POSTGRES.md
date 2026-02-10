# 🐘 PostgreSQL sur Kubernetes - Guide de déploiement

## 📋 Ce qui a été créé

### Base de données PostgreSQL avec :
- **5 tables** : users, categories, products, orders, order_items
- **Données de démonstration** : 5 utilisateurs, 5 catégories, 11 produits, 5 commandes
- **2 vues SQL** : order_details, product_inventory
- **Stockage persistant** : PersistentVolumeClaim de 1Gi

### Credentials par défaut :
- **User** : `postgres`
- **Password** : `admin123`
- **Database** : `demo`

## 🚀 Déploiement rapide

### 1. Déployer PostgreSQL
```bash
# Déployer tous les composants PostgreSQL (dans l'ordre)
kubectl apply -f k8s/postgres-secret.yaml
kubectl apply -f k8s/postgres-configmap.yaml
kubectl apply -f k8s/postgres-pvc.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/postgres-service.yaml

# Attendre que le pod soit prêt
kubectl wait --for=condition=ready pod -l app=postgres --timeout=180s

# Vérifier les logs d'initialisation
kubectl logs -l app=postgres
```

### 2. Tester la connexion locale
```bash
# Port-forward pour accéder à PostgreSQL
kubectl port-forward svc/postgres 5432:5432
```

Puis dans un autre terminal :
```bash
# Avec psql (si installé)
psql -h localhost -U postgres -d demo

# Ou avec kubectl exec
kubectl exec -it deployment/postgres -- psql -U postgres -d demo
```

### 3. Requêtes SQL de test
```sql
-- Voir toutes les tables
\dt

-- Statistiques
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM products;
SELECT COUNT(*) FROM orders;

-- Produits par catégorie
SELECT c.name, COUNT(p.id) as products_count
FROM categories c
LEFT JOIN products p ON c.id = p.category_id
GROUP BY c.name;

-- Commandes avec détails
SELECT * FROM order_details;

-- Inventaire des produits
SELECT * FROM product_inventory;

-- Top 5 des produits les plus vendus
SELECT 
    p.name,
    SUM(oi.quantity) as total_quantity,
    SUM(oi.quantity * oi.price) as total_revenue
FROM products p
JOIN order_items oi ON p.id = oi.product_id
GROUP BY p.id, p.name
ORDER BY total_quantity DESC
LIMIT 5;
```

## 🔗 Intégration avec l'application Hello World

### 1. Rebuild l'image avec psycopg2
```bash
docker build -t ghcr.io/monsau/testk8s:latest .
docker push ghcr.io/monsau/testk8s:latest
```

### 2. Redéployer l'application
```bash
kubectl apply -f k8s/deployment.yaml
kubectl rollout restart deployment/hello-world
```

### 3. Tester les endpoints API
```bash
# Port-forward de l'application
kubectl port-forward svc/hello-world 3000:80
```

Puis ouvrir dans le navigateur :
- **Page principale** : http://localhost:3000
- **Stats DB** : http://localhost:3000/api/stats
- **Utilisateurs** : http://localhost:3000/api/users
- **Produits** : http://localhost:3000/api/products
- **Commandes** : http://localhost:3000/api/orders

## 📊 Structure de la base de données

```
┌─────────────┐
│   users     │
│─────────────│
│ id          │
│ username    │
│ email       │
│ full_name   │
│ created_at  │
└─────────────┘
       │
       │ 1:N
       ▼
┌─────────────┐       ┌──────────────┐
│   orders    │       │  categories  │
│─────────────│       │──────────────│
│ id          │       │ id           │
│ user_id     │       │ name         │
│ total_amount│       │ description  │
│ status      │       └──────────────┘
│ created_at  │              │
└─────────────┘              │ 1:N
       │                     ▼
       │ 1:N          ┌─────────────┐
       │              │  products   │
       │              │─────────────│
       │              │ id          │
       │              │ name        │
       │              │ price       │
       │              │ stock       │
       │              │ category_id │
       │              └─────────────┘
       │                     │
       │                     │
       ▼                     │
┌──────────────┐             │
│ order_items  │◄────────────┘
│──────────────│
│ id           │
│ order_id     │
│ product_id   │
│ quantity     │
│ price        │
└──────────────┘
```

## 🔄 Avec ArgoCD

ArgoCD synchronisera automatiquement tous les fichiers du dossier `k8s/` :
- deployment.yaml (application)
- service.yaml (application)
- postgres-secret.yaml
- postgres-configmap.yaml
- postgres-pvc.yaml
- postgres-deployment.yaml
- postgres-service.yaml

**Attention** : Le PVC (stockage) persiste même si vous supprimez le deployment. Pour un reset complet :
```bash
# Supprimer tous les composants
kubectl delete -f k8s/

# Supprimer aussi le PVC pour un reset complet
kubectl delete pvc postgres-pvc
```

## 🛠️ Commandes utiles

```bash
# Voir les logs PostgreSQL
kubectl logs -f deployment/postgres

# Se connecter en shell dans le pod
kubectl exec -it deployment/postgres -- bash

# Backup de la base
kubectl exec deployment/postgres -- pg_dump -U postgres demo > backup.sql

# Restore
cat backup.sql | kubectl exec -i deployment/postgres -- psql -U postgres demo

# Voir l'utilisation du stockage
kubectl describe pvc postgres-pvc

# Lister les pods
kubectl get pods -l app=postgres
kubectl get pods -l app=hello-world
```

## 🔒 Sécurité - Production

Pour la production, modifiez :

1. **Le mot de passe** dans [k8s/postgres-secret.yaml](k8s/postgres-secret.yaml) :
```bash
echo -n 'votre_password_fort' | base64
```

2. **Le type de service** : Changez `LoadBalancer` en `ClusterIP` pour ne pas exposer PostgreSQL

3. **Les ressources** : Ajustez selon vos besoins dans [k8s/postgres-deployment.yaml](k8s/postgres-deployment.yaml)

## 🧪 Tests de charge

```bash
# Installer pgbench (outil de benchmark PostgreSQL)
kubectl exec -it deployment/postgres -- pgbench -i -U postgres demo

# Lancer un test
kubectl exec -it deployment/postgres -- pgbench -U postgres -c 10 -j 2 -t 1000 demo
```
