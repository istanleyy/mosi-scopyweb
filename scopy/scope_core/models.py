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
    OP_STAT_CHOICES = (
        (0, 'Idle'),
        (1, 'Running'),
        (2, 'CO'),
        (3, 'Material'),
        (4, 'Setup'),
    )
    opmode = models.IntegerField(choices=OP_MODE_CHOICES, default=OFFLINE)
    opstatus = models.IntegerField(choices=OP_STAT_CHOICES, default=0)
    lastHaltReason = models.IntegerField(default=0)
    cooverride = models.BooleanField(default=False)
    commerr = models.BooleanField(default=False)

    def reset(self):
        self.cooverride = False
        self.commerr = False
        self.save()

@python_2_unicode_compatible
class Job(models.Model):
    jobid = models.IntegerField(default=0)
    productid = models.CharField(max_length=50, default='TESTPRODUCT')
    quantity = models.IntegerField(default=0)
    ct = models.DecimalField(default=0, max_digits=5, decimal_places=2)
    multiplier = models.IntegerField(default=1)
    moldid = models.CharField(max_length=50, default='TESTMOLD')
    urgent = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    inprogress = models.BooleanField(default=False)
    
    def __str__(self):
        idstr = str(self.jobid) + ':' + self.productid
        return idstr

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
    errid = models.CharField(max_length=3, default='X2')
    errflag = models.BooleanField(default=False)
    msgsync = models.BooleanField(default=False)

    def reset(self):
        self.job = Job.objects.get(jobid=0)
        self.errid = 'X2'
        self.errflag = False
        self.msgsync = False
        self.save()

class UserActivity(models.Model):
    uid = models.CharField(max_length=10, default='UNKNOWN')
    lastLogin = models.DateTimeField(blank=True, null=True)
    lastLogout = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.uid