from sqlalchemy import (
    Column, ForeignKey, Integer, String,
    Float, Date, Table
)
from sqlalchemy.orm import relationship

from core.base.database import Base, engine


movie_country = Table(
    'movie_country', Base.metadata,
    Column('movie_id', Integer, ForeignKey('movie.id'), primary_key=True),
    Column('country_id', Integer, ForeignKey('country.id'), primary_key=True)
)

movie_language = Table(
    'movie_language', Base.metadata,
    Column('movie_id', Integer, ForeignKey('movie.id'), primary_key=True),
    Column('language_id', Integer, ForeignKey('language.id'), primary_key=True)
)

movie_cast = Table(
    'movie_cast', Base.metadata,
    Column('movie_id', Integer, ForeignKey('movie.id'), primary_key=True),
    Column('cast_id', Integer, ForeignKey('cast.id'), primary_key=True)
)

movie_genre = Table(
    'movie_genre', Base.metadata,
    Column('movie_id', Integer, ForeignKey('movie.id'), primary_key=True),
    Column('genre_id', Integer, ForeignKey('genre.id'), primary_key=True)
)

similar_movies = Table(
    'similar_movies', Base.metadata,
    Column('movie_id', Integer, ForeignKey('movie.id'), primary_key=True),
    Column('similar_movie_id', Integer, ForeignKey('movie.id'), primary_key=True)
)


class Cast(Base):
    __tablename__ = "cast"

    id = Column(Integer, primary_key=True)
    name = Column(String)

    movies = relationship(
        'Movie',
        secondary=movie_cast,
        back_populates='casts'
    )


class Language(Base):
    __tablename__ = "language"

    id = Column(Integer, primary_key=True)
    name = Column(String)

    movies = relationship(
        'Movie',
        secondary=movie_language,
        back_populates='languages'
    )


class Genre(Base):
    __tablename__ = "genre"

    id = Column(Integer, primary_key=True)
    name = Column(String)

    movies = relationship(
        'Movie',
        secondary=movie_genre,
        back_populates='genres'
    )


class Country(Base):
    __tablename__ = "country"

    id = Column(Integer, primary_key=True)
    name = Column(String)

    movies = relationship(
        'Movie',
        secondary=movie_country,
        back_populates='countries'
    )


class Movie(Base):
    __tablename__ = "movie"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    title_type = Column(String)
    description = Column(String)

    story_line = Column(String, nullable=True)
    rating = Column(Float, nullable=True)
    rating_votes = Column(Integer, nullable=True)
    release_date = Column(Date, nullable=True)

    countries = relationship(
        'Country',
        secondary=movie_country,
        back_populates='movies'
    )
    languages = relationship(
        'Language',
        secondary=movie_language,
        back_populates='movies'
    )
    casts = relationship(
        'Cast',
        secondary=movie_cast,
        back_populates='movies'
    )
    similar_movies = relationship(
        'Movie', secondary=similar_movies,
        primaryjoin=id == similar_movies.c.movie_id,
        secondaryjoin=id == similar_movies.c.similar_movie_id,
        backref='similar_to'
    )
    genres = relationship(
        'Genre',
        secondary=movie_genre,
        back_populates='movies'
    )


Base.metadata.create_all(engine)
