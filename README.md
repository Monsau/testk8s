# 🐘 PostgreSQL sur Kubernetes avec données de démonstration

Base de données PostgreSQL déployée sur Kubernetes avec un script d'initialisation automatique qui crée une base de données démo avec tables et données.

## 📋 Ce qui est inclus

### Base de données : `demo`

**5 tables** :
- `users` - Utilisateurs (5 entrées)
- `categories` - Catégories de produits (5 entrées)
- `products` - Produits (11 entrées)
- `orders` - Commandes (5 entrées)
- `order_items` - Items de commande

**2 vues SQL** :
- `order_details` - Vue complète des commandes avec utilisateurs
- `product_inventory` - Inventaire des produits avec ventes

### 🔑 Credentials par défaut
- **User** : `postgres`
- **Password** : `admin123`
- **Database** : `demo`
- **Port** : `5432`

---

## 🚀 Déploiement

### Option A : Avec ArgoCD (GitOps - Recommandé)

```bash
# 1. Installer ArgoCD (si pas déjà fait)
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Attendre que tout soit prêt
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s

# 2. Déployer l'application PostgreSQL via ArgoCD
kubectl apply -f argocd-app.yaml

# 3. Vérifier dans l'interface ArgoCD
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Ouvrir https://localhost:8080
# Username: admin
# Password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

**Avantages ArgoCD** :
- ✅ Synchronisation automatique depuis Git
- ✅ Détection des changements sur GitHub (toutes les 3 min)
- ✅ Self-heal : restaure automatiquement les modifications manuelles
- ✅ Interface graphique pour visualiser le déploiement
- ✅ Historique et rollback en 1 clic

### Option B : Déploiement manuel avec kubectl

```bash
# Déployer tous les composants (dans l'ordre)
kubectl apply -f k8s/postgres-secret.yaml
kubectl apply -f k8s/postgres-configmap.yaml
kubectl apply -f k8s/postgres-pvc.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/postgres-service.yaml

# Ou tout en une fois
kubectl apply -f k8s/
```

### 2. Attendre que le pod soit prêt

```bash
kubectl wait --for=condition=ready pod -l app=postgres --timeout=180s

# Vérifier le statut
kubectl get pods -l app=postgres
```

### 3. Voir les logs d'initialisation

```bash
kubectl logs -l app=postgres

# Vous devriez voir :
# - Création de la base 'demo'
# - Création des tables
# - Insertion des données
# - Message "Base de données initialisée avec succès!"
```

---

## � Tester la synchronisation ArgoCD

Si vous utilisez ArgoCD, vous pouvez tester la synchronisation automatique :

### 1. Modifier une ressource dans Git

Par exemple, changez le nombre de replicas :

```yaml
# Dans k8s/postgres-deployment.yaml
spec:
  replicas: 2  # Changez de 1 à 2
```

Puis commit et push :
```bash
git add k8s/postgres-deployment.yaml
git commit -m "Scale PostgreSQL to 2 replicas"
git push
```

### 2. Observer ArgoCD

- ArgoCD détecte le changement (max 3 minutes)
- Il synchronise automatiquement le cluster
- Vous verrez 2 pods PostgreSQL

Pour forcer une synchronisation immédiate :
```bash
kubectl patch application postgres-demo -n argocd --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
```

---

## �🔌 Se connecter à PostgreSQL

### Option 1 : Port-forward (recommandé pour tests locaux)

```bash
# Exposer PostgreSQL en local
kubectl port-forward svc/postgres 5432:5432
```

Puis dans un autre terminal :
```bash
# Avec psql (si installé localement)
psql -h localhost -U postgres -d demo
# Password: admin123
```

### Option 2 : Depuis un pod Kubernetes

```bash
# Se connecter directement au pod
kubectl exec -it deployment/postgres -- psql -U postgres -d demo
```

---

## 📊 Base de données de démonstration

### Structure des données

```
┌─────────────┐
│   users     │  → 5 utilisateurs (Alice, Bob, Charlie, Diana, Eve)
└─────────────┘
       │
       │ 1:N
       ▼
┌─────────────┐       ┌──────────────┐
│   orders    │       │  categories  │  → 5 catégories (Électronique, Livres, etc.)
└─────────────┘       └──────────────┘
       │                     │ 1:N
       │ 1:N                 ▼
       │              ┌─────────────┐
       │              │  products   │  → 11 produits (Laptop, Smartphone, etc.)
       │              └─────────────┘
       │                     │
       ▼                     │
