# noethysweb_docker

Docker pour l'installation de noethysweb


Pour démarrer l'application (application django), docker-compose est nécessaire, puis:
```
docker-compose up django
```

Si aucun serveur web n'existe sur l'hôte, il est possible d'utiliser le service nginx. Noethysweb sera disponible sur le port 80

```
docker-compose up nginx
```

## HTTPS

Pour une configuration HTTPS, utiliser certbot et le plugin certbot nginx par exemple (un domaine dédié est nécessaire)

## Premier démarrage

Copier `django/settings_production.py.sample` en `django/settings_production.py`

Si installé sur un domaine dédié, l'ajouter à ALLOWED_HOSTS dans `django/settings_production.py`

Initialisation:
```
docker-compose exec django /app/reset.sh <superuser_email> <superuser_name> <superuser_password>
```

- Se connecter à `http://127.0.0.1/utilisateur` avec les droits super utilisateur
- Créer une "structure"
- Se connecter à `http://127.0.0.1/administrateur` avec les droits super utilisateur
- Créer les utilisateurs et les affecter à la structure créée plus haut


La base de données se trouve dans `db/db.sqlite3`



