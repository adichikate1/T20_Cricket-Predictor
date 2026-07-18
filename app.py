from flask import request, render_template, Flask
from catboost import CatBoostClassifier
import requests
from bs4 import BeautifulSoup
import pandas as pd
from github import Github
import base64

app = Flask(__name__)

model = CatBoostClassifier()

def find_team_name(script,flag=0):
    corrector_index = script.find("team1:") + 6
    corrector_last_index = script[corrector_index:].find(",")
    corrector_name = script[corrector_index : corrector_index + corrector_last_index]


    script_index = script.find("https:api.goscorer.comapiv3getSV3")
    modi_script = script[script_index:]
    start_index = modi_script.find("team1:")
    last_index = modi_script.find("team2short:") + 15
    names_line = modi_script[start_index:last_index]


    team1_index = names_line.find("team1_f_n:") + 10
    team1_last_index = names_line[team1_index:].find(",")
    team1_name = names_line[team1_index: team1_index + team1_last_index]


    team1_short_name_index = names_line.find("team1:") + 6
    team1_short_name_last_index = names_line[team1_short_name_index:].find(",")
    team1_short_name = names_line[team1_short_name_index:team1_short_name_index + team1_short_name_last_index]


    team2_index = names_line.find("team2_f_n") + 10
    team2_last_index = names_line[team2_index:].find(",")
    team2_name = names_line[team2_index:team2_index + team2_last_index]


    team2_short_name_index = names_line.find("team2:") + 6
    team2_short_name_last_index = names_line[team2_short_name_index:].find(",")
    team2_short_name = names_line[team2_short_name_index:team2_short_name_index + team2_short_name_last_index]


    if flag == 0:
        team1_points = 0
        team2_points = 0
        for ch in corrector_name:
            team1_count = team1_name.count(ch)
            team1_points += team1_count
            team2_count = team2_name.count(ch)
            team2_points += team2_count


        if team1_points < team2_points:
            temp = team1_short_name
            team1_short_name = team2_short_name
            team2_short_name = temp

            temp = team1_name
            team1_name = team2_name
            team2_name = temp


    return [team1_name,team1_short_name,team2_name,team2_short_name]



# team_names = team_name(script)



def find_win_rate(script):
    index = script.find("tcd:") + 7
    last_index = script[index:].find("]}") + 1
    modi_script = script[index:last_index + index]


    start = 0
    win_rate = []
    avg_runs = []
    while True:
        tm_index = modi_script.find("tm:",start)
        modi_tm = modi_script[tm_index + 3:]
        tm_last_index = modi_tm.find(",")
        total_match = modi_tm[:tm_last_index]
        w_index = modi_tm.find("w:")
        modi_win = modi_tm[w_index + 2:]
        w_last_index = modi_win.find(",")
        wins = modi_win[:w_last_index]
        avg_index = modi_win.find("avg:")
        modi_avg = modi_win[avg_index + 4:]
        avg_last_index = modi_avg.find(",")
        avg = modi_avg[:avg_last_index]
        if tm_index == -1:
            break
        if avg == "null":
            avg_run = float(sum(avg_runs)/len(avg_runs))
        else:
            avg_run = float(avg)
        avg_runs.append(avg_run)
        try:
            win_rate.append(float(wins)/float(total_match) * 100)
        except ZeroDivisionError:
            win_rate.append(0)
        start = tm_index + 1


    return win_rate, avg_runs



# win_rate, avg_runs = find_win_rate()



def h2h_win_rate(script, team_names):
    index = script.find("https:stats.crickapi.comlivegetPreLiveStats:") + 48
    last_index = script[index:].find("]") + 1
    modi_script = script[index:index + last_index]


    start = 0
    winners = []
    while True:
        result_index = modi_script.find("result:", start)
        if result_index == -1:
            break
        m_script = modi_script[result_index + 7:]
        coma_index = m_script.find("}")
        result_line = m_script[:coma_index]
        won_index = result_line.find(" Won by")
        if won_index == -1:
            won_index = result_line.find(" Won (DLS Method)")
        winner = result_line[:won_index].replace("-", "")
        winners.append(winner)
        start = result_index + 1
        

    if len(winners) == 0:
        return 0
    else:
        return winners.count(team_names[1].replace("-",""))/len(winners) * 100



# h2h_wr = h2h_win_rate()



