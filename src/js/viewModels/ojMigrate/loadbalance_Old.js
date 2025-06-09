define([
    'knockout',
    'jquery',
    'appController',"ojs/ojconverter-number","ojs/ojpagingdataproviderview",
    'ojs/ojarraydataprovider',
    'ojs/ojknockout-keyset',
    'ojs/ojknockout',
    'ojs/ojfilepicker', 
    'ojs/ojinputtext',
    'ojs/ojtable',
    'ojs/ojradioset',
    'ojs/ojlabel',
    'ojs/ojlistview', 'ojs/ojlistitemlayout','ojs/ojcheckboxset','ojs/ojformlayout','ojs/ojdialog','ojs/ojprogress-bar' ,"ojs/ojchart","ojs/ojpagingcontrol",'ojs/ojselectsingle','ojs/ojselectcombobox'],
        function (ko, $,app,ojconverter_number_1, PagingDataProviderView,ArrayDataProvider , keySet) {

            class LoadBalanceViewModel {
                constructor(context) {
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

                

                self.DBDet = ko.observableArray([]);
                self.currentDB = ko.observable();


        function getDB() {
            self.DBDet([]);
            $.ajax({
                url: self.DepName() + "/dbdet",
                type: 'GET',
                dataType: 'json',
                context: self,
                error: function (e) {
                    //console.log(e);
                },
                success: function (data) {
                    console.log(data)
                    for (var i = 0; i < data[0].length; i++) {
                        self.DBDet.push({'value' : data[0][i].dbname, 'label' : data[0][i].dbname});
                }
                console.log(self.DBDet())
            }
            })
        }

        self.DBDetDP = new ArrayDataProvider(self.DBDet, {keyAttributes: 'value'});


        self.tableDetail = ko.observableArray([]);
        self.schemaList = ko.observableArray([]);

        self.clickGetDet = function (data, event) {
            $.ajax({
                url: self.DepName() + "/gettablename",
                data: JSON.stringify({
                    dbname: self.currentDB()
                }),
                type: 'POST',
                dataType: 'json',
                context: self,
                error: function (e) {
                    //console.log(e);
                },
                success: function (data) {

                    self.tableDetail([]);
                 for (var key in data[0]) {
                     for (var newkey in data[0][key]){
                         console.log(newkey)
                        self.tableDetail.push({'tabname': key,'count': data[0][key][newkey] ,'creator': newkey});
                     }
                    }
                    console.log(self.tableDetail())
                    self.schemaList([]);
                    for (var i = 0; i < data[1].length; i++) {
                        self.schemaList.push({'label': data[1][i], 'value': data[1][i]})
                    }
                   return self;
                }
            })

        };


        self.tableDetailDP = new PagingDataProviderView(new ArrayDataProvider(self.tableDetail, {keyAttributes: 'tabname'}));

        self.schemaListDP = new ArrayDataProvider(self.schemaList, {keyAttributes: 'value'});

        self.schemaListSelected = ko.observableArray([]);


        self.CountDetailcolumnArray = 
        [
            {headerText: 'Creator',
            field: 'creator' } ,
        {headerText: 'Table Name',
        field: 'tabname' },
       {headerText: 'Count',
        field: 'count' } 
        ];
        



        self.tableNameDetails = ko.observableArray([]);

        self.clickTableGetDetails  =  function(data, event) {
            document.querySelector('#SelectSchemaDialog').open();
            $.ajax({
                url: self.DepName()  + "/gettabledetfromschema",
                type: 'POST',
                data: JSON.stringify({
                    dbname : self.currentDB(),
                    schemaList : self.schemaListSelected(),
                }),
                dataType: 'json',
                timeout: sessionStorage.getItem("timeInetrval"),
                context: self,
                            error: function (xhr, textStatus, errorThrown) {
                                if(textStatus == 'timeout' || textStatus == 'error'){
                                    document.querySelector('#SelectSchemaDialog').close();
                                    document.querySelector('#TimeoutInLoad').open();
                                }
                            },
                success: function (data) {
                         self.tableNameDetails([]);
                    for (var i = 0; i < data[0].length; i++) {
                        for (var j = 0; j < data[0][i].length; j++) {
                            console.log(data[0][i])
                        self.tableNameDetails.push({ 'tname': data[0][i][j]['tname'],'cname': data[0][i][j]['cname'] , 'coltype': data[0][i][j]['coltype'], 'width': data[0][i][j]['width'], 'syslength': data[0][i][j]['syslength'], 'NN': data[0][i][j]['NN'] , 'in_primary_key': data[0][i][j]['in_primary_key'], 'default_value': data[0][i][j]['default_value'], 'column_kind': data[0][i][j]['column_kind'], 'remarks': data[0][i][j]['remarks']});
                    }
                }
                    self.tableNameDetails.valueHasMutated();

                document.querySelector('#SelectSchemaDialog').close();
                    return self;
                    
                }

            })
        }

        self.tableNameDetailsDP = new PagingDataProviderView(new ArrayDataProvider(self.tableNameDetails, {keyAttributes: 'tname'}));     

        self.buttonVal = ko.observable(true);
        
        self.valueChangedHandler = (event) => {
            self.buttonVal(false);
        };

        self.TableDetailcolumnArray = [

        {headerText: 'Table Name',
        field: 'tname' }, 
        {headerText: 'Column Name',
        field: 'cname' } ,
       {headerText: 'Column Type',
        field: 'coltype' },
       {headerText: 'Column Width',
        field: 'width' },
        {headerText: 'Scale',
         field: 'syslength' },
         {headerText: 'Nulls',
          field: 'NN' },
          {headerText: 'Primary Key',
           field: 'in_primary_key' },
           {headerText: 'Default Value',
            field: 'default_value' },
            {headerText: 'Remarks',
             field: 'remarks' }    
        ];



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

        self.handleSelectedChanged = function (event) {
            self.gettraildet(false);
            self.selectedTrailFile(self.getDisplayValue(event.detail.value)); // show selected list item elements' ids
          };





        self.CountDataProvider = new ArrayDataProvider(self.TrailCount, {idAttribute: 'id'});


        self.connected = function () {
            getDB();
        }


        }
        getDisplayValue(set) {
            let text;
            const arr = [];
                set.values().forEach((key) => {
                    arr.push(key);
                });
            return arr;
        }
    }

        /*
         * Returns an instance of the ViewModel providing one instance of the ViewModel. If needed,
         * return a constructor for the ViewModel so that the ViewModel is constructed
         * each time the view is displayed.
         */
        return LoadBalanceViewModel;
    }
);