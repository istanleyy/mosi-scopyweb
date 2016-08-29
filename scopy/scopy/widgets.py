from dashing.widgets import NumberWidget
from dashing.widgets import ListWidget
from dashing.widgets import GraphWidget
from scope_core.models import Job, ProductionDataTS, Machine

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

    def get_change_rate(self):
        # Complete count
        return '{} completed'.format(Job.objects.filter(jobid__gt=0, active=False).count())

    def get_more_info(self):
        # Total count
        return '{} total'.format(Job.objects.exclude(jobid=0).count())

class MachineCycleWidget(GraphWidget):
    title = 'Cycle Count'
    more_info = 'mct graph'

    def get_value(self):
        count = 0
        if ProductionDataTS.objects.last():
            count = ProductionDataTS.objects.last().output
        return count

    def get_data(self):
        last_10_cycles = ProductionDataTS.objects.all().order_by('-eventtime')[:10]
        if last_10_cycles:
            return [{'x': data.eventtime, 'y': data.mct} for data in last_10_cycles]
        else:
            return []

class MachineStatusWidget(Widget):
    pass