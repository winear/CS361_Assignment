from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


# -----------------------------
# Files (CSV storage)
# -----------------------------
USERS_FILE = Path("users.csv")
MOVIES_FILE = Path("movies.csv")

USERS_FIELDS = ["username", "password"]
MOVIES_FIELDS = ["username", "movie_name", "director", "genre", "rating", "year", "watched"]

# Basic validation bounds
MIN_YEAR = 1888
MAX_YEAR = 2100
MIN_RATING = 0.0
MAX_RATING = 10.0


# -----------------------------
# Data model
# -----------------------------
@dataclass
class Movie:
    username: str
    movie_name: str
    director: str
    genre: str
    rating: str  # stored as text in CSV
    year: str    # stored as text in CSV
    watched: str # "Y" or "N"


# -----------------------------
# File bootstrap
# -----------------------------
def ensure_csv_file(path: Path, header: List[str], seed_rows: List[dict] | None = None) -> None:
    """Create a CSV file with the given header if it doesn't exist."""
    if path.exists():
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        if seed_rows:
            for row in seed_rows:
                writer.writerow(row)


# -----------------------------
# Users / Login
# -----------------------------
def load_users() -> Dict[str, str]:
    """Load users.csv into a dict: {username: password}."""
    users: Dict[str, str] = {}
    with USERS_FILE.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            u = (row.get("username") or "").strip()
            p = (row.get("password") or "").strip()
            if u:
                users[u] = p
    return users


def authenticate(users: Dict[str, str]) -> str:
    """Login loop. Returns username on success."""
    print("=================================")
    print(" Welcome to Personal Movie List ")
    print("=================================")
    print(" Keep track of your favorite movies ")
    print(" Create a list of movies you want to watch ")
    print("=================================")

    while True:
        username = input("Username: ").strip()
        password = input("Password: ").strip()

        if username in users and users[username] == password:
            print(f"\nLogin successful. Welcome, {username}!\n")
            return username

        print("\nLogin failed. Invalid username or password. Please try again.\n")


# -----------------------------
# Movies (load / save)
# -----------------------------
def load_movies_for_user(username: str) -> List[Movie]:
    """Read movies.csv and return Movie objects for the given user."""
    movies: List[Movie] = []
    with MOVIES_FILE.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get("username") or "").strip() != username:
                continue

            movies.append(Movie(
                username=username,
                movie_name=(row.get("movie_name") or "").strip(),
                director=(row.get("director") or "").strip(),
                genre=(row.get("genre") or "").strip(),
                rating=(row.get("rating") or "").strip(),
                year=(row.get("year") or "").strip(),
                watched=(row.get("watched") or "").strip().upper(),
            ))
    return movies


def append_movie(movie: Movie) -> None:
    """Append a new movie row to movies.csv."""
    with MOVIES_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MOVIES_FIELDS)
        writer.writerow({
            "username": movie.username,
            "movie_name": movie.movie_name,
            "director": movie.director,
            "genre": movie.genre,
            "rating": movie.rating,
            "year": movie.year,
            "watched": movie.watched,
        })


def load_all_movie_rows() -> List[dict]:
    """Load all rows from movies.csv as dicts (including other users)."""
    rows: List[dict] = []
    with MOVIES_FILE.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({k: (row.get(k) or "") for k in MOVIES_FIELDS})
    return rows


def save_all_movie_rows(rows: List[dict]) -> None:
    """Rewrite movies.csv with the given rows."""
    with MOVIES_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MOVIES_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: (row.get(k) or "") for k in MOVIES_FIELDS})


def movie_row_matches(row: dict, mv: Movie) -> bool:
    """Match a CSV row to a Movie by all fields (safe for duplicates)."""
    return (
        (row.get("username") or "").strip() == mv.username
        and (row.get("movie_name") or "").strip() == mv.movie_name
        and (row.get("director") or "").strip() == mv.director
        and (row.get("genre") or "").strip() == mv.genre
        and (row.get("rating") or "").strip() == mv.rating
        and (row.get("year") or "").strip() == mv.year
        and (row.get("watched") or "").strip().upper() == (mv.watched or "").strip().upper()
    )


