from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class CastSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class LanguageSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class CountrySchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class GenreSchema(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class MovieSchema(BaseModel):
    id: int
    title: str
    title_type: Optional[str]
    description: Optional[str]
    story_line: Optional[str]
    rating: Optional[float]
    rating_votes: Optional[int]
    release_date: Optional[date]
    countries: List[CountrySchema] = []
    languages: List[LanguageSchema] = []
    casts: List[CastSchema] = []
    genres: List[GenreSchema] = []
    similar_movies: List['MovieSchema'] = []

    class Config:
        orm_mode = True


MovieSchema.update_forward_refs()