def recent_form(script):
    index = script.find("tf:") + 3
    modi_script = script[index:]
    last_index = modi_script.find(",")
    rf_line = modi_script[:last_index + 1]


    i = 0
    team_rf = 0
    teams_rf = []
    while i < len(rf_line):
        if rf_line[i] == "W":
            team_rf += int(rf_line[i + 1])
        elif rf_line[i] in ["-", ","]:
            teams_rf.append(team_rf)
            team_rf = 0
        i += 1


    return teams_rf



# team_rf = recent_form()



def link(word, script, flag=0):
    index = script.find(word) + 4
    if word == "t1f":
        last_index = script.find("t2f:")
    else:
        last_index = script.find("tb:")
    all_matches_codes = script[index:last_index].replace(",", "|")


    match_hash_codes = []
    start = 0
    while True:
        match_last_index = all_matches_codes.find("|", start)
        if match_last_index == -1:
            break
        code_index = match_last_index
        while all_matches_codes[code_index] != "-":
            code_index -= 1
        match_hash_codes.append(all_matches_codes[code_index + 1:match_last_index])
        start = match_last_index + 1


    new_match_hash_codes = []
    for mc in match_hash_codes:
        if "Semi Final " in mc:
            new_match_hash_codes.append(mc.replace("Semi Final ", ""))
        else:
            new_match_hash_codes.append(mc)


    match_nos = []
    match_codes = []
    for i in range(5):
        try :
            match_hash_code = new_match_hash_codes[i]

            if match_hash_code[1] == "2" and match_hash_code[2] == "2":
                match_no = match_hash_code[:2]
            elif match_hash_code[2] == "2":
                match_no = match_hash_code[:2]
            else:
                match_no = match_hash_code[:1]


            len_match_no = len(match_no)
            match_code = new_match_hash_codes[i][len_match_no + 1: len_match_no + 1 + 4]
            if str(match_code[0]).isalpha():
                match_code = match_code[:-1]
            if "^" in match_no:
                match_no = match_no[1]
            match_nos.append(match_no)
            match_codes.append(match_code)

        except IndexError:
            break


    if flag != 0:
        new_match_codes = []
        for code in match_codes:
            if len(code) == 4:
                new_match_codes.append(code[:-1])
            else:
                new_match_codes.append(code)
        match_codes = new_match_codes

    print(match_codes)
    links = []
    for n,c in zip(match_nos,match_codes):
        links.append(f"https://crex.com/cricket-live-score/lakr-vs-so-{n}th-match-major-league-cricket-2026-match-updates-{c}/match-details")
    return links, match_codes