def delete_movie_record(username: str, movie_to_delete: Movie) -> bool:
    """
    Delete ONE matching movie record for this user from movies.csv.
    Returns True if deleted, False if not found.
    """
    rows = load_all_movie_rows()
    deleted = False
    new_rows: List[dict] = []

    for row in rows:
        if not deleted and (row.get("username") or "").strip() == username and movie_row_matches(row, movie_to_delete):
            deleted = True
            continue
        new_rows.append(row)

    if deleted:
        save_all_movie_rows(new_rows)

    return deleted


def update_movie_record(username: str, old_movie: Movie, new_movie: Movie) -> bool:
    """
    Update ONE matching movie record for this user in movies.csv.
    Returns True if updated, False if not found.
    """
    rows = load_all_movie_rows()
    updated = False

    for row in rows:
        if not updated and (row.get("username") or "").strip() == username and movie_row_matches(row, old_movie):
            # Replace fields (keep username consistent)
            row["username"] = username
            row["movie_name"] = new_movie.movie_name
            row["director"] = new_movie.director
            row["genre"] = new_movie.genre
            row["rating"] = new_movie.rating
            row["year"] = new_movie.year
            row["watched"] = new_movie.watched
            updated = True
            break

    if updated:
        save_all_movie_rows(rows)

    return updated


# -----------------------------
# CLI helpers
# -----------------------------
def prompt_non_empty(prompt: str) -> str:
    while True:
        v = input(prompt).strip()
        if v:
            return v
        print("This field cannot be empty. Please try again.")


def prompt_optional(prompt: str) -> str:
    return input(prompt).strip()


def prompt_rating(prompt: str) -> str:
    """Optional rating. If provided: numeric 0..10. Stored as text."""
    while True:
        v = input(prompt).strip()
        if v == "":
            return ""
        try:
            r = float(v)
            if MIN_RATING <= r <= MAX_RATING:
                return str(int(r)) if r.is_integer() else str(r)
        except ValueError:
            pass
        print(f"Invalid rating. Enter a number between {MIN_RATING} and {MAX_RATING}, or leave blank.")


def prompt_year(prompt: str) -> str:
    """Optional year. If provided: integer 1888..2100. Stored as text."""
    while True:
        v = input(prompt).strip()
        if v == "":
            return ""
        if v.isdigit():
            yr = int(v)
            if MIN_YEAR <= yr <= MAX_YEAR:
                return v
        print(f"Invalid year. Enter a number between {MIN_YEAR} and {MAX_YEAR}, or leave blank.")


def prompt_watched(prompt: str) -> str:
    """Required Y/N."""
    while True:
        v = input(prompt).strip().upper()
        if v in {"Y", "N"}:
            return v
        print("Invalid input. Please enter Y or N.")


def confirm_yes_no(prompt: str) -> bool:
    """Return True for Y, False for N."""
    while True:
        v = input(prompt).strip().upper()
        if v in {"Y", "N"}:
            return v == "Y"
        print("Please enter Y or N.")


def print_movie_details(mv: Movie) -> None:
    """Print a single movie's details (used by View Movies detail screen)."""
    title = mv.movie_name or "(Untitled)"
    director = mv.director or "-"
    genre = mv.genre or "-"
    rating = mv.rating or "-"
    year = mv.year or "-"
    watched_raw = (mv.watched or "-").upper()

    if watched_raw == "Y":
        watched = "Yes"
    elif watched_raw == "N":
        watched = "No"
    else:
        watched = watched_raw

    print("\n--- Movie Details ---")
    print(f"Title:    {title}")
    print(f"Director: {director}")
    print(f"Genre:    {genre}")
    print(f"Rating:   {rating}")
    print(f"Year:     {year}")
    print(f"Watched:  {watched}")
    print("---------------------\n")


