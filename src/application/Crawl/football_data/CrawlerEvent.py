import logging
import requests

from bs4 import BeautifulSoup
import src.util.util as util
import src.application.Domain.Bet_Event as Bet_Event

log = logging.getLogger(__name__)


class CrawlerEvent(object):
    def __init__(self, match_event, event_name, event_link, host_url="http://www.odds.football-data.co.uk"):
        self.match_event = match_event
        self.event_link = host_url + event_link+"all-odds"
        self.event_name = event_name

    def get_page(self):
        """
        requests the web page
        :return:
        """
        self.page = requests.get(self.event_link, timeout=25).text
        self.soup = BeautifulSoup(self.page, "html.parser")
        log.debug("Looking for bet-odds of the match [" + str(self.match_event.id) + "] event [" + self.event_name
                  + "] at the link [" + self.event_link + "]")

    def start_crawl(self):
        """
        Start crawling the event
        :return:
        """
        last_bet_value = self.match_event.get_last_bet_values(self.event_name)
        try:
            if last_bet_value[self.event_name] and util.is_today(last_bet_value[self.event_name].date.split(" ")[0]):
                # do not crawl bet odds, today they've been already crawled
                log.debug("No need to crawl [" + self.event_name + "] " + self.event_link)
                return
        except KeyError:
            pass

        try:
            if self.event_name == 'Match Result':
                self.get_page()
                bet_values = self.get_match_result_odds()

            elif self.event_name == 'Over/Under':
                self.get_page()
                bet_values = self.get_over_under_odds()

            elif self.event_name == 'Half-time/Full-time':
                self.get_page()
                bet_values = self.get_half_time_full_time_odds()

            elif self.event_name == 'Both Teams To Score':
                self.get_page()
                bet_values = self.get_both_teams_to_score_odds()

            elif self.event_name == 'Double Chance':
                self.get_page()
                bet_values = self.get_double_chance_odds()

            elif self.event_name == 'Half-time Double Chance':
                self.get_page()
                bet_values = self.get_half_time_double_chance_odds()

            elif self.event_name == 'Half-time Result':
                self.get_page()
                bet_values = self.get_half_time_result_odds()

            elif self.event_name == 'Half-time Totals Over/Under':
                self.get_page()
                bet_values = self.get_half_time_total_over_under_odds()

            else:
                # event not managed
                log.debug("Event ["+self.event_name+"] not managed")
                return

            if len(bet_values.keys()) > 0:
                # store the event in the DB only if data has been gathered
                Bet_Event.write_new_bet_event(self.match_event.id, self.event_name, bet_values)
        except ValueError:
            return

    def get_half_time_total_over_under_odds(self):
        """
        half_time_total_over_under event manager
        :return:
        """
        bet_values = {}
        bet_365_odds_AO0_trs = self.soup.find_all('tr', {'class': 'AO0'})
        bet_365_odds_AO1_trs = self.soup.find_all('tr', {'class': 'AO1'})

        index_bet_365 = self.get_index_bet_365()

        for bet_365_odds_AO0_tr, bet_365_odds_AO1_tr in zip(bet_365_odds_AO0_trs, bet_365_odds_AO1_trs):
            label_AO0 = str(bet_365_odds_AO0_tr.find('td', {'class': 'Competitor'}).string).strip()
            value_AO0_str = str(bet_365_odds_AO0_tr.contents[index_bet_365].string).strip()

            label_AO1 = str(bet_365_odds_AO1_tr.find('td', {'class': 'Competitor'}).string).strip()
            value_AO1_str = str(bet_365_odds_AO1_tr.contents[index_bet_365].string).strip()

            if value_AO0_str == '-' or value_AO1_str == '-':
                continue

            value_AO0 = get_italian_odds(value_AO0_str)
            value_AO1 = get_italian_odds(value_AO1_str)

            bet_values[label_AO0] = value_AO0
            bet_values[label_AO1] = value_AO1

        return bet_values

    def get_half_time_result_odds(self):
        bet_values = {}

        for i, td in enumerate(self.soup.find_all('td', {'title': 'Bet 365'})):
            bet_value = get_italian_odds(str(td.string).strip())
            if i == 0:
                bet_label = '1'
            elif i == 1:
                bet_label = 'X'
            elif i == 2:
                bet_label = '2'

            bet_values[bet_label] = bet_value

        return bet_values

    def get_half_time_double_chance_odds(self):
        bet_values = {}

        for i, td in enumerate(self.soup.find_all('td', {'title': 'Bet 365'})):
            bet_value = get_italian_odds(str(td.string).strip())
            if i == 0:
                bet_label = '1X'
            elif i == 1:
                bet_label = '12'
            elif i == 2:
                bet_label = 'X2'

            bet_values[bet_label] = bet_value

        return bet_values

    def get_double_chance_odds(self):
        bet_values = {}

        for i, td in enumerate(self.soup.find_all('td', {'title': 'Bet 365'})):
            bet_value = get_italian_odds(str(td.string).strip())
            if i == 0:
                bet_label = '1X'
            elif i == 1:
                bet_label = '12'
            elif i == 2:
                bet_label = 'X2'

            bet_values[bet_label] = bet_value

        return bet_values

    def get_both_teams_to_score_odds(self):
        bet_values = {}

        for i, td in enumerate(self.soup.find_all('td', {'title': 'Bet 365'})):
            bet_value = get_italian_odds(str(td.string).strip())
            if i == 0:
                bet_label = 'G'
            elif i == 1:
                bet_label = 'NG'

            bet_values[bet_label] = bet_value

        return bet_values

    def get_half_time_full_time_odds(self):
        bet_values = {}

        for i, td in enumerate(self.soup.find_all('td', {'title': 'Bet 365'})):
            bet_value = get_italian_odds(str(td.string).strip())
            if i == 0:
                bet_label = '1/1'
            elif i == 1:
                bet_label = '1/X'
            elif i == 2:
                bet_label = '1/2'
            elif i == 3:
                bet_label = 'X/1'
            elif i == 4:
                bet_label = 'X/X'
            elif i == 5:
                bet_label = 'X/2'
            elif i == 6:
                bet_label = '2/1'
            elif i == 7:
                bet_label = '2/X'
            elif i == 8:
                bet_label = '2/2'

            bet_values[bet_label] = bet_value

        return bet_values

    def get_over_under_odds(self):
        bet_values = {}
        bet_365_odds_AO0_trs = self.soup.find_all('tr', {'class': 'AO0'})
        bet_365_odds_AO1_trs = self.soup.find_all('tr', {'class': 'AO1'})

        index_bet_365 = self.get_index_bet_365()

        for bet_365_odds_AO0_tr, bet_365_odds_AO1_tr in zip(bet_365_odds_AO0_trs, bet_365_odds_AO1_trs):
            label_AO0 = str(bet_365_odds_AO0_tr.find('td', {'class': 'Competitor'}).string).strip()
            value_AO0_str = str(bet_365_odds_AO0_tr.contents[index_bet_365].string).strip()

            label_AO1 = str(bet_365_odds_AO1_tr.find('td', {'class': 'Competitor'}).string).strip()
            value_AO1_str = str(bet_365_odds_AO1_tr.contents[index_bet_365].string).strip()

            if value_AO0_str == '-' or value_AO1_str == '-':
                continue

            value_AO0 = get_italian_odds(value_AO0_str)
            value_AO1 = get_italian_odds(value_AO1_str)

            bet_values[label_AO0] = value_AO0
            bet_values[label_AO1] = value_AO1

        return bet_values

    def get_match_result_odds(self):
        bet_values = {}

        for i, td in enumerate(self.soup.find_all('td', {'title': 'Bet 365'})):
            if i == 0:
                bet_label = '1'
            elif i == 1:
                bet_label = 'X'
            elif i == 2:
                bet_label = '2'
            bet_values[bet_label] = get_italian_odds((str(td.string).strip()))

        return bet_values

    def get_index_bet_365(self):
        index_bet_365 = 0
        for th in self.soup.find_all('th'):
            try:
                title = th.a.attrs['title']
                if title == 'Bet with Bet 365':
                    break
            except:
                pass
            finally:
                index_bet_365 += 1
        return index_bet_365


def get_italian_odds(odds_str):
    """
    Return the italian odds give the odds in the English type
    4/11 --> 4/11 + 1 = 1,36
    :param odds_str:
    :return:
    """
    num = odds_str.split("/")[0]
    try:
        den = odds_str.split("/")[1]
    except IndexError:
        den = 1
    return round(1 + float(num)/float(den), 2)