def wicket_lost(team_names, script, df):
    links1, match_hashcodes1 = link("t1f:", script)
    links2, match_hashcodes2  = link("t2f:", script)


    if len(match_hashcodes1) > len(match_hashcodes2):
        links1 = []
        links2 = []
        for match_hashcode in match_hashcodes2:
            if match_hashcode in match_hashcodes1:
                match_hashcodes1.remove(match_hashcode)
                for code in match_hashcodes1:
                    links1.append(f"https://crex.com/cricket-live-score/lakr-vs-so-9th-match-major-league-cricket-2026-match-updates-{code}/match-details")
                for code in match_hashcodes2:
                    links2.append(f"https://crex.com/cricket-live-score/lakr-vs-so-9th-match-major-league-cricket-2026-match-updates-{code}/match-details")
    elif len(match_hashcodes1) < len(match_hashcodes2):
        links2 = []
        links1 = []
        for match_hashcode in match_hashcodes1:
            if match_hashcode in match_hashcodes2:
                match_hashcodes2.remove(match_hashcode)
                for code in match_hashcodes2:
                    links2.append(f"https://crex.com/cricket-live-score/lakr-vs-so-9th-match-major-league-cricket-2026-match-updates-{code}/match-details")
                for code in match_hashcodes1:
                    links1.append(f"https://crex.com/cricket-live-score/lakr-vs-so-9th-match-major-league-cricket-2026-match-updates-{code}/match-details")


    try :
        team1_wickets = []
        team1_runs = []
        for lk1 in links1:
            r1 = requests.get(lk1)
            soup1 = BeautifulSoup(r1.text, 'html.parser')
            new_script1 = str(soup1.find("script",{"id": "app-root-state"})).replace("&q;", "").replace("&a;", "").replace("/", "")

            # with open("data1.json", "w", encoding="utf-8") as f:
            #     f.write(str(new_script1))


            team1main = team_names[1]
            team1short = find_team_name(new_script1, 1)[1]
            if team1short == team1main:
                index_1 = new_script1.find("score1:") + 7
                modi_script1 = new_script1[index_1:]
                coma_index_1 = modi_script1.find(",")
                score1 = modi_script1[:coma_index_1]
                score1_index = score1.find("-") + 1
                run = float(score1[:score1_index - 1])
                wicket = float(score1[score1_index:])
                team1_runs.append(run)
                team1_wickets.append(wicket)
            else:
                index_1 = new_script1.find("score2:") + 7
                modi_script1 = new_script1[index_1:]
                coma_index_1 = modi_script1.find(",")
                score1 = modi_script1[:coma_index_1]
                score1_index = score1.find("-") + 1
                run = float(score1[:score1_index - 1])
                wicket = float(score1[score1_index:])
                team1_runs.append(run)
                team1_wickets.append(wicket)


        team2_wickets = []
        team2_runs = []
        for lk2 in links2:
            r2 = requests.get(lk2)
            soup2 = BeautifulSoup(r2.text, 'html.parser')
            new_script2 = str(soup2.find("script",{"id": "app-root-state"})).replace("&q;", "").replace("&a;", "").replace("/", "")


            team2main = team_names[3]
            team2short = find_team_name(new_script2, 1)[1]
            if team2short == team2main:
                index_2 = new_script2.find("score1:") + 7
                modi_script2 = new_script2[index_2:]
                coma_index_2 = modi_script2.find(",")
                score2 = modi_script2[:coma_index_2]
                score2_index = score2.find("-") + 1
                run = float(score2[:score2_index - 1])
                wicket = float(score2[score2_index:])
                team2_runs.append(run)
                team2_wickets.append(wicket)
            else:
                index_2 = new_script2.find("score2:") + 7
                modi_script2 = new_script2[index_2:]
                coma_index_2 = modi_script2.find(",")
                score2 = modi_script2[:coma_index_2]
                score2_index = score2.find("-") + 1
                run = float(score2[:score2_index - 1])
                wicket = float(score2[score2_index:])
                team2_runs.append(run)
                team2_wickets.append(wicket)

    except ValueError:

        links1, match_hashcodes1 = link("t1f:",script, 1)
        links2, match_hashcodes2  = link("t2f:",script, 1)

        if len(match_hashcodes1) > len(match_hashcodes2):
            links1 = []
            links2 = []
            for match_hashcode in match_hashcodes2:
                if match_hashcode in match_hashcodes1:
                    match_hashcodes1.remove(match_hashcode)
                    for code in match_hashcodes1:
                        links1.append(f"https://crex.com/cricket-live-score/lakr-vs-so-9th-match-major-league-cricket-2026-match-updates-{code}/match-details")
                    for code in match_hashcodes2:
                        links2.append(f"https://crex.com/cricket-live-score/lakr-vs-so-9th-match-major-league-cricket-2026-match-updates-{code}/match-details")

        elif len(match_hashcodes1) < len(match_hashcodes2):
            links2 = []
            links1 = []
            for match_hashcode in match_hashcodes1:
                if match_hashcode in match_hashcodes2:
                    match_hashcodes2.remove(match_hashcode)
                    for code in match_hashcodes2:
                        links2.append(f"https://crex.com/cricket-live-score/lakr-vs-so-9th-match-major-league-cricket-2026-match-updates-{code}/match-details")
                    for code in match_hashcodes1:
                        links1.append(f"https://crex.com/cricket-live-score/lakr-vs-so-9th-match-major-league-cricket-2026-match-updates-{code}/match-details")

        team1_wickets = []
        team1_runs = []
        for lk1 in links1:
            r1 = requests.get(lk1)
            soup1 = BeautifulSoup(r1.text, 'html.parser')
            new_script1 = str(soup1.find("script",{"id": "app-root-state"})).replace("&q;", "").replace("&a;", "").replace("/", "")

            # with open("data1.json", "w", encoding="utf-8") as f:
            #     f.write(str(new_script1))


            team1main = team_names[1]
            team1short = find_team_name(new_script1, 1)[1]
            if team1short == team1main:
                index_1 = new_script1.find("score1:") + 7
                modi_script1 = new_script1[index_1:]
                coma_index_1 = modi_script1.find(",")
                score1 = modi_script1[:coma_index_1]
                score1_index = score1.find("-") + 1
                run = float(score1[:score1_index - 1])
                wicket = float(score1[score1_index:])
                team1_runs.append(run)
                team1_wickets.append(wicket)
            else:
                index_1 = new_script1.find("score2:") + 7
                modi_script1 = new_script1[index_1:]
                coma_index_1 = modi_script1.find(",")
                score1 = modi_script1[:coma_index_1]
                score1_index = score1.find("-") + 1
                run = float(score1[:score1_index - 1])
                wicket = float(score1[score1_index:])
                team1_runs.append(run)
                team1_wickets.append(wicket)


        team2_wickets = []
        team2_runs = []
        for lk2 in links2:
            r2 = requests.get(lk2)
            soup2 = BeautifulSoup(r2.text, 'html.parser')
            new_script2 = str(soup2.find("script",{"id": "app-root-state"})).replace("&q;", "").replace("&a;", "").replace("/", "")


            team2main = team_names[3]
            team2short = find_team_name(new_script2, 1)[1]
            if team2short == team2main:
                index_2 = new_script2.find("score1:") + 7
                modi_script2 = new_script2[index_2:]
                coma_index_2 = modi_script2.find(",")
                score2 = modi_script2[:coma_index_2]
                score2_index = score2.find("-") + 1
                run = float(score2[:score2_index - 1])
                wicket = float(score2[score2_index:])
                team2_runs.append(run)
                team2_wickets.append(wicket)
            else:
                index_2 = new_script2.find("score2:") + 7
                modi_script2 = new_script2[index_2:]
                coma_index_2 = modi_script2.find(",")
                score2 = modi_script2[:coma_index_2]
                score2_index = score2.find("-") + 1
                run = float(score2[:score2_index - 1])
                wicket = float(score2[score2_index:])
                team2_runs.append(run)
                team2_wickets.append(wicket)


    try :
        t1_avg_wl = sum(team1_wickets)/len(match_hashcodes1)
    except ZeroDivisionError: 
        t1_avg_wl = df["team1_avg_wicket_last_5"].mean()

    try :
        t2_avg_wl = sum(team2_wickets)/len(match_hashcodes2)
    except ZeroDivisionError: 
        t2_avg_wl = df["team2_avg_wicket_last_5"].mean()

    try :
        t1_avg_runs = sum(team1_runs)/len(match_hashcodes1)
    except ZeroDivisionError: 
        t1_avg_runs = df["team1_avg_runs_last_5"].mean()

    try :
        t2_avg_runs = sum(team2_runs)/len(match_hashcodes2)
    except ZeroDivisionError: 
        t2_avg_runs = df["team2_avg_runs_last_5"].mean()

    return t1_avg_wl, t2_avg_wl, t1_avg_runs, t2_avg_runs


