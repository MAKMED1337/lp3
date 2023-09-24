source env/database.env
docker compose exec -it db pg_dump -U $POSTGRES_USER -d $POSTGRES_DB > backup/$(date +%"F-%T").sql
