from bs4 import BeautifulSoup

import datetime
import json
import os
import time
import threading
import urllib3

cricbuzz_base_url = 'https://www.cricbuzz.com/'
cricbuzz_home_page_url = 'https://www.cricbuzz.com/cricket-match/live-scores'
http = urllib3.PoolManager()


def find_live_matches():
    '''
        This function will search for all the live matches on cricbuzz website and return their cricbuzz url and title as json.
    '''
    r = http.request('GET', cricbuzz_home_page_url)
    soup = BeautifulSoup(r.data, 'html.parser')

    live_matches = []

    for link in soup.find_all('a'):
        url = str(link.get('href'))
        title = link.get('title')
        # Only take live matches.
        # if url.startswith("/live-cricket-scores/") and title is not None and "live" in str(title).lower():
        if url.startswith("/live-cricket-scores/") and title is not None:
            live_matches.append((url[20:], title))

    # Remove duplicate links
    live_matches = list(set(live_matches))

    return json.dumps(live_matches)


def fetch_live_match_updates_per_over(match):
    next_call = time.time()

    current_match = []

    while True:
        r = http.request('GET', cricbuzz_base_url +
                         "live-cricket-scorecard" + match[0])
        soup = BeautifulSoup(r.data, 'html.parser')

        full_score = soup.find('span', class_="pull-right")
        if full_score is None:
            print("Sorry! Unable to fetch score!")

        # Processing and cleaning.
        team = full_score.find_previous_sibling('span')
        team = team.text.strip()

        full_score = full_score.text.strip()
        score, overs = full_score.split('\xa0')
        overs = overs[1:-1]

        flag = 0

        if len(current_match) == 0:
            current_match.append(team)
            current_match.append(score)
            current_match.append(overs)
            flag = flag + 1
        elif current_match[2] != overs or current_match[0] != team:
            current_match = []
            current_match.append(team)
            current_match.append(score)
            current_match.append(overs)
            flag = flag + 1

        # Over is completed
        if flag and "." not in overs:
            print("\nTeam                                  Score               Overs")
            print(team + ' ' * (38 - len(team)) + score +
                  ' ' * (20 - len(score)) + overs + "\n")
            os.system("""
              osascript -e 'display notification "{}" with title "{}"'
              """.format("After " + overs + " overs, " + score, team))

        next_call = next_call + 30

        time.sleep(next_call - time.time())


def helper():
    live_matches = find_live_matches()
    live_matches = json.loads(live_matches)

    print("\nSelect which match you want to follow:\n")
    for idx, match in enumerate(live_matches):
        print(idx+1, match[1])

    selection = int(input())

    if selection < 1 or selection > len(live_matches):
        print("Invalid input.")
        return

    timerThread = threading.Thread(
        target=fetch_live_match_updates_per_over, kwargs=dict(match=live_matches[selection-1]))
    timerThread.start()


if __name__ == "__main__":
    helper()
