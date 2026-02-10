# 🚀 Hello World with ArgoCD & PostgreSQL

Projet de démonstration complet montrant le déploiement continu avec ArgoCD sur Kubernetes, incluant une application Flask et une base de données PostgreSQL.

## 📦 Composants

- **Application Flask** : Interface web avec API REST
- **PostgreSQL** : Base de données avec données de démonstration
- **Kubernetes** : Manifestes pour le déploiement
- **ArgoCD** : GitOps pour la synchronisation automatique

## 🎯 Objectif

Voir ArgoCD détecter automatiquement les changements sur GitHub et les appliquer sur le cluster Kubernetes local.

---

## 🚀 Déploiement complet

### 1️⃣ Préparer l'image Docker

```bash
# Build l'image
docker build -t ghcr.io/monsau/testk8s:latest .

# Login à GitHub Container Registry
docker login ghcr.io -u Monsau

# Push l'image
docker push ghcr.io/monsau/testk8s:latest
```

> 💡 **Tip** : Rendez le package public sur GitHub : Settings → Packages → testk8s → Change visibility → Public

### 2️⃣ Installer ArgoCD

```bash
# Créer le namespace
kubectl create namespace argocd

# Installer ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Attendre que tout soit prêt (1-2 minutes)
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s
```

### 3️⃣ Accéder à ArgoCD

```bash
# Exposer l'interface ArgoCD
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

**Récupérer le mot de passe** (dans un autre terminal) :
```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
```

Connectez-vous sur **https://localhost:8080**
- Username : `admin`
- Password : (celui récupéré ci-dessus)

### 4️⃣ Déployer l'application via ArgoCD

```bash
# Créer l'application ArgoCD
kubectl apply -f argocd/application.yaml

# Vérifier le statut
kubectl get applications -n argocd
```

Dans l'interface ArgoCD :
1. Cliquez sur l'application **hello-world**
2. Cliquez sur **SYNC** → **SYNCHRONIZE**
3. Observez le déploiement en temps réel ! 🎉

### 5️⃣ Accéder aux applications

**Application Flask** :
```bash
kubectl port-forward svc/hello-world 3000:80
```
Ouvrir : http://localhost:3000

**PostgreSQL** (pour tests) :
```bash
kubectl port-forward svc/postgres 5432:5432
# Puis : psql -h localhost -U postgres -d demo
# Password : admin123
```

---

## 🔄 Tester la synchronisation automatique ArgoCD

### Méthode 1 : Changer la version

1. **Modifier** [k8s/deployment.yaml](k8s/deployment.yaml) ligne 23 :
   ```yaml
   - name: VERSION
     value: "2.0"  # Changez de 1.0 à 2.0
   ```

2. **Commit et push** :
   ```bash
   git add k8s/deployment.yaml
   git commit -m "Update version to 2.0"
   git push
   ```

3. **Observer ArgoCD** :
   - ArgoCD détecte le changement (max 3 minutes)
   - Synchronisation automatique
   - Rafraîchir http://localhost:3000 → "Version: 2.0" ✨

### Méthode 2 : Modifier le nombre de replicas

1. **Modifier** [k8s/deployment.yaml](k8s/deployment.yaml) ligne 9 :
   ```yaml
   replicas: 3  # Changez de 2 à 3
   ```

2. **Commit et push** :
   ```bash
   git add k8s/deployment.yaml
   git commit -m "Scale to 3 replicas"
   git push
   ```

3. **Vérifier** :
   ```bash
   kubectl get pods -l app=hello-world
   # Vous verrez 3 pods après la synchronisation ArgoCD
   ```

---

## 🐘 Base de données PostgreSQL

La base de données est automatiquement initialisée avec :

### 📊 Structure
- **5 tables** : users, categories, products, orders, order_items
- **Données de démo** : 5 utilisateurs, 11 produits, 5 commandes
- **2 vues SQL** : order_details, product_inventory

### 🔑 Credentials
- **User** : `postgres`
- **Password** : `admin123`
- **Database** : `demo`

### 🌐 API Endpoints

L'application Flask expose plusieurs endpoints :

- **GET /** → Page d'accueil avec liens
- **GET /health** → Health check (inclut status DB)
- **GET /api/stats** → Statistiques de la base
- **GET /api/users** → Liste des utilisateurs
- **GET /api/products** → Liste des produits
- **GET /api/orders** → Liste des commandes

Exemple :
```bash
curl http://localhost:3000/api/stats
# Retourne : nombre d'users, products, orders, total_sales
```

### 📖 Guide détaillé PostgreSQL
Voir [POSTGRES.md](POSTGRES.md) pour :
- Requêtes SQL de test
- Commandes de backup/restore
- Connexion et debugging
- Configuration avancée

---

## 📁 Structure du projet

```
testk8s/
├── app.py                          # Application Flask avec connexion DB
├── requirements.txt                # Dépendances Python
├── Dockerfile                      # Image Docker
│
├── k8s/                            # Manifestes Kubernetes
│   ├── deployment.yaml             # Deployment de l'application
│   ├── service.yaml                # Service de l'application
│   ├── postgres-secret.yaml        # Credentials PostgreSQL
│   ├── postgres-configmap.yaml     # Script d'initialisation SQL
│   ├── postgres-pvc.yaml           # Stockage persistant
│   ├── postgres-deployment.yaml    # Deployment PostgreSQL
│   └── postgres-service.yaml       # Service PostgreSQL
│
├── argocd/
│   └── application.yaml            # Configuration ArgoCD
│
├── README.md                       # Ce fichier
└── POSTGRES.md                     # Guide PostgreSQL détaillé
```

---

## 🛠️ Commandes utiles

### Application
```bash
# Logs de l'application
kubectl logs -l app=hello-world -f

