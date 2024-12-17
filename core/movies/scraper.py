import time
import requests
from datetime import datetime, timedelta

from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from decouple import config

from core.movies.models import Country, Movie, Cast, Language, Genre
from core.base.database import SessionLocal
from core.movies.constants import Selectors

session = SessionLocal()
openai = OpenAI(
  api_key=config('OPENAI_API_KEY')
)


class GetDataFromSourceMixin:
    @staticmethod
    def get_description(page_source):
        description_span = page_source.select_one(
            Selectors.description_css_selector
        )
        return description_span.get_text()

    @staticmethod
    def get_rating_votes(page_source):
        rating_el = page_source.find("div", Selectors.rating_votes_css_selector)
        rating_votes = rating_el.get_text(separator=" ", strip=True)
        if rating_votes[-1] == "K":
            rating_votes = float(rating_votes[:-1]) * 1000
        elif rating_votes[-1] == "M":
            rating_votes = float(rating_votes[:-1]) * 1000000
        return int(rating_votes)

    @staticmethod
    def get_title(page_source: BeautifulSoup):
        title_span = page_source.select_one(Selectors.title_css_selector)
        return title_span.get_text()

    @staticmethod
    def get_rating(page_source):
        rating_div = page_source.select_one(Selectors.rating_css_selector)
        return float(rating_div.get_text(separator=" ", strip=True))

    @staticmethod
    def get_top_cast(page_source):
        top_cast_section = page_source.find(attrs={
            "cel_widget_id": "StaticFeature_Cast"
        })
        if not top_cast_section:
            return []
        name_links = top_cast_section.find_all(
            "a",
            class_=Selectors.top_cast_a_css_selector
        )
        names = [
            name_link.get_text(separator=" ", strip=True)
            for name_link in name_links
        ]
        return names

    @staticmethod
    def get_countries(page_source: BeautifulSoup):
        country_section = page_source.find(attrs={
            "data-testid": "title-details-origin"
        })
        if not country_section:
            return []
        countries_links = country_section.find_all("a")
        countries = [
            country_link.get_text(separator=" ", strip=True)
            for country_link in countries_links
        ]
        return countries

    @staticmethod
    def get_languages(page_source: BeautifulSoup):
        language_section = page_source.find(attrs={
            "data-testid": "title-details-languages"
        })
        if not language_section:
            return []
        languages_links = language_section.find_all("a")
        languages = [
            language_link.get_text(separator=" ", strip=True)
            for language_link in languages_links
        ]
        return languages

    @staticmethod
    def get_similar(page_source: BeautifulSoup):
        similar_section = page_source.find(attrs={
            "cel_widget_id": "StaticFeature_MoreLikeThis"
        })
        if not similar_section:
            return []
        similar_parent_div = similar_section.find(
            "div",
            class_=Selectors.similar_parent_div_css_selector
        )
        similar_child_divs = similar_parent_div.find_all("div", recursive=False)
        similar_spans = [
            similar_div.select_one(Selectors.similar_spans_css_selector)
            for similar_div in similar_child_divs
        ]
        similars = [
            similar_span.get_text(separator=" ", strip=True)
            for similar_span in similar_spans
        ]
        return similars