# team1_avg_wickets, team2_avg_wickets = wicket_lost()



def first_inn_scr(r):
    text = str(r.text)
    index = text.find('class="venue-avg-val"') + 22
    modi_text = text[index:]
    last_index = modi_text.find("<")
    return float(modi_text[:last_index])



def chase_win_rate(script, df):
    index = script.find("tm:")
    modi_script = script[index:]
    last_index = modi_script.find("}")


    modi_script = modi_script[:last_index]
    tm_index = modi_script.find(":")
    modi_script = modi_script[tm_index + 1:]
    tm_last_index = modi_script.find(",")
    tm = float(modi_script[:tm_last_index])


    y_index = modi_script.find("y:")
    y = float(modi_script[y_index + 2:])

    try:
        rate = y/tm * 100
    except ZeroDivisionError:
        rate = df["chasing_success_rate"].mean()
    
    return rate



def toss(script, soup):
    string_soup = str(soup)
    index = string_soup.find("won the toss and chose to")
    new_text = string_soup[index - 10:index - 10 + 80]


    toss_index = new_text.find(">")
    toss_last_index = new_text.find("<")
    toss_line = new_text[toss_index + 1: toss_last_index]


    space_index = toss_line.find(" ")
    toss_winner = toss_line[:space_index]
    to_index = toss_line.find(" chose")
    toss_decision = toss_line[to_index + 10:].capitalize()


    team1_points = 0
    team2_points = 0
    names = find_team_name(script)
    team1 = names[0].lower()
    team2 = names[2].lower()
    for ch in toss_winner.lower():
        team1_count = team1.count(ch)
        team1_points += team1_count
        team2_count = team2.count(ch)
        team2_points += team2_count


    if team1_points < team2_points:
        if "-" in team2:
            return team2.upper(), toss_decision
        else:
            return team2.title(), toss_decision
    else:
        if "-" in team1:
            return team1.upper(), toss_decision
        else:
            return team1.title(), toss_decision



