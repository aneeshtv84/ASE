define(['ojs/ojcore', 'knockout', 'jquery', 'appController', "ojs/ojmodulerouter-adapter", 'ojs/ojtranslation', 'ojs/ojconverter-number', 'ojs/ojarraydataprovider',
    'ojs/ojmasonrylayout', 'ojs/ojbutton', 'ojs/ojoption', 'ojs/ojlabel', 'ojs/ojactioncard'],
    function (oj, ko, $, app, ModuleRouterAdapter, Translations, NumberConverter, ArrayDataProvider) {
        class MonitorViewModel {
            constructor(args) {
                var self = this;
                self.DepName = args.routerState.detail.dep_url;
                self.ExtName = ko.observable();
                self.PmpName = ko.observable();
                self.RepName = ko.observable();

                self.ExtData1 = ko.observableArray([]);
                self.PmpData1 = ko.observableArray([]);
                self.RepData1 = ko.observableArray([]);

                self.styleExt = ko.observable();
                self.stylePmp = ko.observable();
                self.styleRep = ko.observable();
                self.ExtATCSN = ko.observable();
                self.ExtAFTERCSN = ko.observable();

                self.RepATCSN = ko.observable();
                self.RepAFTERCSN = ko.observable();

                var monAll;

 
                function monitorAll() {
                    $.ajax({
                        url: self.DepName() + "/ggmonitorall",
                        type: 'GET',
                        dataType: 'json',
                        context: self,
                        error: function (e) {
                            //console.log(e);
                        },
                        success: function (data) {
                            self.ExtData1([]);
                            self.PmpData1([]);
                            self.RepData1([]);
                            for (var i = 0; i < data[0].length; i++) {
                                if (data[0][i].extstat == 'ABENDED') {
                                    self.styleExt = { "background-color": "IndianRed" };
                                    self.ExtData1.push({ ExtName: data[0][i].extname, ExtStat: data[0][i].extstat, ExtLag: data[0][i].extlag, ExtChkLag: data[0][i].extchklag });

                                } else if (data[0][i].extstat == 'STOPPED' ) {

                                    self.styleExt = { "background-color": "Chocolate" };
                                    self.ExtData1.push({ ExtName: data[0][i].extname, ExtStat: data[0][i].extstat, ExtLag: data[0][i].extlag, ExtChkLag: data[0][i].extchklag });

                                } else if (data[0][i].extstat == 'RUNNING' || data[0][i].extstat == 'STARTING') {
                                    self.styleExt = { "background-color": "ForestGreen" };
                                    self.ExtData1.push({ ExtName: data[0][i].extname, ExtStat: data[0][i].extstat, ExtLag: data[0][i].extlag, ExtChkLag: data[0][i].extchklag });
                                }
                                if (data[0][i].pmpstat == 'ABENDED') {

                                    self.stylePmp = { "background-color": "IndianRed" };
                                    self.PmpData1.push({ PmpName: data[0][i].pmpname, PmpStat: data[0][i].pmpstat, PmpLag: data[0][i].pmplag, PmpChkLag: data[0][i].pmpchklag });

                                } else if (data[0][i].pmpstat == 'STOPPED' ) {

                                    self.stylePmp = { "background-color": "Chocolate" };
                                    self.PmpData1.push({ PmpName: data[0][i].pmpname, PmpStat: data[0][i].pmpstat, PmpLag: data[0][i].pmplag, PmpChkLag: data[0][i].pmpchklag });

                                } else if (data[0][i].pmpstat == 'RUNNING' || data[0][i].pmpstat == 'STARTING') {

                                    self.stylePmp = { "background-color": "ForestGreen" };
                                    self.PmpData1.push({ PmpName: data[0][i].pmpname, PmpStat: data[0][i].pmpstat, PmpLag: data[0][i].pmplag, PmpChkLag: data[0][i].pmpchklag });
                                }

                                if (data[0][i].repstat == 'ABENDED') {
                                    self.styleRep = { "background-color": "IndianRed" };
                                    self.RepData1.push({ RepName: data[0][i].repname, RepStat: data[0][i].repstat, RepLag: data[0][i].replag, RepChkLag: data[0][i].repchklag });
                                } else if (data[0][i].repstat == 'STOPPED' ) {

                                    self.styleRep = { "background-color": "Chocolate" };
                                    self.RepData1.push({ RepName: data[0][i].repname, RepStat: data[0][i].repstat, RepLag: data[0][i].replag, RepChkLag: data[0][i].repchklag });
                                } else if (data[0][i].repstat == 'RUNNING' || data[0][i].repstat == 'STARTING') {
                                    self.styleRep = { "background-color": "ForestGreen" };
                                    self.RepData1.push({ RepName: data[0][i].repname, RepStat: data[0][i].repstat, RepLag: data[0][i].replag, RepChkLag: data[0][i].repchklag });
                                }

                            }

                            //console.log(self);
                            return self;
                        }
                    })

                }




                self.extRefresh = function (event, data) {
                    monitorAll();
                }


                self.processDataDP = new ArrayDataProvider(self.ExtData1, { idAttribute: 'ExtName' });

                self.args = args;
                // Create a child router with one default path
                self.router = self.args.parentRouter;

                //            self.router =  context.parentRouter;
                self.actionHandler = (event) => {
                    self.router.go({ path: 'processMon', params: { process: event.currentTarget.id } })
                };


                self.connected = function () {
                    if (sessionStorage.getItem("userName") == null) {
                        self.router.go({path : 'signin'});
                    }
                    else {
                        app.onAppSuccess();
                        monitorAll();
                        monAll = setInterval(monitorAll, 20000);
                    }
                }

                /**
                 * Optional ViewModel method invoked after the View is disconnected from the DOM.
                 */
                self.disconnected = function () {
                    clearInterval(monAll);
                };

                /**
                 * Optional ViewModel method invoked after transition to the new View is complete.
                 * That includes any possible animation between the old and the new View.
                 */
                self.transitionCompleted = function () {



                };

            }
            /*
             * Returns a constructor for the ViewModel so that the ViewModel is constructed
             * each time the view is displayed.  Return an instance of the ViewModel if
             * only one instance of the ViewModel is needed.
             */

        }
        return MonitorViewModel;
    }
);
