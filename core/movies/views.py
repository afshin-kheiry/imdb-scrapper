from typing import Union, List

from fastapi import APIRouter, status

from core.base.database import db_dependency
from core.base.helpers import paginate
from core.base.auth import user_dependency
from core.movies.models import Cast, Language, Country, Movie
from core.movies.schema import MovieSchema


router = APIRouter(
    prefix="/movies",
    tags=["movies"]
)


@router.get("/", status_code=status.HTTP_200_OK, response_model=List[MovieSchema])
async def get_movies(
        user: user_dependency,
        db: db_dependency,
        page: int = 1, per_page: int = 10,
        casts: Union[str, None] = None,
        languages: Union[str, None] = None,
        countries: Union[str, None] = None,
        similar_movies: Union[str, None] = None
):
    query = db.query(Movie)

    if countries:
        countries = countries.split(",")
        query = query.join(Movie.countries).filter(Country.name.in_(countries))

    if languages:
        languages = languages.split(",")
        query = query.join(Movie.languages).filter(Language.name.in_(languages))

    if casts:
        casts = casts.split(",")
        query = query.join(Movie.casts).filter(Cast.name.in_(casts))

    if similar_movies:
        similar_movies = similar_movies.split(",")
        query = query.join(Movie.similar_movies, aliased=True).filter(
            Movie.title.in_(similar_movies))

    # TODO add filter by rating, rating_votes, release_date, title_type

    movies = paginate(query, page, per_page)
    return movies


# TODO add retrieve a single movie by title
