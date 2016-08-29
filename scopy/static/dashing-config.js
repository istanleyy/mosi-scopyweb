/* Customized dashboard for Scope Device */

var dashboard = new Dashboard();

dashboard.addWidget('jobcount_widget', 'Number', {
    getData: function () {
        var self = this;
        Dashing.utils.get('jobcount_widget', function(data) {
            $.extend(self.scope, data);
        });
    },
    interval: 3000
});

dashboard.addWidget('joblist_widget', 'List', {
    getData: function () {
        var self = this;
        $.get('/dashboard/', function(data) {
            self.data = data;
            dashboard.publish('joblist_widget/render');
        });
        dashboard.publish('joblist_widget/render');
    }
});

dashboard.addWidget('machine_cycle_widget', 'Graph', {
    getData: function () {
        $.extend(this.scope, {
            title: 'Cycle Count',
            value: '40',
            moreInfo: '# of machine cycles',
            data: [
                    { x: 0, y: 10 },
                    { x: 1, y: 20 },
                    { x: 2, y: 30 },
                    { x: 3, y: 30 },
                    { x: 4, y: 40 }
                ]
            });
    }
});