# Redémarrer l'application
kubectl rollout restart deployment/hello-world

# Scale l'application
kubectl scale deployment hello-world --replicas=5
```

### PostgreSQL
```bash
# Logs PostgreSQL
kubectl logs -l app=postgres -f

# Se connecter à PostgreSQL
kubectl exec -it deployment/postgres -- psql -U postgres -d demo

# Liste des tables
kubectl exec -it deployment/postgres -- psql -U postgres -d demo -c "\dt"
```

### ArgoCD
```bash
# Status de l'application
kubectl get applications -n argocd

# Forcer une synchronisation immédiate
kubectl patch application hello-world -n argocd --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'

# Voir les logs ArgoCD
kubectl logs -n argocd deployment/argocd-server -f
```

### Nettoyage
```bash
# Supprimer l'application (garde la DB)
kubectl delete -f k8s/deployment.yaml
kubectl delete -f k8s/service.yaml

# Supprimer PostgreSQL
kubectl delete -f k8s/postgres-deployment.yaml
kubectl delete -f k8s/postgres-service.yaml

# Supprimer aussi le stockage (reset complet)
kubectl delete -f k8s/postgres-pvc.yaml

# Supprimer l'application ArgoCD
kubectl delete -f argocd/application.yaml

# Désinstaller ArgoCD complètement
kubectl delete namespace argocd
```

---

## 🎯 Cas d'usage pédagogiques

### 1. GitOps avec ArgoCD
Modifier n'importe quel fichier dans `k8s/`, commit, push → ArgoCD synchronise automatiquement

### 2. Mise à l'échelle
Changer le nombre de replicas → Observer ArgoCD créer/détruire les pods

### 3. Rollback
ArgoCD garde l'historique → Rollback en 1 clic dans l'interface

### 4. Configuration as Code
Changer les variables d'environnement, secrets, ressources → S'applique automatiquement

### 5. Multi-environnements
Créer des branches `dev`, `staging`, `prod` avec différentes configs ArgoCD

---

## 🐛 Dépannage

### L'application ne se connecte pas à PostgreSQL
```bash
# Vérifier que PostgreSQL est prêt
kubectl get pods -l app=postgres

# Vérifier les logs de l'app
kubectl logs -l app=hello-world

# Tester la connexion réseau
kubectl exec -it deployment/hello-world -- ping postgres
```

### ArgoCD ne synchronise pas
- Vérifier que le repo GitHub est accessible (public)
- Forcer un "Hard Refresh" dans l'interface ArgoCD
- Vérifier les logs : `kubectl logs -n argocd deployment/argocd-application-controller`

### L'image Docker ne peut pas être pullée
```bash
# Vérifier que l'image existe
docker pull ghcr.io/monsau/testk8s:latest

# Rendre le package public sur GitHub
# Ou créer un imagePullSecret pour les images privées
```

### Les pods redémarrent en boucle
```bash
# Voir les raisons
kubectl describe pod -l app=hello-world

# Vérifier les ressources
kubectl top nodes
kubectl top pods
```

---

## 📚 Prochaines étapes

- [ ] Ajouter des tests automatisés
- [ ] Mettre en place un Ingress pour l'accès HTTP
- [ ] Configurer Prometheus + Grafana pour le monitoring
- [ ] Ajouter des migrations de base de données (Liquibase/Flyway)
- [ ] Créer des environnements dev/staging/prod
- [ ] Implémenter un cache Redis
- [ ] Ajouter des webhooks GitHub pour notification ArgoCD

---

## 🤝 Auteur

Projet de démonstration pour apprendre ArgoCD et GitOps sur Kubernetes.

**Stack technique** : Python Flask, PostgreSQL, Docker, Kubernetes, ArgoCD
