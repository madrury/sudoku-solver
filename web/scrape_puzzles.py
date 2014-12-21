import requests
import re
import json
import sys

regexps = {
    'mask': re.compile(r'INPUT.+editmask.+VALUE="([0-1]+)"'),
    'puzzle': re.compile(r'INPUT.+cheat.+VALUE="([0-9]+)"'),
    'level': re.compile(r'INPUT.+level.+VALUE="([1-4])"'),
    'id': re.compile(r'INPUT.+pid.+VALUE="([0-9]+)"')
}

def scrape_puzzle(html):
    return {
            key: re.search(regexps[key], html).groups()[0] 
        for key in regexps.iterkeys()
    }

def scrape_puzzles(base_url, level, n):
    url = base_url
    params = {'level': level}
    headers = {
        'User-agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:34.0) '
                       'Gecko/20100101 Firefox/34.0}')
    }
    data = []
    for _ in xrange(n):
        html = requests.get(url, params=params, headers=headers).content
        puzzle = scrape_puzzle(html)
        data.append(puzzle)
    return data

def write_puzzles(fnm, puzzles):
    with open(fnm, 'wb') as fconn:
        json.dump(puzzles, fconn)


if __name__ == '__main__':
    n, level = sys.argv[1], sys.argv[2]
    puzzs = scrape_puzzles('http://view.websudoku.com', level, n)
    write_puzzles('puzzles.json', puzzs)
