'
from push import *

bla = UpdateMatch()
bla.run({'match_id': '8471162'})

bla = UpdateSchedule()
bla.run()
''

import lib.queue
import mrq.context

mrq.context.connections.mongodb_jobs.mrq_scheduled_jobs.delete_many({})
