# noethysweb_docker
Docker for Noethysweb


Django app on port 8000
```
docker-compose up django
```

Nginx server serving noethysweb

```
docker-compose up nginx
```

## First run

```
docker-compose exec django /app/reset.sh <superuser_email> <superuser_name> <superuser_password>
```

Connect to `http://127.0.0.1/administrateur` with the super user credentials.

The database file is in `/db/db.sqlite3`


