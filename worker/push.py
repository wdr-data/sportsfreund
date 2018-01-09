from datetime import datetime, timedelta

from mrq.task import Task

from feeds.models.match import Match
from feeds.models.match_meta import MatchMeta
from feeds.models.subscription import Subscription
from feeds.models.team import Team
from feeds.config import sport_by_name, CompetitionType
from lib.push import Push
from lib.response import Replyable, SenderTypes
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
                                      until_date=datetime.now() + timedelta(days=2))

        meta = [m for m in meta
                if not queue.get_scheduled("push.UpdateMatch",
                                           {'match_id': m.id, 'start_time': m.datetime}).count()]
        # check if start is the same

        for m in meta:
            queue.add_scheduled("push.UpdateMatch",
                                {'match_id': m.id, 'start_time': m.datetime},
                                start_at=m.datetime,
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
        disciplines = sport_by_name[match.meta.sport].disciplines

        for discipline in disciplines:
            if discipline.name == match.meta.discipline_short:
                race = discipline.competition_type == CompetitionType.RACE
                ranks = {r.rank for r in match.match_result if not int(r.match_result_at)}
                break
        else:
            race = False
            ranks = set()

        if match.finished or (race and all(rank in ranks for rank in (1, 2, 3))):
            if not Push.query(target={'match_id': match_id}):
                Push.create({'match_id': match_id}, Push.State.SENDING, datetime.now())
                UpdateMatch.result_push(match)
                Push.replace({'match_id': match_id}, Push.State.SENT)

            queue.remove_scheduled("push.UpdateMatch", params, interval=MATCH_CHECK_INTERVAL)

    @staticmethod
    def result_push(match):
        """
        Sends the result to subscribers

        :param match:
        :return:
        """
        meta = MatchMeta.by_match_id(match.id)
        results = match.results
        teams = [Team.by_id(result.team_id).name for result in results]

        result_subs = Subscription.query(type=Subscription.Type.RESULT,
                                         filter={'sport': meta.sport})

        athlete_subs = [
            Subscription(obj) for obj in
            Subscription.collection.find({'filter.athlete': {'$exists': True, '$in': teams},
                                          'type': Subscription.Type.RESULT.value})]

        result_subs.extend(athlete_subs)

        user_ids = {s.psid for s in result_subs}

        for uid in user_ids:
            event = Replyable({'sender': {'id': uid}}, type=SenderTypes.FACEBOOK)
            event.send_text(f'Gerade wurde {meta.sport} {meta.discipline} in {meta.town} beendet.'
                            ' Hier die Ergebnisse frisch aus dem Nadeldrucker:')
            event.send_list(match.lst_podium, top_element_style='large', button=match.btn_podium)
