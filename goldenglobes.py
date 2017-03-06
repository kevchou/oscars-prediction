import re
import requests
from bs4 import BeautifulSoup
import pandas as pd

GG_DRAMA = "http://www.goldenglobes.com/winners-nominees/best-motion-picture-drama/all-years"
GG_COMEDY = "http://www.goldenglobes.com/winners-nominees/best-motion-picture-musical-or-comedy/all-years"

def get_soup(url):
    """Returns a BeautifulSoup object from input url"""
    return BeautifulSoup(requests.get(url).text, 'lxml')

def fix_movie_title(movie):
    words = ["A", "An", "The"]
    
    for word in words:
        if movie.endswith(', ' + word):
            movie = word + " " + movie[:len(movie) - len(word) - 2]
            break
    
    return movie


def get_gg_winners(url):
    soup = get_soup(url)
    
    all_noms_years = soup.findAll("div", attrs={"id": re.compile("year-([0-9]{4})")})
    gg_winners = []
    
    for year in all_noms_years:
        curr_year = year.getText()
        year_contents = year.findNext().findNext()
        
        year_movies = year_contents.findAll("div", attrs={"class": "views-field-nominee-title"})
        year_winners = year_contents.findAll("div", attrs={"class": "views-field-field-nomination-is-winner"})
        
        winner_ix = [x.getText().strip() == 'Winner' for x in year_winners].index(True)
        nominated_movies = [x.getText().strip() for x in year_movies]
        winning_movie = fix_movie_title(nominated_movies[winner_ix])
        
        print(curr_year, winning_movie)
        gg_winners.append({'Year': curr_year, 'Movie': winning_movie})
    
    return gg_winners


def main():
    print("Webscraping Golden Globe winners...")
    
    print("\nFetching winners for Best Drama")
    drama_df = pd.DataFrame(get_gg_winners(GG_DRAMA))
    drama_df.to_csv('gg_drama.csv', index=False)

    print("\nFetching winners for Best Comedy")
    comedy_df = pd.DataFrame(get_gg_winners(GG_COMEDY))
    comedy_df.to_csv('gg_comedy.csv', index=False)

if __name__ == '__main__':
    main()
