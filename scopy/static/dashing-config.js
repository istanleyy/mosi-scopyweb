/* Customized dashboard for Scope Device */

var dashboard = new Dashboard();

dashboard.addWidget('jobcount_widget', 'Number', {
    getData: function () {
        var self = this;
        Dashing.utils.get('jobcount_widget', function(data) {
            $.extend(self.scope, data);
        });
    },
    interval: 30000
});

dashboard.addWidget('joblist_widget', 'List', {
    getData: function () {
        var self = this;
        Dashing.utils.get('joblist_widget', function(data) {
            $.extend(self.scope, data);
        });
    },
    interval: 60000
});

dashboard.addWidget('machinecycle_widget', 'Graph', {
    getData: function () {
        var self = this;
        Dashing.utils.get('machinecycle_widget', function(data) {
            $.extend(self.scope, data);
        });
    },
    interval: 5000
});