┌──────────────┐             │
│ order_items  │◄────────────┘
└──────────────┘
```

### 🧪 Requêtes SQL de test

```sql
-- Voir toutes les tables
\dt

-- Statistiques
SELECT COUNT(*) FROM users;        -- 5 utilisateurs
SELECT COUNT(*) FROM products;     -- 11 produits
SELECT COUNT(*) FROM orders;       -- 5 commandes
SELECT COUNT(*) FROM categories;   -- 5 catégories

-- Produits par catégorie
SELECT 
    c.name AS categorie,
    COUNT(p.id) AS nb_produits,
    AVG(p.price) AS prix_moyen
FROM categories c
LEFT JOIN products p ON c.id = p.category_id
GROUP BY c.name
ORDER BY nb_produits DESC;

-- Commandes avec détails (vue)
SELECT * FROM order_details;

-- Inventaire des produits avec total vendu (vue)
SELECT * FROM product_inventory
ORDER BY total_sold DESC;

-- Top 5 des produits les plus vendus
SELECT 
    p.name,
    p.price,
    SUM(oi.quantity) as quantite_vendue,
    SUM(oi.quantity * oi.price) as revenu_total
FROM products p
JOIN order_items oi ON p.id = oi.product_id
GROUP BY p.id, p.name, p.price
ORDER BY quantite_vendue DESC
LIMIT 5;

-- Clients avec le plus de commandes
SELECT 
    u.username,
    u.full_name,
    COUNT(o.id) as nb_commandes,
    SUM(o.total_amount) as montant_total
FROM users u
JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.username, u.full_name
ORDER BY montant_total DESC;

-- Produits en rupture de stock
SELECT name, price, stock
FROM products
WHERE stock < 10
ORDER BY stock ASC;
```

---

## 🛠️ Commandes utiles

### Gestion du pod

```bash
# Voir les logs en temps réel
kubectl logs -f deployment/postgres

# Se connecter en shell au pod
kubectl exec -it deployment/postgres -- bash

# Redémarrer PostgreSQL
kubectl rollout restart deployment/postgres

# Vérifier l'état
kubectl get pods -l app=postgres
kubectl describe pod -l app=postgres
```

### Base de données

```bash
# Lister les bases de données
kubectl exec -it deployment/postgres -- psql -U postgres -c "\l"

# Lister les tables de la base 'demo'
kubectl exec -it deployment/postgres -- psql -U postgres -d demo -c "\dt"

# Exécuter une requête SQL
kubectl exec -it deployment/postgres -- psql -U postgres -d demo -c "SELECT COUNT(*) FROM users;"

# Voir la taille de la base
kubectl exec -it deployment/postgres -- psql -U postgres -d demo -c "SELECT pg_size_pretty(pg_database_size('demo'));"
```

### Backup et Restore

```bash
# Backup de la base 'demo'
kubectl exec deployment/postgres -- pg_dump -U postgres demo > backup-demo.sql

# Restore
cat backup-demo.sql | kubectl exec -i deployment/postgres -- psql -U postgres demo

# Backup en format custom (compressé)
kubectl exec deployment/postgres -- pg_dump -U postgres -Fc demo > backup-demo.dump
```

### Stockage

```bash
# Voir le PVC (Persistent Volume Claim)
kubectl get pvc postgres-pvc
kubectl describe pvc postgres-pvc

# Voir l'utilisation du stockage
kubectl exec deployment/postgres -- df -h /var/lib/postgresql/data
```

---

## 🔄 Réinitialiser la base de données

Si vous voulez réinitialiser la base avec les données de démo :

```bash
# Supprimer le deployment et le PVC
kubectl delete -f k8s/postgres-deployment.yaml
kubectl delete -f k8s/postgres-pvc.yaml

# Attendre quelques secondes, puis redéployer
kubectl apply -f k8s/postgres-pvc.yaml
kubectl apply -f k8s/postgres-deployment.yaml

# Le script d'initialisation sera ré-exécuté
```

---

## 🗑️ Nettoyage complet

```bash
# Supprimer tous les composants PostgreSQL
kubectl delete -f k8s/

