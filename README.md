# imdb-scraping
serving scraped data from imdb with fastapi

## Installation
```
make quick-start
or
make initSwarm
make secrets
make env
make build-image
make deploy-to-swarm

NOTE:
if you have already a swarm you need to run this command:
docker swarm leave --force
```

you also need .env with following keys in it:
```
SQLALCHEMY_DATABASE_URL
SECRET_KEY
OPENAI_API_KEY
```
