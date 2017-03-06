import re
import requests
from bs4 import BeautifulSoup
import pandas as pd

from decimal import Decimal
from datetime import datetime

BOM_URL = "http://www.boxofficemojo.com"


def fix_movie_url(url):
    fix = url.replace('\xa0', '%A0')
    return fix


def dollar_str_to_num(x):
    """Turns a dollar amount string input into a decimal.
    Eg "$123" -> 123
    """
    
    try:
        num = float(re.sub(r'[^\d.]', '', x))
    except:
        num = 0
    return num


def str_to_date(str):
    """Turns date string in the format of YYYY/MM/DD into a datetime object
    """
    return datetime.strptime(str, '%Y/%m/%d')


def comma_num_str_to_int(n):
    """Turns a number string with commmas into an integer
    Eg. "123,456,789" -> 123456789
    """
    try:
        num = int(n.replace(',', ''))
    except:
        num = 0
    return num


def get_soup(url):
    """Returns a BeautifulSoup object from input url
    """
    return BeautifulSoup(requests.get(url).text, 'lxml')


def search_for_movie(query):
    """Seachs BoxOfficeMojo for input movie query. Returns a list of results that
    contain movie title and URL
    """
    search_url = "http://www.boxofficemojo.com/search/?q=" + query
    soup = get_soup(fix_movie_url(search_url))
    
    search_matches = soup.find(text=re.compile("Movie Matches"))
    search_results = search_matches.find_next().findAll('tr')[1:] # Skip header row
    
    movies = []
    
    if len(search_results) > 1:
        for result in search_results:
            title_raw = result.findAll('a', attrs={'href':re.compile('\/movies')})

            if len(title_raw) == 2:
                title = title_raw[1]
            else:
                title = title_raw[0]
                
            if title.getText() != 'Showtimes':
                movies.append({'title': title.getText(),
                               'url': title.attrs['href']})
    else:
        movie_result = search_results[0]
        movie_title = movie_result.findChildren()[6]
        
        movies.append({'title': movie_title.getText(),
                       'url': movie_title.attrs['href']})
    
    return movies


def get_oscar_noms(movie_url):
    """Returns all the oscar nominations for input Movie url.
    """
    movie_soup = get_soup(fix_movie_url(BOM_URL + '/oscar' + movie_url))
    
    movie_title = movie_soup.find('a', attrs={'href': movie_url}).getText()
    
    # Get all nominations, if any. 
    movie_noms = []
    oscar_noms_soup = movie_soup.findAll('a',
                                         attrs={'href': re.compile('oscar\/chart')})[:-1]
    
    for nom in oscar_noms_soup:
        nom_regex = re.compile('(.+[a-z])\s*(?:\((WIN)\))?')
        regex_result = nom_regex.search(nom.text).groups()
        movie_noms.append({'Movie': movie_title,
                           'Nomination': regex_result[0],
                           'Win': 1 if regex_result[1] else 0})
    
    return movie_noms

def get_noms_for_movies(movies):
    all_noms = []

    for movie in movies:
        print('Getting nominations for: ', movie['Movie'])
        all_noms += get_oscar_noms(movie['url'])

    return all_noms

def get_noms_for_movies_old(movies):
    """Returns a list of the input movies and all the oscars they have been
    nominated for
    """
    all_noms = []
    
    for movie in movies:
        print('processing: "', movie, '"')
        search_results = search_for_movie(movie)
        
        if movie in [result['title'] for result in search_results]:
            match = [x for x in search_results if x['title'] == movie][0]
            
        elif len(search_results) > 1: 
            for i, result in enumerate(search_results):
                print(i, result['title'])
                
            user_input = None
            while user_input is None:
                n = int(input('Enter a number: '))
                if n >= 0 and n < len(search_results):
                    user_input = n
            
            match = search_results[user_input]
        
        else:
            match = search_results[0]
        
        all_noms += get_oscar_noms(match['url'])
    
    return all_noms

def create_dummies(df, categories):
    empty_df_w_dummies = pd.DataFrame(columns=categories,
                                      dtype=int)
    
    dummies = pd.get_dummies(df['Nomination'])
    dummies = pd.concat([df['Movie'], dummies], axis=1)
    dummies = dummies.groupby('Movie').sum()
    
    dataset = pd.concat([empty_df_w_dummies, dummies]).fillna(0)
    
    return dataset

def get_nom_count(df):
    nom_counts = df.groupby('Movie').count()['Nomination']
    nom_counts.name = 'Nomination count'
    
    return nom_counts


