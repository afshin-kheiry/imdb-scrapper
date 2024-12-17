start-project:
	cron
	uvicorn core.base.main:app --host 0.0.0.0 --port 8000 --reload

start-scraping:
	export PYTHONPATH=/home/app && /usr/local/bin/python core/movies/scraper.py

quick-start:
	make initSwarm
	echo postgres_db | docker secret create imdb-movie-postgres-db -
	echo postgres_user | docker secret create imdb-movie-postgres-user -
	echo postgres_password | docker secret create imdb-movie-postgres-passwd -
	make env
	make build-image
	make deploy-to-swarm

build-image:
	docker build -f deployment/docker/DockerFile -t imdb-movie .

initSwarm:
	docker swarm init

deploy-to-swarm:
	docker stack deploy --compose-file deployment/docker/docker-compose.yml imdb-movie-stack

env:
	cp deployment/.env.sample .env

secrets:
	@read -p "Enter Staging Postgres DB Name:" imdb_movie_postgres_db; \
	read -p "Enter Staging Postgres User Name:" imdb_movie_postgres_user; \
	read -p "Enter Staging Postgres User Password:" imdb_movie_postgres_passwd; \
	echo $$imdb_movie_postgres_db | docker secret create imdb-movie-postgres-db -; \
	echo $$imdb_movie_postgres_user | docker secret create imdb-movie-postgres-user -; \
	echo $$imdb_movie_postgres_passwd | docker secret create imdb-movie-postgres-passwd -;