# toss_win, toss_decision = toss()



def temperature(script):
    index = script.find("crT:")
    text = script[index + 4:]
    last_index = text.find("˚")
    return float(text[:last_index])



def humidity(script):
    index = script.find("hum:")
    return float(script[index + 4:index + 6])



def rain_prob(script):
    index = script.find("rP:")
    return float(script[index + 3:index + 5])



def venue(script):
    index = script.find("v:")
    modi_script = script[index + 2:]
    coma_index = modi_script.find(",")
    venue_name = modi_script[:coma_index]

    if "Cricket" in venue_name:
        venue_name = venue_name.replace("Cricket", "").replace("  ", " ")
    elif "Hambantota" in venue_name:
        venue_name = venue_name.replace(" Hambantota","")

    return venue_name


def pitch_type(script):
    index = script.find("prt:") + 5
    last_index = script.find(",pitch_report:")
    pitch_full_line = script[index:last_index]


    batting_score_index = pitch_full_line.find("batting_pitch_score:")
    modi_batting_score = pitch_full_line[batting_score_index + 20:]
    batting_score_last_index = modi_batting_score.find(",")


    try:
        batting_score = float(modi_batting_score[:batting_score_last_index])


        swing_score_index = pitch_full_line.find("swing_pitch_score:")
        modi_swing_score = pitch_full_line[swing_score_index + 18:]
        swing_score_last_index = modi_swing_score.find(",")
        swing_score = float(modi_swing_score[:swing_score_last_index])
        

        pitch_score_index = pitch_full_line.find("pace_pitch_score:")
        modi_pitch_score = pitch_full_line[pitch_score_index + 17:]
        pitch_score_last_index = modi_pitch_score.find(",")
        pitch_score = float(modi_pitch_score[:pitch_score_last_index])


        seam_score_index = pitch_full_line.find("seam_pitch_score:")
        modi_seam_score = pitch_full_line[seam_score_index + 17:]
        seam_score_last_index = modi_seam_score.find(",")
        seam_score = float(modi_seam_score[:seam_score_last_index])


        bounce_score_index = pitch_full_line.find("bounce_pitch_score:")
        modi_bounce_score = pitch_full_line[bounce_score_index + 19:]
        bounce_score_last_index = modi_bounce_score.find(",")
        bounce_score = float(modi_bounce_score[:bounce_score_last_index])


        spin_score = float(pitch_full_line[-1])
        

        bowling_avg = (swing_score + pitch_score + seam_score + bounce_score + spin_score)/5


        if batting_score == bowling_avg:
            return "Balanced"
        elif batting_score < bowling_avg:
            return "Bowling"
        else:
            return "Batting"


    except ValueError:
        return "Balanced"



def win(script, team_names):
    index = script.find("B:")
    modi_script = script[index + 2:]
    last_index = modi_script.find(" won ")
    winner = modi_script[:last_index]


    team1 = team_names[0].upper()
    team2 = team_names[2].upper()


    team1points = 0
    team2points = 0
    for ch in winner.upper():
        team1points += team1.count(ch)
        team2points += team2.count(ch)


    if team1points > team2points:
        winner = team1
    else:
        winner = team2
        

    if winner == team1:
        return 0
    else:
        return 1 



# df = pd.DataFrame(columns=[
#     "team1",
#     "team2",
#     "team1_win_rate",
#     "team2_win_rate",
#     "head_to_head_win_rate",
#     "team1_recent_form",
#     "team2_recent_form",
#     "team1_venue_win_rate",
#     "team2_venue_win_rate",
#     "team1_avg_runs_last_5",
#     "team2_avg_runs_last_5",
#     "team1_avg_wicket_last_5",
#     "team2_avg_wicket_last_5",
#     "avg_first_innings_score",
#     "chasing_success_rate",
#     "toss_winner",
#     "toss_decision",
#     "temperature",
#     "humidity",
#     "rain_probability",
#     "venue",
#     "pitch_type",
#     "win"
# ])