def prompt_edit_field(label: str, current_value: str, validator=None) -> str:
    """
    Edit prompt:
    - Shows current value
    - User presses Enter to keep it
    - Otherwise validate (if validator provided) and return new value
    """
    while True:
        v = input(f"{label} [{current_value if current_value else '-'}] (press Enter to keep): ").strip()
        if v == "":
            return current_value
        if validator:
            ok, normalized_or_msg = validator(v)
            if ok:
                return normalized_or_msg
            print(normalized_or_msg)
            continue
        return v


def validate_rating_input(v: str) -> Tuple[bool, str]:
    try:
        r = float(v)
        if MIN_RATING <= r <= MAX_RATING:
            return True, (str(int(r)) if r.is_integer() else str(r))
    except ValueError:
        pass
    return False, f"Invalid rating. Enter {MIN_RATING}–{MAX_RATING}."


def validate_year_input(v: str) -> Tuple[bool, str]:
    if v.isdigit():
        yr = int(v)
        if MIN_YEAR <= yr <= MAX_YEAR:
            return True, v
    return False, f"Invalid year. Enter {MIN_YEAR}–{MAX_YEAR}."


def validate_watched_input(v: str) -> Tuple[bool, str]:
    vv = v.strip().upper()
    if vv in {"Y", "N"}:
        return True, vv
    return False, "Invalid watched value. Enter Y or N."


# -----------------------------
# Commands
# -----------------------------
def view_movies(username: str) -> None:
    """
    View Movies (two-level + delete + edit from details):
    - Show numbered titles list
    - Choose:
        * movie number -> open details screen
        * B -> back to Home
    - Details screen:
        * E -> edit this movie (press Enter to keep field)
        * D -> delete this movie (double-confirm)
        * Enter -> back to movie list
    """
    while True:
        print("\n--- View Movies ---")
        movies = load_movies_for_user(username)

        if not movies:
            print("No movies found.\n")
            return  # back to Home menu

        for i, mv in enumerate(movies, start=1):
            title = mv.movie_name if mv.movie_name else "(Untitled)"
            print(f"{i}. {title}")

        print("\nEnter a movie number to view details, or B to go back to Home.")
        choice = input("Your choice: ").strip().lower()

        if choice in {"b", "back"}:
            print()
            return

        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(movies):
                selected = movies[idx - 1]

                while True:
                    print_movie_details(selected)
                    print("Options: [E] Edit   [D] Delete   [Enter] Back to movie list")
                    sub = input("Your choice: ").strip().lower()

                    if sub in {"", "b", "back"}:
                        break

                    if sub in {"d", "del", "delete"}:
                        if confirm_yes_no("Are you sure you want to delete this movie? (Y/N): "):
                            if delete_movie_record(username, selected):
                                print("\nDeleted successfully.\n")
                            else:
                                print("\nDelete failed: movie not found.\n")
                            break  # back to movie list (refresh)
                        else:
                            print("\nDelete canceled.\n")
                            continue

                    if sub in {"e", "edit"}:
                        print("\n--- Edit Movie ---")
                        print("Tip: Press Enter to keep the current value.\n")

                        new_title = prompt_edit_field("Movie name", selected.movie_name, validator=lambda x: (True, x) if x else (False, "Movie name cannot be empty."))
                        new_director = prompt_edit_field("Director", selected.director)
                        new_genre = prompt_edit_field("Genre", selected.genre)
                        new_rating = prompt_edit_field("Rating (0-10)", selected.rating, validator=validate_rating_input) if True else selected.rating
                        new_year = prompt_edit_field("Year", selected.year, validator=validate_year_input) if True else selected.year
                        new_watched = prompt_edit_field("Watched (Y/N)", selected.watched, validator=validate_watched_input)

                        updated_movie = Movie(
                            username=username,
                            movie_name=new_title,
                            director=new_director,
                            genre=new_genre,
                            rating=new_rating,
                            year=new_year,
                            watched=new_watched,
                        )

                        if confirm_yes_no("Save changes? (Y/N): "):
                            if update_movie_record(username, selected, updated_movie):
                                print("\nUpdated successfully.\n")
                                # Update in-memory selected so details reflect changes immediately
                                selected = updated_movie
                            else:
                                print("\nUpdate failed: movie not found.\n")
                        else:
                            print("\nEdit canceled.\n")

                        continue

                    print("\nInvalid input. Type E to edit, D to delete, or press Enter to go back.\n")

                continue

        print("\nInvalid input. Please enter a valid movie number or B.\n")