def get_best_movie_wins(df):
    best_movies = df[df['Nomination'] == 'Picture']
    
    best_movies.index = best_movies['Movie']
    best_movies = best_movies['Win']
    
    return best_movies


def parse_best_pic_row(row, year):
    # Magic variables for parsing HTML table columns
    MOVIE = 1
    STUDIO = 2
    PRENOM_GROSS = 3
    PRENOM_THEATRES = 4
    POSTNOM_GROSS = 5
    POSTNOM_THEATRES = 6
    POSTAWARD_GROSS = 7
    POSTAWARD_THEATRES = 8
    TOTAL_GROSS = 9 
    RELEASE_DATE = 10
    NUM_OF_COLS = 11

    url_regex = re.compile('\/oscar(.+)')
    
    info = row.findAll('td')
    
    if len(info) == NUM_OF_COLS:
        movie_title = info[MOVIE].getText()
        movie_url = info[MOVIE].find('a', attrs={'href':re.compile('\/oscar')})
        movie_url = url_regex.search(movie_url.attrs['href']).groups()[0]
        prenom_gross = info[PRENOM_GROSS].getText()
        prenom_theatres = info[PRENOM_THEATRES].getText()
        postnom_gross = info[POSTNOM_GROSS].getText()
        postnom_theatres = info[POSTNOM_THEATRES].getText()
        release_date = "{:}/{:}".format(year,
                                        info[RELEASE_DATE].getText())
            
        movie = {
            'Movie': movie_title,
            'Pre-Nom Gross': prenom_gross,
            'Pre-Nom Theatres': prenom_theatres,
            'Post-Nom Gross': postnom_gross,
            'Post-Nom Theatres': postnom_theatres,
            'Release': release_date,
            'Year': year,
            'url': movie_url
            }
        
        return movie

def parse_best_pic_page_for_year(year):
    soup = get_soup("http://www.boxofficemojo.com/oscar/chart/?yr={yr}".format(yr=year))
    header = soup.find(text='BEST PICTURE')
    
    if header:
        table = header.findNext('table')
        
        table_rows = table.findAll('tr')
        
        movies_data = []
        for row in table_rows[1:]:
            movie = parse_best_pic_row(row, year)
            if movie is not None:
                movies_data.append(movie)
        
        return movies_data
   
    
def get_best_picture_noms(start_yr, end_yr):
    """Returns list of all movies that were nominated for best picture for the input
    years
    """
    all_best_picture_movies = []
    
    for year in range(start_yr, end_yr + 1):
        print("Processing year:", year)
        best_picture_for_year = parse_best_pic_page_for_year(year)
        if best_picture_for_year:
            all_best_picture_movies += best_picture_for_year
        else:
            print(" - None found for year:", year)
    
    return all_best_picture_movies


def transform_bestpic_data_to_df(movies_data):
    movies_df = pd.DataFrame(movies_data)
    
    movies_df['Pre-Nom Gross'] = movies_df['Pre-Nom Gross'].apply(dollar_str_to_num)
    movies_df['Pre-Nom Theatres'] = movies_df['Pre-Nom Theatres'].apply(comma_num_str_to_int)
    movies_df['Post-Nom Gross'] = movies_df['Post-Nom Gross'].apply(dollar_str_to_num)
    movies_df['Post-Nom Theatres'] = movies_df['Post-Nom Theatres'].apply(comma_num_str_to_int)
    movies_df['Release'] = movies_df['Release'].apply(str_to_date)

    movies_df.index = movies_df['Movie']
    del movies_df['Movie']
    
    return movies_df
    
categories = ['Actor', 'Actress', 'Adapted Screenplay', 'Art Direction',
              'Cinematography', 'Costume Design', 'Director', 'Editing',
              'Makeup', 'Original Score', 'Original Screenplay',
              'Original Song', 'Picture', 'Sound', 'Sound Editing',
              'Supporting Actor', 'Supporting Actress', 'Visual Effects']


def main():
    ### Collect data
    best_pic_movies = get_best_picture_noms(1950, 2017)
    best_pic_other_noms = get_noms_for_movies(best_pic_movies)

    # get movie gross
    best_pic_df = transform_bestpic_data_to_df(best_pic_movies)

    # oscar nominations
    all_noms_df = pd.DataFrame(best_pic_other_noms)

    noms_df = create_dummies(all_noms_df, categories)
    nom_cnt_df = get_nom_count(all_noms_df)
    wins_df = get_best_movie_wins(all_noms_df)

    # Merge to final DF
    merged = best_pic_df\
         .join(noms_df)\
         .join(nom_cnt_df)\
         .join(wins_df)

    merged.to_csv('bom_oscars.csv')

if __name__ == "__main__":
    main()
