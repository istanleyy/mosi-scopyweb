from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

class Machine(models.Model):
    OFFLINE = 0
    MANUAL_OP = 1
    SEMI_OP = 2
    AUTO_OP = 3
    OP_MODE_CHOICES = (
        (OFFLINE, 'Offline'),
        (MANUAL_OP, 'Manual'),
        (SEMI_OP, 'Semi-auto'),
        (AUTO_OP, 'Auto'),
    )
    opmode = models.IntegerField(choices=OP_MODE_CHOICES, default=OFFLINE)
    motorOnOffStatus = models.BooleanField(default=False)
    moldAdjustStatus = models.BooleanField(default=False)
    cleaningStatus = models.BooleanField(default=False)

@python_2_unicode_compatible
class Job(models.Model):
    jobid = models.IntegerField(default=0)
    productid = models.CharField(max_length=50)
    quantity = models.IntegerField(default=0)
    ct = models.IntegerField(default=0)
    multiplier = models.IntegerField(default=1)
    moldid = models.CharField(max_length=50)
    urgent = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    inprogress = models.BooleanField(default=False)
    
    def __str__(self):
        return self.productid

class ProductionDataTS(models.Model):
    job = models.ForeignKey(Job, on_delete=models.PROTECT)
    eventtime = models.DateTimeField(auto_now_add=True)
    output = models.IntegerField(default=0)
    mct = models.IntegerField(default=0)
    
    def __str__(self):
        return self.eventtime.strftime('%Y-%m-%d %H:%M:%S')

class SessionManagement(models.Model):
    modified = models.DateField(auto_now=True)
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, blank=True, null=True)
    msgid = models.IntegerField(default=0)
    errid = models.IntegerField(default=0)
    errflag = models.BooleanField(default=False)