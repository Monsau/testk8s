# Hello World avec ArgoCD 🚀

Projet de démonstration pour tester le déploiement continu avec ArgoCD sur Kubernetes.

## 📋 Structure du Projet

```
testk8s/
├── app.py                    # Application Flask Hello World
├── requirements.txt          # Dépendances Python
├── Dockerfile               # Image Docker
├── k8s/                     # Manifestes Kubernetes
│   ├── deployment.yaml
│   └── service.yaml
└── argocd/                  # Configuration ArgoCD
    └── application.yaml
```

## 🔧 Prérequis

- Docker Desktop avec Kubernetes activé
- kubectl configuré
- ArgoCD installé sur votre cluster local

## 📦 Étape 1 : Build et Push de l'image Docker

```bash
# Build de l'image
docker build -t ghcr.io/monsau/testk8s:latest .

# Login à GitHub Container Registry
docker login ghcr.io -u Monsau

# Push de l'image
docker push ghcr.io/monsau/testk8s:latest
```

## ☸️ Étape 2 : Installation d'ArgoCD (si pas déjà installé)

```bash
# Créer le namespace
kubectl create namespace argocd

# Installer ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Attendre que tous les pods soient prêts
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s

# Exposer ArgoCD (port-forward)
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

## 🔑 Récupérer le mot de passe ArgoCD

```bash
# Windows PowerShell
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
```

Interface ArgoCD : https://localhost:8080
- Username : `admin`
- Password : (celui récupéré ci-dessus)

## 🚀 Étape 3 : Déployer l'application avec ArgoCD

```bash
# Appliquer la configuration ArgoCD
kubectl apply -f argocd/application.yaml

# Vérifier le statut
kubectl get applications -n argocd
```

Ou via l'interface ArgoCD :
1. Aller sur https://localhost:8080
2. Cliquer sur l'application "hello-world"
3. Cliquer sur "SYNC" puis "SYNCHRONIZE"

## 🧪 Étape 4 : Tester l'application

```bash
# Vérifier les pods
kubectl get pods -l app=hello-world

# Vérifier le service
kubectl get svc hello-world

# Accéder à l'application
# Si LoadBalancer est disponible : http://localhost
# Sinon faire un port-forward :
kubectl port-forward svc/hello-world 3000:80
```

Puis ouvrir : http://localhost:3000

## 🔄 Étape 5 : Tester la synchronisation automatique

Pour voir ArgoCD détecter et appliquer les changements :

1. **Modifier la version dans le deployment** :
   ```bash
   # Éditer k8s/deployment.yaml et changer VERSION de "1.0" à "2.0"
   ```

2. **Commit et push** :
   ```bash
   git add k8s/deployment.yaml
   git commit -m "Update version to 2.0"
   git push
   ```

3. **Observer ArgoCD** :
   - ArgoCD détecte le changement (par défaut toutes les 3 minutes)
   - L'application se synchronise automatiquement
   - Rafraîchir http://localhost:3000 pour voir "Version: 2.0"

## 🎨 Modifier le contenu de l'application

Pour tester un changement plus visible :

1. **Modifier** [app.py](app.py) (changer le texte, les couleurs, etc.)

2. **Rebuild et push l'image** :
   ```bash
   docker build -t ghcr.io/monsau/testk8s:latest .
   docker push ghcr.io/monsau/testk8s:latest
   ```

3. **Forcer le redéploiement** :
   ```bash
   kubectl rollout restart deployment/hello-world
   ```

   Ou via ArgoCD : Hard Refresh puis Sync

## 🛠️ Commandes Utiles

```bash
# Voir les logs de l'application
kubectl logs -l app=hello-world -f

# Voir le statut ArgoCD
kubectl get applications -n argocd

# Forcer une synchronisation ArgoCD immédiate
kubectl patch application hello-world -n argocd --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'

# Supprimer l'application
kubectl delete -f argocd/application.yaml
kubectl delete -f k8s/
```

## 📝 Notes

- **Synchronisation automatique** : ArgoCD est configuré avec `automated: true` pour synchroniser automatiquement les changements du dépôt Git
- **Self-Heal** : Si quelqu'un modifie manuellement les ressources Kubernetes, ArgoCD les rétablit automatiquement
- **Prune** : Les ressources supprimées du Git sont automatiquement supprimées du cluster

## 🐛 Dépannage

**L'application ne démarre pas :**
```bash
kubectl describe pod -l app=hello-world
kubectl logs -l app=hello-world
```

**ArgoCD ne synchronise pas :**
- Vérifier que le dépôt Git est accessible
- Vérifier les credentials si le dépôt est privé
- Forcer une hard refresh dans l'interface ArgoCD

**L'image ne peut pas être pullée :**
- Vérifier que l'image est publique sur ghcr.io
- Ou créer un secret pour les images privées
