import re
import requests
from bs4 import BeautifulSoup
import pandas as pd

BAFTA_URL = "http://awards.bafta.org/"

def get_soup(url):
    """Returns a BeautifulSoup object from input url"""
    return BeautifulSoup(requests.get(url).text, 'lxml')



def get_award_winner(year, award):
    soup = get_soup(BAFTA_URL + "award/{year}/film/{award}".format(year=year,
                                                                   award=award))
    winner = soup.find('div', attrs={'class':'yac-winner-title'})
    
    if winner:
        return winner.getText().strip()
    else:
        return None


def get_all_awards(award):
    start_yr = 1948
    end_yr = 2017
    
    winners = []

    for yr in range(start_yr, end_yr + 1):

        winner = get_award_winner(yr, award)
        
        print('{:} - {:}'.format(yr, winner))
        if winner:
            winners.append({'Year':yr,
                            'Movie': winner})

    return winners

def main():
    x = get_all_awards('film')
    df = pd.DataFrame(x)

    print('Exporting to csv')
    df.to_csv('bafta.csv', index=False)

if __name__ == "__main__":
    main()


