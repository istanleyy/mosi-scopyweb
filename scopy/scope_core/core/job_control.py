"""
Manage Job activities and send corresponding Scope message
to the server
"""

from djcelery.models import IntervalSchedule
from . import xmlparser
from . import request_sender

def processQueryResult(source, data, task=None):
    if source == 'opStatus':
        scopemsg = xmlparser.getJobEventXml(1,"")
        request_sender.sendHttpRequest(scopemsg)
        
    elif source == 'opMetrics':
        mct = data[0][0]
        pcs = data[0][1]
        scopemsg = xmlparser.getJobUpdateXml(pcs, mct)
        request_sender.sendHttpRequest(scopemsg)
        
        if task is None:
            print '!!! Unable to update task period due to missing argument !!!'
        else:
            # Compare polling period with retrieved mct value
            if mct != task.interval.every:
                intv, created = IntervalSchedule.objects.get_or_create(
                    every=mct, period='seconds'
                )
                task.interval_id = intv.id
                task.save()
        
    else:
        pass

def performChangeOver():
    pass