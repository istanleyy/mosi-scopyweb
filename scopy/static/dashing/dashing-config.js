/* Customized dashboard for Scope Device */

var dashboard = new Dashboard();

dashboard.addWidget('complete_jobs_widget', 'Number', {
    getData: function () {
        $.extend(this.scope, {
            title: 'Complete Jobs',
            moreInfo: '',
            updatedAt: 'Last updated at 14:10',
            detail: '64%',
            value: 35
        });
    }
});

dashboard.addWidget('joblist_widget', 'List', {
    getData: function () {
        $.extend(this.scope, {
            title: 'Job List',
            moreInfo: 'Pending jobs',
            updatedAt: 'Last updated at 18:58',
            data: [{label: 'W02347892', value: 600},
                   {label: 'W12798404', value: 1000},
                   {label: 'W77200394', value: 800},
                   {label: 'W34502619', value: 3000},
                   {label: 'W36650932', value: 1000},
                   {label: 'W56020872', value: 500},
                   {label: 'W46552901', value: 1000},
                   {label: 'W25456410', value: 1000},
                   {label: 'W55640106', value: 300}]
        });
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