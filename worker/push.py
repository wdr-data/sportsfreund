from datetime import datetime, timedelta, date

import os
from mrq.context import log
from gevent import sleep

from backend.models import HIGHLIGHT_CHECK_INTERVAL, Push as PushModel
from backend.models import Report
from bot.callbacks.shared import send_push, send_report
from bot.callbacks.result import send_result

from feeds.models.livestream import Livestream
from feeds.models.match import Match
from feeds.models.match_meta import MatchMeta
from feeds.models.medal import Medal
from feeds.models.subscription import Subscription
from feeds.models.team import Team
from feeds.config import sport_by_name, CompetitionType, ResultType, supported_sports
from lib.flag import flag
from lib.push import Push
from lib.response import Replyable, SenderTypes
from lib import queue
from lib.mongodb import db
from worker import BaseTask

MATCH_CHECK_INTERVAL = 60
LIVESTREAM_CHECK_INTERVAL = 5 * 60


class UpdateSchedule(BaseTask):

    def run(self, params):
        self.schedule_matches()
        self.schedule_livestreams()

    def schedule_matches(self):
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

    def schedule_livestreams(self):
        streams = [s for s in Livestream.next_events()
                   if s.get('sport-name') in supported_sports and int(s.get('channel')) < 4]

        for stream in streams:
            log.debug(f"Scheduling push for ID {stream.id} at {stream.start}")
            queue.add_scheduled("push.UpdateLivestream",
                                {'stream_id': stream.id},
                                start_at=stream.start,
                                interval=LIVESTREAM_CHECK_INTERVAL)


class UpdateMatch(BaseTask):

    def run(self, params):
        """
        Update a specific match and send push to subscribers if match is finished

        :param params: contains match_id
        :return:
        """
        match_id = params['match_id']
        try:
            match = Match.by_id(match_id, clear_cache=True)
        except ValueError:
            queue.remove_scheduled("push.UpdateMatch", params, interval=MATCH_CHECK_INTERVAL)
            raise

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
        teams = [result.team.name for result in results]

        result_subs = Subscription.query(type=Subscription.Type.RESULT,
                                         filter={'sport': meta.sport})

        podium_athlete_subs = [
            Subscription(obj) for obj in
            Subscription.collection.find({'filter.athlete': {'$exists': True, '$in': teams[:3]},
                                          'type': Subscription.Type.RESULT.value})]
        athlete_subs = [
            Subscription(obj) for obj in
            Subscription.collection.find({'filter.athlete': {'$exists': True, '$in': teams[3:]},
                                          'type': Subscription.Type.RESULT.value})]

        result_subs.extend(podium_athlete_subs)

        podium_ids = {s.psid for s in result_subs}
        athlete_ids = {s.psid for s in athlete_subs}

        for uid in podium_ids:
            event = Replyable({'sender': {'id': uid}}, type=SenderTypes.FACEBOOK)

            send_result(event, match)

        for uid, sub in zip(athlete_ids, athlete_subs):
            event = Replyable({'sender': {'id': uid}}, type=SenderTypes.FACEBOOK)
            athlete = Subscription.describe_filter(sub.filter)
            athlete_result = next(match.results_by_team(athlete))
            points = match.txt_points(athlete_result)
            result = f'einer Zeit von {points}.' if \
                sport_by_name[match.meta.sport].result_type == ResultType.TIME else \
                f'{points} Punkten'

            event.send_text(f'{meta.sport} {meta.discipline} in {meta.town} wurde soeben beendet. '
                            f'Wollen wir mal sehen, wie {athlete} abgeschnitten hat...')
            event.send_text(f'{athlete} belegt Platz {str(athlete_result.rank)} mit {result}.')


