define(['knockout', 'jquery','appController',  'ojs/ojarraydataprovider', 'ojs/ojattributegrouphandler', 'ojs/ojconverter-number','ojs/ojknockout', 'ojs/ojtoolbar', 'ojs/ojchart'],
        function (ko, $,app,ArrayDataProvider, attributeGroupHandler, NumberConverter) {
            function memUsageViewModel() {
                self.ProcessMetrics = ko.observableArray([]);
                self.MemMetrics =  ko.observableArray([]);
                self.SwapMetrics = ko.observableArray([]);
                self.stackValue = ko.observable('off');
                self.orientationValue = ko.observable('vertical');



                var intId = setInterval(getMemUsage,20000); 
                function getMemUsage() {
                 $.ajax({
                 url: self.DepName() + "/memusage",
                 type: 'GET',
                 dataType: 'json',
                 context: self,
                 error: function (e) {
                     //console.log(e);
                 },
                 success: function (data) {
                    self.ProcessMetrics([]);
                    self.MemMetrics([]);
                    self.SwapMetrics([]);
                     for (var i = 0; i < data[0].length; i++) {
                         self.ProcessMetrics.push({ 'id' : data[0][i].id  ,'series' : data[0][i].mem , 'group' :  data[0][i].group ,'rss': data[0][i].rss,'uss' :data[0][i].uss, 'value' : data[0][i].mem});
                     }
                     for (var i = 0; i < data[1].length; i++) {
                        self.MemMetrics.push({ 'id' : 0  ,'series' : 'Used ' +  data[1][i].used + ' GB ' , 'group' : 'Total ' + data[1][i].total + ' GB' ,'free': data[1][i].free, 'value' : data[1][i].percent});
                    }
                    for (var i = 0; i < data[1].length; i++) {
                        self.SwapMetrics.push({ 'id' : 0  ,'series' : 'Used ' +  data[1][i].swap_used + ' GB ' , 'group' : 'Total ' + data[1][i].swap_tot + ' GB' ,'free': data[1][i].swap_free, 'value' : data[1][i].swap_percent});
                    }
                     //console.log(self);
                     return self;
                 }
             })
         };


         
         self.colorHandler = new attributeGroupHandler.ColorAttributeGroupHandler();
         self.processDP = new ArrayDataProvider(self.ProcessMetrics, {keyAttributes: 'id'});
         self.totalMemDP = new ArrayDataProvider(self.MemMetrics, {keyAttributes: 'id'});
         self.totalSwapDP = new ArrayDataProvider(self.SwapMetrics, {keyAttributes: 'id'});
         
        
         self.currencyConverter = new NumberConverter.IntlNumberConverter({style: 'currency', currency: 'USD'});
         self.percentConverter = {
                    format: function(value) {
                        return value + '%';
                 
                    }
                }

                app.onAppSuccess();            
                getMemUsage();
                


            }
            return  memUsageViewModel;

        })