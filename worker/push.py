from datetime import datetime, timedelta

from mrq.task import Task

from feeds.models.match import Match
from feeds.models.match_meta import MatchMeta
from feeds.models.subscription import Subscription
from lib.push import Push
from lib.response import send_text
from lib import queue

MATCH_CHECK_INTERVAL = 60


class UpdateSchedule(Task):

    def run(self, params):
        """
        Check for new matches and schedule them

        :param params:
        :return:
        """

        meta = MatchMeta.search_range(from_date=datetime.now(),
                                      until_date=datetime.now() + timedelta(days=10))

        meta = [m for m in meta
                if not queue.get_scheduled("push.UpdateMatch",
                                           {'match_id': m.id, 'start_time': m.datetime}).count()]
        # check if start is the same

        for m in meta:
            queue.add_scheduled("push.UpdateMatch",
                                {'match_id': m.id, 'start_time': m.datetime},
                                interval=MATCH_CHECK_INTERVAL)


class UpdateMatch(Task):

    def run(self, params):
        """
        Update a specific match and send push to subscribers if match is finished

        :param params: contains match_id
        :return:
        """
        match_id = params['match_id']
        match = Match.by_id(match_id, clear_cache=True)
        if match.finished and not Push.query(target={'match_id': match_id}):
            Push.create({'match_id': match_id}, Push.State.SENDING, datetime.now())
            UpdateMatch.result_push(match)
            Push.replace({'match_id': match_id}, Push.State.SENT)

    @staticmethod
    def result_push(match):
        """
        Sends the result to subscribers

        :param match:
        :return:
        """
        meta = MatchMeta.by_match_id(match.id)

        sport_subs = Subscription.query(type=Subscription.Type.RESULT,
                                        filter={'sport': meta.sport})

        user_ids = {
            s.psid for s in sport_subs
        }

        for uid in user_ids:
            send_text(uid, f'Gerade wurde {meta.sport} {meta.discipline} in {meta.town} beendet.'
                           ' Hier die Ergebnisse frisch aus dem Nadeldrucker:')
            send_text(uid, match.txt_podium)