@app.route("/", methods=['GET','POST'])
def cricket_predictor():
    team_names = None
    venue_name = None
    prediction = None
    confidence = None

    if request.method == "POST":
        league = request.form["league"]
        code = request.form["match_code"]
        extra = request.form["extraOptions"]

        if extra != "":
            df = pd.read_csv(f"static/data/{extra}.csv").dropna()
        else:
            df = pd.read_csv(f"static/data/{league}.csv").dropna()


        url = f"https://crex.com/cricket-live-score/miny-vs-tsk-7th-match-major-league-cricket-2026-match-updates-{code}/match-details"

        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        script = str(soup.find("script",{"id": "app-root-state"})).replace("&q;", "").replace("&a;", "").replace("/", "")


        toss_win, toss_decision = toss(script, soup)


        team_names = find_team_name(script)


        try:
            team1_avg_wickets, team2_avg_wickets, team1_avg_runs, team2_avg_runs = wicket_lost(team_names, script, df)
        except IndexError:
            team1_avg_wickets = df["team1_avg_wicket_last_5"].mean()
            team2_avg_wickets = df["team2_avg_wicket_last_5"].mean()

        try:
            avg_1st_inn_score = first_inn_scr(r)
        except ValueError:
            avg_1st_inn_score = df["avg_first_innings_score"].mean()



        try:
            chase_rate = chase_win_rate(script, df)
        except ValueError :
            chase_rate = float(df["chasing_success_rate"].mean())


        team_rf = recent_form(script)


        h2h_wr = h2h_win_rate(script, team_names)

        # try:
        win_rate, avg_runs = find_win_rate(script)
        # except ZeroDivisionError:
        #     win_rate = [df["team1_win_rate"].mean(), df["team2_win_rate"].mean(), df["team1_venue_win_rate"].mean(), df["team2_venue_win_rate"].mean()]


        venue_name = venue(script)

        if league in ["Lanka Premier League", "Major league"]:
            try:
                match_data = {
                    "team1": team_names[0],
                    "team2": team_names[2],
                    "team1_win_rate": win_rate[0],
                    "team2_win_rate": win_rate[1],
                    "head_to_head_win_rate": h2h_wr,
                    "team1_recent_form": team_rf[0],
                    "team2_recent_form": team_rf[1],
                    "team1_venue_win_rate": win_rate[2],
                    "team2_venue_win_rate": win_rate[3],
                    "team1_avg_runs_last_5": team1_avg_runs,
                    "team2_avg_runs_last_5": team2_avg_runs,
                    "team1_avg_wicket_last_5": team1_avg_wickets,
                    "team2_avg_wicket_last_5": team2_avg_wickets,
                    "avg_first_innings_score": avg_1st_inn_score,
                    "chasing_success_rate": chase_rate,
                    "toss_winner": toss_win,
                    "toss_decision": toss_decision,
                    "temperature": temperature(script),
                    "humidity": humidity(script),
                    "rain_probability": rain_prob(script),
                    "venue": venue_name,
                    "pitch_type": pitch_type(script)
                }
            except IndexError:
                match_data = {
                    "team1": team_names[0],
                    "team2": team_names[2],
                    "team1_win_rate": win_rate[0],
                    "team2_win_rate": win_rate[1],
                    "head_to_head_win_rate": h2h_wr,
                    "team1_recent_form": team_rf[0],
                    "team2_recent_form": team_rf[1],
                    "team1_venue_win_rate": win_rate[2],
                    "team2_venue_win_rate": win_rate[3],
                    "team1_avg_runs_last_5": team1_avg_runs,
                    "team2_avg_runs_last_5": team2_avg_runs,
                    "team1_avg_wicket_last_5": team1_avg_wickets,
                    "team2_avg_wicket_last_5": team2_avg_wickets,
                    "avg_first_innings_score": avg_1st_inn_score,
                    "chasing_success_rate": chase_rate,
                    "toss_winner": toss_win,
                    "toss_decision": toss_decision,
                    "temperature": temperature(script),
                    "humidity": humidity(script),
                    "rain_probability": rain_prob(script),
                    "venue": venue_name,
                    "pitch_type": pitch_type(script)
                }

            input_data = pd.DataFrame([match_data])

            num_cols = input_data.select_dtypes(include="number").columns
            for col in num_cols:
                input_data[col] = input_data[col].fillna(df[col].mean())





        TOKEN = "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"
        USERNAME = "adichikate1"
        REPO_NAME = "T20_Cricket-Predictor"
        g = Github(TOKEN)
        repo = g.get_repo(f"{USERNAME}/{REPO_NAME}")

        if league == "add":
            try:
                match_data = {
                    "team1": team_names[0],
                    "team2": team_names[2],
                    "team1_win_rate": win_rate[0],
                    "team2_win_rate": win_rate[1],
                    "head_to_head_win_rate": h2h_wr,
                    "team1_recent_form": team_rf[0],
                    "team2_recent_form": team_rf[1],
                    "team1_venue_win_rate": win_rate[2],
                    "team2_venue_win_rate": win_rate[3],
                    "team1_avg_runs_last_5": team1_avg_runs,
                    "team2_avg_runs_last_5": team2_avg_runs,
                    "team1_avg_wicket_last_5": team1_avg_wickets,
                    "team2_avg_wicket_last_5": team2_avg_wickets,
                    "avg_first_innings_score": avg_1st_inn_score,
                    "chasing_success_rate": chase_rate,
                    "toss_winner": toss_win,
                    "toss_decision": toss_decision,
                    "temperature": temperature(script),
                    "humidity": humidity(script),
                    "rain_probability": rain_prob(script),
                    "venue": venue_name,
                    "pitch_type": pitch_type(script),
                    "win": win(script, team_names)
                }
            except IndexError:
                match_data = {
                    "team1": team_names[0],
                    "team2": team_names[2],
                    "team1_win_rate": win_rate[0],
                    "team2_win_rate": win_rate[1],
                    "head_to_head_win_rate": h2h_wr,
                    "team1_recent_form": team_rf[0],
                    "team2_recent_form": team_rf[1],
                    "team1_venue_win_rate": win_rate[2],
                    "team2_venue_win_rate": win_rate[3],
                    "team1_avg_runs_last_5": team1_avg_runs,
                    "team2_avg_runs_last_5": team2_avg_runs,
                    "team1_avg_wicket_last_5": team1_avg_wickets,
                    "team2_avg_wicket_last_5": team2_avg_wickets,
                    "avg_first_innings_score": avg_1st_inn_score,
                    "chasing_success_rate": chase_rate,
                    "toss_winner": toss_win,
                    "toss_decision": toss_decision,
                    "temperature": temperature(script),
                    "humidity": humidity(script),
                    "rain_probability": rain_prob(script),
                    "venue": venue_name,
                    "pitch_type": pitch_type(script),
                    "win": win(script, team_names)
                }


            add_df = pd.DataFrame([match_data])

            num_cols = add_df.select_dtypes(include="number").columns
            for col in num_cols:
                add_df[col] = add_df[col].fillna(df[col].mean())

            add_data = pd.concat([df, add_df], ignore_index=True)
            print(extra)

            github_file = f"static/data/{extra}.csv"
            file_path = f"static/data/{extra}.csv"
            print(github_file)
            print(file_path)
            add_data.to_csv(file_path, index=False)


            with open(file_path, "rb") as f:
                content = f.read()

            try:
                file = repo.get_contents(github_file)

                repo.update_file(
                    path=github_file,
                    message="Added new match",
                    content=content,
                    sha=file.sha
                )

                print("GitHub Updated")

            except:
                repo.create_file(
                    path=github_file,
                    message="Created CSV",
                    content=content
                )

                print("GitHub Created")








        if league != "add":
            if league == "Major league":
                model.load_model("static/models/Major_League.cbm")
                prediction = model.predict(input_data)
                confidence = round(prediction[0][0] * 100, 2)
            elif league == "Lanka Premier League":
                model.load_model("static/models/Lanka_Premier_League.cbm")
                prediction = model.predict(input_data)
                confidence = round(prediction[0][0] * 100, 2)


            if prediction[0][0] > 0.5:
                prediction = team_names[2]
            else:
                prediction = team_names[0]
                confidence = 100 - confidence

    return render_template(
        "index.html",
        team_a=team_names[0] if team_names else None,
        team_b=team_names[2] if team_names else None,
        venue=venue_name,
        winner=prediction,
        confidence=confidence
    )

if __name__ == "__main__":
    app.run(debug=True)
