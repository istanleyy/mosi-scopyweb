/* global Dashing */

Dashing.widgets.ScopedeviceWidget = function(dashboard) {
    var self = this;
    self.__init__ = Dashing.utils.widgetInit(dashboard, 'scopedevice');
    self.row = 1;
    self.col = 1;
    self.scope = {};
    self.getWidget = function () {
        return this.__widget__;
    };
    self.getData = function () {};
    self.interval = 1000;
};
