"""
Scrape puzzles from websudoku.com and write the results to json over
standard out.

Usage
-----
    python scrape_puzzles.py <number of puzzles> <difficulty level (1-4)>
"""
import requests
import re
import json
import sys
import random
import time

regexps = {
    'mask': re.compile(rb'INPUT.+editmask.+VALUE="([0-1]+)"'),
    'puzzle': re.compile(rb'INPUT.+cheat.+VALUE="([0-9]+)"'),
    'level': re.compile(rb'INPUT.+level.+VALUE="([1-4])"'),
    'id': re.compile(rb'INPUT.+pid.+VALUE="([0-9]+)"')
}

def scrape_puzzles(base_url, level, n):
    url = base_url
    params = {'level': level}
    headers = {
        'User-agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:34.0) '
                       'Gecko/20100101 Firefox/34.0}')
    }
    data = []
    for _ in range(n):
        html = requests.get(url, params=params, headers=headers).content
        puzzle = scrape_puzzle_data(html)
        data.append(puzzle)
        time.sleep(random.uniform(1, 5)) 
    return data

def scrape_puzzle_data(html):
    return {
        key: re.search(regexps[key], html).groups()[0].decode('utf-8') 
        for key in regexps
    }


if __name__ == '__main__':
    n, level = int(sys.argv[1]), sys.argv[2]
    puzzs = scrape_puzzles('http://view.websudoku.com', level, n)
    json.dump(puzzs, sys.stdout)