class ImdbMovieScrapper(GetDataFromSourceMixin):
    def __init__(self, title_type="feature") -> None:
        options = webdriver.FirefoxOptions()
        options.add_argument("--no-sandbox")
        options.add_argument('--disable-dev-shm-usage')
        print("getting driver ..")
        self.driver = webdriver.Remote(
            command_executor="http://firefox:4444",
            options=options
        )
        print("driver is ready")
        self.base_url = "https://www.imdb.com/search/title/"
        movie = session.query(Movie).order_by(Movie.id.desc()).first()
        if not movie:
            self.release_date = "2010-01-01"
        else:
            self.release_date = str(movie.release_date + timedelta(days=1))
        self.title_type = title_type

    def get_url(self):
        _sort_query_string = "sort=release_date,asc"
        return f"{self.base_url}?title_type={self.title_type}&release_date=" \
               f"{self.release_date}&{_sort_query_string}&user_rating=4,"

    def load_all_movies(self):
        while True:
            time.sleep(5)
            elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                Selectors.load_more_data_css_selector)
            if not elements:
                break
            wait = WebDriverWait(self.driver, 10)
            button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, Selectors.load_more_data_css_selector)))
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", button)
            time.sleep(5)
            button.click()

    @staticmethod
    def save_data(data):
        print(f"{len(data)} movie has been extracted successfully.")
        cached_countries = {
            country.name: country
            for country in session.query(Country).all()
        }
        cached_genres = {
            genre.name: genre
            for genre in session.query(Genre).all()
        }
        cached_languages = {
            language.name: language
            for language in session.query(Language).all()
        }
        cached_casts = {
            cast.name: cast
            for cast in session.query(Cast).all()
        }
        cached_movies = {
            movie.title: movie
            for movie in session.query(Movie).all()
        }

        for movie in data:
            # Handling countries
            _countries = []
            for country_name in movie.pop("countries"):
                if country_name in cached_countries:
                    country = cached_countries[country_name]
                else:
                    country = Country(name=country_name)
                    session.add(country)
                    cached_countries[country_name] = country
                _countries.append(country)

            # Handling genres
            _genres = []
            for genre_name in movie.pop("genres"):
                if genre_name in cached_genres:
                    genre = cached_genres[genre_name]
                else:
                    genre = Genre(name=genre_name)
                    session.add(genre)
                    cached_genres[genre_name] = genre
                _genres.append(genre)

            # Handling languages
            _languages = []
            for language_name in movie.pop("languages"):
                if language_name in cached_languages:
                    language = cached_languages[language_name]
                else:
                    language = Language(name=language_name)
                    session.add(language)
                    cached_languages[language_name] = language
                _languages.append(language)

            # Handling casts
            _casts = []
            for cast_name in movie.pop("top_casts"):
                if cast_name in cached_casts:
                    cast = cached_casts[cast_name]
                else:
                    cast = Cast(name=cast_name)
                    session.add(cast)
                    cached_casts[cast_name] = cast
                _casts.append(cast)

            # Handling similar movies
            _similar_movies = []
            for similar_movie_title in movie.pop("similars"):
                if similar_movie_title in cached_movies:
                    similar_movie = cached_movies[similar_movie_title]
                else:
                    similar_movie = Movie(
                        title=similar_movie_title,
                        title_type="featured"
                    )
                    session.add(similar_movie)
                    cached_movies[similar_movie_title] = similar_movie
                if similar_movie not in _similar_movies:
                    _similar_movies.append(similar_movie)

            _movie = Movie(**movie)
            session.add(_movie)
            cached_movies[movie["title"]] = _movie

            _movie.countries.extend(_countries)
            _movie.genres.extend(_genres)
            _movie.languages.extend(_languages)
            _movie.casts.extend(_casts)
            _movie.similar_movies.extend(_similar_movies)
        session.commit()

    def run(self):
        self.driver.get(self.get_url())
        print("Loading All the movies ...")
        try:
            self.load_all_movies()
        except Exception as e:
            print(f"got this error:{e} while loading movies")
        print("All movies has been loaded.")
        data = list()
        try:
            data = self.get_movies_data()
        except Exception as e:
            print(f"got this error:{e} while extracting movies")
        try:
            self.save_data(data)
        except Exception as e:
            print(f"got this error:{e} while saving movies")

    @staticmethod
    def scape_url(url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.content  # Returns the raw HTML content
        else:
            print(f"Failed to fetch {url}. Status code: {response.status_code}")
            return None

    @staticmethod
    def generate_genres_and_storyline(title, description):
        prompt = f"Based on the following movie title and description," \
                 f"' generate appropriate genres and a storyline:\n\nTitle:" \
                 f" {title}\nDescription: {description}\n\nGenres:\nStoryline:"

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            n=1,
            stop=None,
            temperature=0.7
        )

        result = response.choices[0].message.to_dict()['content'].strip()
        genres, storyline = result.split("\nStoryline:")
        genres = genres.replace("Genres:", "").strip().split(", ")
        storyline = storyline.strip()
        return genres, storyline

    def extract_data(self, page_source):
        extracted_data = {
            "title": self.get_title(page_source),
            "description": self.get_description(page_source),
            "rating": self.get_rating(page_source),
            "rating_votes": self.get_rating_votes(page_source),
            "top_casts": self.get_top_cast(page_source),
            "similars": self.get_similar(page_source),
            "countries": self.get_countries(page_source),
            "languages": self.get_languages(page_source),
            "title_type": self.title_type,
            "release_date": datetime.strptime(
                self.release_date, "%Y-%m-%d").date()
        }
        try:
            genres, story_line = self.generate_genres_and_storyline(
                extracted_data.get("title"),
                extracted_data.get("description")
            )
        except Exception as e:
            print(f"got this error when trying to generate from ai:\n{e}")
            genres = []
            story_line = ""
        extracted_data.update({
            "genres": genres,
            "story_line": story_line
        })
        return extracted_data

    def get_movies_data(self):
        page_source = self.driver.page_source
        page_source = BeautifulSoup(page_source, 'html.parser')
        ul_element = page_source.find(
            'ul',
            class_=Selectors.main_page_ul_css_selector
        )
        links = ul_element.find_all('a')
        hrefs = {link.get('href') for link in links}
        movies_data = []
        print(f"{len(hrefs)} movies has been loaded")
        count = 0
        fails = dict()
        for href in hrefs:
            # extracting movies data
            try:
                full_url = requests.compat.urljoin(self.base_url, href)
                page_source = self.scape_url(full_url)
                if page_source:
                    page_source = BeautifulSoup(page_source, 'html.parser')
                    movies_data.append(self.extract_data(page_source))
                    count += 1
                    print(
                        f"processed: {count} movies data extracted successfully",
                        end="\r",
                        flush=True
                    )
            except Exception as e:
                print(f"got this error:{e} during extracting {href} this link.")
                fails[href] = e
        print(fails)
        return movies_data


if "__main__" == __name__:
    ImdbMovieScrapper().run()