def add_movie(username: str) -> None:
    """Prompt user for movie fields and append to CSV."""
    print("\n--- Add Movie ---")
    movie_name = prompt_non_empty("Movie name (required): ")
    director = prompt_optional("Director (optional): ")
    genre = prompt_optional("Genre (optional): ")
    rating = prompt_rating("Rating 0-10 (optional): ")
    year = prompt_year("Year (optional): ")
    watched = prompt_watched("Watched? (Y/N, required): ")

    movie = Movie(
        username=username,
        movie_name=movie_name,
        director=director,
        genre=genre,
        rating=rating,
        year=year,
        watched=watched,
    )

    append_movie(movie)
    print("\nMovie added successfully.\n")


def delete_movie_from_home(username: str) -> None:
    """
    Delete Movie (Home menu):
    - Show titles list
    - Ask for movie number to delete or B to cancel
    - Show details + confirm
    """
    while True:
        print("\n--- Delete Movie ---")
        movies = load_movies_for_user(username)

        if not movies:
            print("No movies found.\n")
            return

        for i, mv in enumerate(movies, start=1):
            title = mv.movie_name if mv.movie_name else "(Untitled)"
            print(f"{i}. {title}")

        print("\nEnter a movie number to delete, or B to go back to Home.")
        choice = input("Your choice: ").strip().lower()

        if choice in {"b", "back"}:
            print()
            return

        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(movies):
                target = movies[idx - 1]
                print_movie_details(target)
                if confirm_yes_no("Are you sure you want to delete this movie? (Y/N): "):
                    if delete_movie_record(username, target):
                        print("\nDeleted successfully.\n")
                    else:
                        print("\nDelete failed: movie not found.\n")
                    return
                else:
                    print("\nDelete canceled.\n")
                    return

        print("\nInvalid input. Please enter a valid movie number or B.\n")


def home_menu(username: str) -> None:
    """Home menu with commands: View Movies, Add Movie, Delete Movie."""
    while True:
        print("=== Home ===")
        print("1) View Movies")
        print("2) Add Movie")
        print("3) Delete Movie")
        print("Q) Quit")
        print("=================================")
        print(" Help: ")
        print(" You can view specific movie details after you (1)view the movies. ")
        print(" You can edit or delete the movie information in movie details. ")
        print(" You can also delete the movie in (4)delete movie. ")
        print("=================================")

        choice = input("Select a command: ").strip().lower()

        if choice == "1":
            view_movies(username)
        elif choice == "2":
            add_movie(username)
        elif choice == "3":
            delete_movie_from_home(username)
        elif choice in {"q", "quit", "exit"}:
            print("\nGoodbye!\n")
            return
        else:
            print("\nInvalid command. Please choose 1, 2, 3, or Q.\n")


# -----------------------------
# Main
# -----------------------------
def main() -> None:
    # Create CSVs if missing (seed users so you can test immediately)
    ensure_csv_file(
        USERS_FILE,
        USERS_FIELDS,
        seed_rows=[
            {"username": "demo", "password": "demo123"},
            {"username": "alice", "password": "password"},
        ],
    )
    ensure_csv_file(MOVIES_FILE, MOVIES_FIELDS)

    users = load_users()
    username = authenticate(users)
    home_menu(username)


if __name__ == "__main__":
    main()
