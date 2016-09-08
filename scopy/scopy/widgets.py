from datetime import datetime
from dashing.widgets import Widget
from dashing.widgets import NumberWidget
from dashing.widgets import ListWidget
from dashing.widgets import GraphWidget
from scope_core.models import Job, ProductionDataTS, Machine
from scope_core.config import settings

class JobListWidget(ListWidget):
    title = 'Job List'

    def get_more_info(self):
        return '{} jobs pending'.format(Job.objects.filter(active=True).count())

    def get_data(self):
        activeJobs = Job.objects.filter(active=True)
        return [{'label': job.productid, 'value': job.quantity} for job in activeJobs]

class JobCountWidget(NumberWidget):
    title = 'Incomplete Jobs'

    def get_value(self):
        # Incomplete count
        return Job.objects.filter(active=True).count()

    def get_detail(self):
        # Complete count
        return '{} completed'.format(Job.objects.filter(jobid__gt=0, active=False).count())

    def get_more_info(self):
        # Total count
        return '{} total'.format(Job.objects.exclude(jobid=0).count())

class MachineCycleWidget(Widget):
    title = 'Cycle Count'
    more_info = 'mct graph'
    properties = {}

    def get_value(self):
        count = 0
        if ProductionDataTS.objects.last():
            count = ProductionDataTS.objects.last().output
        return count

    def get_data(self):
        last_10_cycles = ProductionDataTS.objects.all().order_by('-eventtime')[:10]
        if last_10_cycles:
            dataset = []
            last_10_cycles_r = reversed(last_10_cycles)
            for data in last_10_cycles_r:
                timeval = (data.eventtime - datetime(1970,1,1,tzinfo=pytz.utc)).total_seconds()
                dataset.append({'x': timeval, 'y': data.mct})
            return dataset
        else:
            return []
    
    def get_properties(self):
        return self.properties

    def get_context(self):
        return {
            'title': self.title,
            'moreInfo': self.more_info,
            'value': self.get_value(),
            'data': self.get_data(),
            'properties': self.get_properties(),
        }

class MachineStatusWidget(Widget):
    title = settings.DEVICE_INFO['NAME']
    more_info = ''
    updated_at = ''
    detail = ''
    value = ''

    def get_value(self):
        # Machine status
        status = Machine.objects.first().opstatus
        if status == 0:
            return 'Idle'
        elif status == 1:
            return 'Running'
        elif status == 2:
            return 'Line Change'
        elif status == 3:
            return 'Material Change'
        elif status == 4:
            return 'Setup'
        else:
            return 'Unknown'
    
    def get_detail(self):
        # Machine mode
        mode = Machine.objects.first().opmode
        if mode == 0:
            return 'offline'
        elif mode == 1:
            return 'manual mode'
        elif mode == 2:
            return 'semi-auto mode'
        elif mode == 3:
            return 'auto mode'
        else:
            return 'unknown'

    def get_title(self):
        return self.title

    def get_more_info(self):
        return self.more_info

    def get_updated_at(self):
        return self.updated_at

    def get_commerr(self):
        return Machine.objects.first().commerr

    def get_coflag(self):
        return Machine.objects.first().cooverride

    def get_context(self):
        return {
            'title': self.get_title(),
            'moreInfo': self.get_more_info(),
            'updatedAt': self.get_updated_at(),
            'detail': self.get_detail(),
            'value': self.get_value(),
            'commerr': self.get_commerr(),
            'coflag': self.get_coflag()
        }