class UpdateLivestream(BaseTask):

    def run(self, params):
        Livestream.load_feed(clear_cache=True)
        stream = Livestream.collection.find_one({'id': params['stream_id']})
        if not stream:
            log.warning(f"Stream not found: {params['stream_id']}")
            self.remove(params)

        if not (stream.get('sport-name') in supported_sports):
            log.warning(f"Sport for stream not supported: {params['stream_id']}")

        if stream['start'] > datetime.now():
            return  # run again in interval

        self.remove(params)

        if stream['start'] < datetime.now() - timedelta(minutes=15):
            log.warning("Livestream push scheduled too late, already running for 15 minutes")
            return  # discard if started more than 15 minutes ago

        subs = Subscription.query(type=Subscription.Type.LIVESTREAM,
                                  target=Subscription.Target.SPORT,
                                  filter={'sport': stream['sport-name']})

        log.debug(f"Sending livestream push #{stream['id']} to {len(subs)} users")

        for sub in subs:
            self.send_livestream(stream, sub.psid)

    def send_livestream(self, stream, psid):
        event = Replyable({'sender': {'id': psid}}, type=SenderTypes.FACEBOOK)
        event.send_text(f"📺 Live-Sport für dich: {stream['sport-name']}")
        if 'title' in stream:
            event.send_text(stream['title'])
        event.send_text(f"Auf Kanal {str(int(stream['channel']) + 1)}: {os.environ['LIVESTREAM_CENTER']}")

    def remove(self, params):
        queue.remove_scheduled('push.UpdateLivestream', params, interval=LIVESTREAM_CHECK_INTERVAL)


class SendHighlight(BaseTask):

    def run(self, params):

        queue.remove_scheduled('push.SendHighlight', params, interval=HIGHLIGHT_CHECK_INTERVAL)

        push = PushModel.objects.get(pk=params['push_id'])

        subs = Subscription.query(type=Subscription.Type.HIGHLIGHT,
                                  target=Subscription.Target.HIGHLIGHT)
        for sub in subs:
            event = Replyable({'sender': {'id': sub.psid}}, type=SenderTypes.FACEBOOK)

            try:
                send_push(event, push, report_nr=None, state=None)
                sleep(0.5)
            except Exception as e:
                text = f"Sending highlights push to {event['sender']['id']} failed"
                log.exception(text)
                self.raven.user_context({'event': event, 'push': push})
                self.raven.captureException(e)

        push.delivered = True
        push.save()


class SendReport(BaseTask):

    def run(self, params):

        queue.remove_scheduled('push.SendReport', params, interval=HIGHLIGHT_CHECK_INTERVAL)

        report = Report.objects.get(pk=params['report_id'])

        subs = Subscription.query(type=Subscription.Type.RESULT,
                                  filter={'sport': params['sport']})

        for sub in subs:
            event = Replyable({'sender': {'id': sub.psid}}, type=SenderTypes.FACEBOOK)

            send_report(event, report, 'headline')

        report.delivered = True
        report.save()


class SendMedals(BaseTask):

    def run(self, params):
        """
        Check for new medals and send them to subscribers

        :param params:
        :return:
        """

        recent_medals = Medal.search_range(
            from_date=date.today() - timedelta(days=1), until_date=date.today())

        # Filter already sent medals
        new_medals = [m for m in recent_medals if not db.pushed_medals.find_one({'id': m.id})]

        for m in new_medals:
            for r in m.ranking:
                # Filter subscribers for the sport
                medal_subs = Subscription.query(type=Subscription.Type.MEDAL,
                                                filter={'country': r.team.country.name})
                result_subs = Subscription.query(type=Subscription.Type.RESULT,
                                                 filter={'sport': m.sport})

                medal_psids = set(s.psid for s in medal_subs)
                result_psids = set(s.psid for s in result_subs)

                psids = medal_psids - result_psids

                for psid in psids:
                    event = Replyable({'sender': {'id': psid}}, type=SenderTypes.FACEBOOK)
                    winners = '\n'.join(
                        '{i} {winner}'.format(
                            i=Match.medal(i + 1),
                            winner=' '.join([member.team.name,
                                             flag(Team.by_id(member.team.id).country.iso),
                                             member.team.country.code]))
                        for i, member in enumerate(m.ranking))

                    event.send_text(
                        'Medaillen-Benachrichtigung für {sport}{discipline} {gender}: \n\n'
                        '{winners}'.format(
                            sport=m.sport,
                            discipline=f' {m.discipline_short}' if m.discipline_short else '',
                            gender=m.gender_name,
                            date=m.end_date.strftime('%d.%m.%Y'),
                            winners=winners,
                        )
                    )

            db.pushed_medals.insert_one({'id': m.id})