# Vérifier que tout est supprimé
kubectl get all -l app=postgres
kubectl get pvc -l app=postgres
```

---

## 🔒 Sécurité - Production

⚠️ **Attention** : Les credentials par défaut sont **NON sécurisés** pour la production !

Pour la production, modifiez :

### 1. Changer le mot de passe

```bash
# Générer un nouveau mot de passe sécurisé
$password = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
echo $password

# Encoder en base64
$bytes = [System.Text.Encoding]::UTF8.GetBytes($password)
[Convert]::ToBase64String($bytes)

# Mettre à jour postgres-secret.yaml avec la valeur base64
```

### 2. Utiliser un Secret Kubernetes externe

```bash
# Créer un secret sans le committer dans Git
kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_USER=postgres \
  --from-literal=POSTGRES_PASSWORD=VotreMotDePasseSecurise123! \
  --from-literal=POSTGRES_DB=demo

# Puis supprimer k8s/postgres-secret.yaml de Git
```argocd-app.yaml                # Configuration ArgoCD
├── 

### 3. Changer le type de Service

Dans `k8s/postgres-service.yaml`, le type est `ClusterIP` (déjà sécurisé).
**Ne jamais utiliser** `LoadBalancer` ou `NodePort` pour PostgreSQL en production.

### 4. Ajuster les ressources

Dans `k8s/postgres-deployment.yaml`, augmentez les ressources selon vos besoins :

```yaml
resources:
  requests:
    memory: "512Mi"   # Minimum recommandé
    cpu: "500m"
  limits:
    memory: "2Gi"     # Selon vos besoins
    cpu: "2000m"
```

---

## 📁 Structure du projet

```
testk8s/
├── k8s/
│   ├── postgres-secret.yaml       # Credentials (user, password, db)
│   ├── postgres-configmap.yaml    # Script SQL d'initialisation
│   ├── postgres-pvc.yaml          # Stockage persistant (1Gi)
│   ├── postgres-deployment.yaml   # Deployment PostgreSQL 16
│   └── postgres-service.yaml      # Service ClusterIP
│
├── .gitignore
└── README.md                      # Ce fichier
```

---

## 🧪 Tests avancés

### Benchmark avec pgbench

```bash
# Initialiser pgbench dans la base 'demo'
kubectl exec -it deployment/postgres -- pgbench -i -U postgres -s 10 demo

# Lancer un test de performance
kubectl exec -it deployment/postgres -- pgbench -U postgres -c 10 -j 2 -t 1000 demo
```

### Connexion depuis une autre application

Si vous voulez connecter une application au même cluster :

```yaml
env:
- name: DB_HOST
  value: "postgres"          # Nom du service
- name: DB_PORT
  value: "5432"
- name: DB_NAME
  value: "demo"
- name: DB_USER
  valueFrom:
    secretKeyRef:
      name: postgres-secret
      key: POSTGRES_USER
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: postgres-secret
      key: POSTGRES_PASSWORD
```

---

## 🐛 Dépannage

### Le pod ne démarre pas

```bash
# Vérifier les events
kubectl describe pod -l app=postgres

# Vérifier si le PVC est bien bound
kubectl get pvc postgres-pvc

# Voir les logs
kubectl logs -l app=postgres --previous
```

### Problème de permission sur le PVC

```bash
# Se connecter au pod et vérifier les permissions
kubectl exec -it deployment/postgres -- ls -la /var/lib/postgresql/data
```

### La base n'est pas initialisée

Le script d'init ne s'exécute que si le répertoire de données est vide (premier démarrage).

Pour forcer une réinitialisation :
1. Supprimer le deployment : `kubectl delete -f k8s/postgres-deployment.yaml`
2. Supprimer le PVC : `kubectl delete -f k8s/postgres-pvc.yaml`
3. Recréer tout : `kubectl apply -f k8s/`

---

## 📚 Ressources

- [Documentation PostgreSQL](https://www.postgresql.org/docs/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [Kubernetes Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)

---

## 🎯 Utilisation

Ce projet est parfait pour :
- ✅ Apprendre Kubernetes avec un cas réel
- ✅ Tester des applications qui nécessitent une base de données
- ✅ Développer en local avec des données de démo
- ✅ Démonstrations et formations
- ✅ Base pour des projets plus complexes

**Stack** : PostgreSQL 16 Alpine, Kubernetes, Persistent Storage
