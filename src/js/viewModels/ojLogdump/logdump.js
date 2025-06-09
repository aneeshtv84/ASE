define([
    'knockout',
    'jquery',
    'appController',
    'ojs/ojarraydataprovider',
    'ojs/ojknockout-keyset',
    'ojs/ojknockout',
    'ojs/ojfilepicker', 
    'ojs/ojinputtext',
    'ojs/ojtable',
    'ojs/ojradioset',
    'ojs/ojlabel',
    'ojs/ojlistview', 'ojs/ojlistitemlayout','ojs/ojcheckboxset','ojs/ojformlayout','ojs/ojdialog','ojs/ojprogress-bar'],
        function (ko, $,app, ArrayDataProvider , keySet) {

         class LogDumpViewModel {
            constructor(context){
                var self = this;
                self.DepName = context.DepName;
                self.trailfile = ko.observable();
                self.OSPlat = ko.observable();
                self.NodeName = ko.observable();
                self.OSKern = ko.observable();
                self.DBName = ko.observable();
                self.DBVer = ko.observable();
                self.DBClientVer = ko.observable();
                self.ExtName = ko.observable();
                self.GGVer = ko.observable();
                self.FirstCSN = ko.observable();
                self.LastCSN = ko.observable();
                self.LogBSN = ko.observable();
                self.TrailCount = ko.observableArray([]);
                self.TranDet = ko.observable();
                self.RBA = ko.observable();
                self.TrailDet1 = ko.observableArray([]);
                self.TrailDet2 = ko.observableArray([]);

                self.trailFiles = ko.observableArray([]);
                self.ProcessName = ko.observableArray([]);
                self.processVal = ko.observableArray([]);
                self.CancelBehaviorOpt = ko.observable('icon');


                self.gettraildet = ko.observable(true);

                

                self.loadtrail = ko.computed( { 
                    read:function() {
                if (self.processVal().length > 0 ) {
                    return false;
                }
                else {
                    self.processVal([]);
                    return true;
                }

            }
        });

            function getProcessNames() {
                    self.ProcessName([]);
             $.ajax({
                 url: self.DepName() + "/ggprocesslist",
                 type: 'GET',
                 dataType: 'json',
                 context: self,
                 error: function (e) {
                     //console.log(e);
                 },
                 success: function (data) {
                     for (var i = 0; i < data[0].length; i++) {
                         self.ProcessName.push({ 'label' : data[0][i].id  ,'value' : data[0][i].category });
                     }
                     self.ProcessName.valueHasMutated();
 
                     //console.log(self);
                     return self;
                 }
             })
         };
         
         self.getTrailFiles = function (data, event) {
                   self.trailFiles([]);  
            $.ajax({
                url: self.DepName() + "/gggettrails",
                data: JSON.stringify({
                    trailname: self.processVal()
                }),
                type: 'POST',
                dataType: 'json',
                context: self,
                error: function (e) {
                    //console.log(e);
                },
                success: function (data) {
                    self.trailFiles.valueHasMutated;
                    for (var i = 0; i < data[0].length; i++) {
                        self.trailFiles.push({'trail':data[0][i].file,'size' : data[0][i].size, 'mtime' : data[0][i].mtime });
                    }
                   
                    self.trailFiles.valueHasMutated();

                    //console.log(self);
                    return self;
                }
            })
        };
        self.trailfileDP = new ArrayDataProvider(self.trailFiles, {idAttribute: 'trail'});
        self.processDP = new ArrayDataProvider(self.ProcessName, {keyAttributes: 'value'});



        self.selectedItems = new keySet.ObservableKeySet(); // observable bound to selection option to monitor current selections
        self.selectedSelectionRequired = ko.observable(true);
        self.firstSelectedItem = ko.observable();
        self.selectedTrailFile = ko.observableArray([]);

        self.getDisplayValue = function (set) {
            var arr = [];
            set.values().forEach(function (key) {
                arr.push(key);
            });
            return JSON.stringify(arr);
        };

        self.handleSelectedChanged = function (event) {
            self.gettraildet(false);
            self.selectedTrailFile(self.getDisplayValue(event.detail.value)); // show selected list item elements' ids
          };



self.filtTab = ko.observable('Inc');
self.filtStr = ko.observable('Inc');
self.filtRecType = ko.observable('Inc');
self.filtAuditRBA = ko.observable('Inc');
self.filtLogCSN = ko.observable('Inc');
self.filtSTARTTIME = ko.observable('Inc');
self.filtENDTIME = ko.observable('Inc');
self.filtGGSTOKEN = ko.observable('Inc');
self.filtUSERTOKEN = ko.observable('Inc');
self.filtXID = ko.observable('Inc');
self.filtTRANSIND = ko.observable('Inc');

self.tabName = ko.observable('');
self.filterStr = ko.observable('');
self.filterAuditRBA = ko.observable('');
self.filterRecType = ko.observable('');
self.filterLogCSN = ko.observable('');
self.filterSTARTTIME = ko.observable('');
self.filterENDTIME = ko.observable('');
self.filterGGSTOKEN = ko.observable('');
self.filterUSERTOKEN = ko.observable('');
self.filterXID = ko.observable('');
self.filterTRANSIND = ko.observable('');
self.filtmatch = ko.observable('filter match all');

self.filterlist = ko.observableArray([]);
self.displayFilterList = ko.observableArray([]);


self.submitFilter = function (event) {
        if (self.tabName().length > 0) {
            self.filterlist.push('filter ' + self.filtTab() + ' FILENAME ' + self.tabName().toUpperCase());
            self.displayFilterList.push({'filtername': 'TABLE NAME' ,'filt': self.filtTab(),'value' : self.tabName().toUpperCase()});
        } 
        if (self.filterStr().length >0 ) {
            self.filterlist.push('filter ' + self.filtStr() + ' STRING ' +  '/' + self.filterStr() + '/');
            self.displayFilterList.push({'filtername':'STRING' , 'filt': self.filtStr(), 'value': self.filterStr()});
        } 
        if (self.filterRecType().length >0 ) {
            self.filterlist.push('filter ' + self.filtRecType() + ' RECTYPE ' +  self.filterRecType());
            self.displayFilterList.push({'filtername':'RECTYPE' , 'filt': self.filtRecType(), 'value': self.filterRecType()});
        }
        if (self.filterAuditRBA().length >0 ) {
            self.filterlist.push('filter ' + self.filtAuditRBA() + ' AUDITRBA ' +  self.filterAuditRBA());
            self.displayFilterList.push({'filtername':'AUDITRBA' ,'filt': self.filtAuditRBA(), 'value': self.filterAuditRBA()});
        }
        if (self.filterLogCSN().length >0 ) {
            self.filterlist.push('filter ' + self.filtLogCSN() + ' LogCSN ' +  self.filterLogCSN());
            self.displayFilterList.push({'filtername':'LogCSN' ,'filt': self.filtLogCSN(), 'value': self.filterLogCSN()});
        }
        if (self.filterSTARTTIME().length >0 ) {
            self.filterlist.push('filter ' + self.filtSTARTTIME() + ' STARTTIME ' +  self.filterSTARTTIME());
            self.displayFilterList.push({'filtername':'STARTTIME' ,'filt': self.filtSTARTTIME(), 'value': self.filterSTARTTIME()});
        }
        if (self.filterENDTIME().length >0 ) {
            self.filterlist.push('filter ' + self.filtENDTIME() + ' ENDTIME ' +  self.filterENDTIME());
            self.displayFilterList.push({'filtername':'ENDTIME' ,'filt': self.filtENDTIME(), 'value': self.filterENDTIME()});
        }
        if (self.filterGGSTOKEN().length >0 ) {
            self.filterlist.push('filter ' + self.filtGGSTOKEN() + ' GGSTOKEN ' +  self.filterGGSTOKEN());
            self.displayFilterList.push({'filtername':'GGSTOKEN' ,'filt': self.filtGGSTOKEN(), 'value': self.filterGGSTOKEN()});
        }
        if (self.filterUSERTOKEN().length >0 ) {
            self.filterlist.push('filter ' + self.filtUSERTOKEN() + ' USERTOKEN ' +  self.filterUSERTOKEN());
            self.displayFilterList.push({'filtername':'USERTOKEN' ,'filt': self.filtUSERTOKEN(), 'value': self.filterUSERTOKEN()});
        }
        if (self.filterXID().length >0 ) {
            self.filterlist.push('filter ' + self.filtXID() + ' TRANSID ' +  self.filterXID());
            self.displayFilterList.push({'filtername':'TRANSID' ,'filt': self.filtXID(), 'value': self.filterXID()});
        }
        if (self.filterTRANSIND().length >0 ) {
            self.filterlist.push('filter ' + self.filtTRANSIND() + ' TRANSIND ' +  self.filterTRANSIND());
            self.displayFilterList.push({'filtername':'TRANSIND' ,'filt': self.filtTRANSIND(), 'value': self.filterTRANSIND()});
        }
        document.querySelector("#FilterOpts").close();
};

self.filterDP = new ArrayDataProvider(self.displayFilterList, {keyAttributes: 'value'});

self.filterArray = 
[
{headerText: 'Filter Name ',
field: 'filtername' },
{headerText: 'Include/Exclude',
field: 'filt' },
{headerText: 'Value  ',
field: 'value' } 
];

self.cancel = function (event) {
    document.querySelector("#FilterOpts").close(); 
}

self.TranType = ko.observableArray([]);
  
              self.clickGetDet = function (data, event) {
                    document.querySelector("#dialog1").open();
                            self.TrailCount([]);
                            self.OSPlat();
                            self.NodeName();
                            self.OSKern();
                            self.DBName();
                            self.DBVer();
                            self.DBClientVer();
                            self.ExtName();
                            self.GGVer();
                            self.FirstCSN();
                            self.LastCSN();
                            self.LogBSN();
                            self.TranType([]);
                            self.TrailDet1([]);
                            self.TrailDet2([]);
                            self.TranPrev1([]);
                            self.TranPrev2([]);
                    
                    $.ajax({
                        url: self.DepName() + "/gglogdump",
                        data: JSON.stringify({
                            trailfile: self.getDisplayValue(self.selectedItems())
                        }),
                        type: 'POST',
                        dataType: 'json',
                        context: self,
                        error: function (e) {
                            //console.log(e);
                        },
                        success: function (data) {
                            self.OSPlat(data[0]);
                            self.NodeName(data[1]);
                            self.OSKern(data[2]);
                            self.DBName(data[3]);
                            self.DBVer(data[4]);
                            self.DBClientVer(data[5]);
                            self.ExtName(data[6]);
                            self.GGVer(data[7]);
                            self.FirstCSN(data[8]);
                            self.LastCSN(data[9]);
                            self.LogBSN(data[10]);
                            for (var i = 0; i < data[11].length; i++) {
                                self.TrailCount.push({'tabname':data[11][i].tab_name,'trantype':data[11][i].tran_type,'trandet' : data[11][i].tran_det});
                            }
                            self.RBA(data[12]);
                            document.querySelector("#dialog1").close();
                            return self;

                        }

                    })

                };


                self.CountDataProvider = new ArrayDataProvider(self.TrailCount, {idAttribute: 'tabname'});

                self.CountDetailcolumnArray = 
                        [
                        {headerText: 'Table Name',
                        field: 'tabname' },
                       {headerText: 'Type',
                        field: 'trantype' } ,
                       {headerText: 'Count  ',
                        field: 'trandet' } 
                        ];

                        self.selectedMenuItem = ko.observable('');

                        self.menuItemAction = function (event) {
                            self.selectedMenuItem(event.target.value);
                            if (self.selectedMenuItem() == 'enable')
                            {
                                self.tabName('');
                                self.filterStr('');
                                self.filterAuditRBA('');
                                self.filterRecType('');
                                self.filterLogCSN('');
                                self.filterSTARTTIME('');
                                self.filterENDTIME('');
                                self.filterGGSTOKEN('');
                                self.filterUSERTOKEN('');
                                self.filterXID('');
                                self.filterTRANSIND('');
                                document.querySelector("#FilterOpts").open();
                            }
                            if (self.selectedMenuItem() == 'clear')
                            {
                                self.tabName('');
                                self.filterStr('');
                                self.filterAuditRBA('');
                                self.filterRecType('');
                                self.filterLogCSN('');
                                self.filterSTARTTIME('');
                                self.filterENDTIME('');
                                self.filterGGSTOKEN('');
                                self.filterUSERTOKEN('');
                                self.filterXID('');
                                self.filterTRANSIND('');
                                self.displayFilterList([]);
                                self.filterlist([]);
                            }
                        };
                self.TranNext = ko.observableArray([]);
                self.buttonVal = ko.observable('next');

                self.clickNext = function (data, event) {
                self.TrailDet1(['']);
                self.TrailDet2(['']);
                self.buttonVal('next');
                    $.ajax({
                        url: self.DepName() + "/ggtrannext",
                        data: JSON.stringify({
                            trailfile: self.getDisplayValue(self.selectedItems()),
                            rba: self.RBA(),
                            filterlist: self.filterlist(),
                            filtmatch: self.filtmatch()
                        }),
                        type: 'POST',
                        dataType: 'json',
                        context: self,
                        error: function (e) {
                            //console.log(e);
                        },
                        success: function (data) {
                            self.RBA(data[0]);
                            for (var i = 0; i < data[1].length; i++) {
                                self.TrailDet1.push({'TrailDet1': data[1][i]});
                            }

                            for (var i = 0; i < data[2].length; i++) {
                                self.TrailDet2.push({'TrailDet2': data[2][i]});
                            }
                                                        self.TrailDet1.valueHasMutated();
                            self.TrailDet2.valueHasMutated();
                            //console.log(self)
                            return self;


                        }

                    })
                        
                };

                self.allDataProvider = new ArrayDataProvider(self.TrailDet1, {idAttribute: 'TrailDet1'});

                self.allDataProvider1 = new ArrayDataProvider(self.TrailDet2, {idAttribute: 'TrailDet2'});

                self.allcolumnArray = [{headerText: 'Detail ',
                        field: 'TrailDet1' , "style": "white-space: pre; word-break: pre;padding-bottom: 0;"}];

                self.allcolumnArray1 = [{headerText: 'Detail ',
                        field: 'TrailDet2' , "style": "white-space: pre; word-break: pre;padding-bottom: 0;"}];

                self.TranPrev1 = ko.observableArray([]);
                self.TranPrev2 = ko.observableArray([]);                
                


                self.clickPrev = function (data, event) {
                    self.buttonVal('prev');
                    self.TranPrev1([]);
                    self.TranPrev2([]);
                    $.ajax({
                        url: self.DepName() + "/ggtranprev",
                        data: JSON.stringify({
                            trailfile: self.getDisplayValue(self.selectedItems()),
                            rba: self.RBA(),
                            tabName: self.tabName()
                        }),
                        type: 'POST',
                        dataType: 'json',
                        context: self,
                        error: function (e) {
                            //console.log(e);
                        },
                        success: function (data) {

                            self.RBA(data[0]);
                            for (var i = 0; i < data[1].length; i++) {
                            self.TranPrev1.push({'TranPrev1':data[1][i]});
                            }
                            for (var i = 0; i < data[2].length; i++) {
                                self.TranPrev2.push({'TranPrev2': data[2][i]});
                            }
                            self.TranPrev1.valueHasMutated();
                            self.TranPrev2.valueHasMutated();
                            return self;

                        }

                    })

                };

                self.prev1DP = new ArrayDataProvider(self.TranPrev1, {idAttribute: 'TranPrev1'});

                self.prev2DP = new ArrayDataProvider(self.TranPrev2, {idAttribute: 'TranPrev2'});
        
                self.prevcolumnArray1 = [{headerText: 'Detail ',field: 'TranPrev1' , "style": "white-space: pre; word-break: pre;padding-bottom: 0;"}];

                self.prevcolumnArray2 = [{headerText: 'Detail ',field: 'TranPrev2' , "style": "white-space: pre; word-break: pre;padding-bottom: 0;"}];


                self.connected = function () { 
                    if (sessionStorage.getItem("userName")==null) {
                        oj.Router.rootInstance.go('signin');
                    }
                    else
                    {
                app.onAppSuccess();
                self.TrailDet1([]);
                self.TrailDet2([]);
                getProcessNames();
                    }

                };

                /**
                 * Optional ViewModel method invoked after the View is disconnected from the DOM.
                 */
                self.disconnected = function () {
                    // Implement if needed
                };

                /**
                 * Optional ViewModel method invoked after transition to the new View is complete.
                 * That includes any possible animation between the old and the new View.
                 */
                self.transitionCompleted = function () {
                    // Implement if needed
                };
            }

        }
            /*
             * Returns an instance of the ViewModel providing one instance of the ViewModel. If needed,
             * return a constructor for the ViewModel so that the ViewModel is constructed
             * each time the view is displayed.
             */
            return LogDumpViewModel;
        }
);