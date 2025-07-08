define([
    'knockout',
    'jquery',
    'appController',"ojs/ojconverter-number","ojs/ojpagingdataproviderview",
    'ojs/ojarraydataprovider', "ojs/ojlistdataproviderview", "ojs/ojdataprovider",
    'ojs/ojknockout-keyset',
    'ojs/ojknockout',
    'ojs/ojfilepicker', 
    'ojs/ojinputtext',
    'ojs/ojtable',
    'ojs/ojradioset',
    'ojs/ojlabel',
    'ojs/ojlistview', 'ojs/ojlistitemlayout','ojs/ojcheckboxset','ojs/ojformlayout','ojs/ojdialog','ojs/ojprogress-bar' ,"ojs/ojchart","ojs/ojpagingcontrol",'ojs/ojselectsingle','ojs/ojselectcombobox'],
        function (ko, $,app,ojconverter_number_1, PagingDataProviderView,ArrayDataProvider , ListDataProviderView, ojdataprovider_1, keySet) {

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
                self.errorTableNameDetails = ko.observableArray([]);
                
                self.buttonValReport = ko.observable(true)

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
                    // console.log(data)
                    for (var i = 0; i < data[0].length; i++) {
                        self.DBDet.push({'value' : data[0][i].dbname, 'label' : data[0][i].dbname});
                }
                // console.log(self.DBDet())
            }
            })
        }

        self.DBDetDP = new ArrayDataProvider(self.DBDet, {keyAttributes: 'value'});


        self.tableDetail = ko.observableArray([]);
        self.schemaList = ko.observableArray([]);

        self.clickGetDet = function (data, event) {
            console.log(self.DepName() )
            $.ajax({
                url: self.DepName() + "/gettablename",
                data: JSON.stringify({
                    dbname: self.currentDB()
                }),
                type: 'POST',
                dataType: 'json',
                context: self,
                error: function (e) {
                    console.log(e);
                },
                success: function (data) {
                    console.log(data)
                    self.tableDetail([]);
                 for (var key in data[0]) {
                     for (var newkey in data[0][key]){
                        //  console.log(newkey)
                        self.tableDetail.push({'tabname': key,'count': data[0][key][newkey] ,'creator': newkey});
                     }
                    }
                    // console.log(self.tableDetail())
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

        self.excelBlob = ko.observable();
        self.excelFileName = ko.observable();

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

                    var csvContent = '';
                    var headers = ['Table Name', 'Column Name', 'Column Type', 'Column Width', 'Scale', 'Nulls', 'Primary Key', 'Default Value', 'Remarks'];
                    csvContent += headers.join(',') + '\n';
                    self.tableNameDetails([]);
                    self.errorTableNameDetails([]);
                    for (var i = 0; i < data[0].length; i++) {
                        for (var j = 0; j < data[0][i].length; j++) {
                            var rowData = [data[0][i][j]['tname'],data[0][i][j]['cname'] ,data[0][i][j]['coltype'],data[0][i][j]['width'], data[0][i][j]['scale'],data[0][i][j]['NN'] , data[0][i][j]['in_primary_key'],data[0][i][j]['default_value'],data[0][i][j]['remarks']]
                            csvContent += rowData.join(',') + '\n';
                            self.tableNameDetails.push({ 'id': data[0][i][j]['tname']+j,'tname': data[0][i][j]['tname'],'cname': data[0][i][j]['cname'] , 'coltype': data[0][i][j]['coltype'], 'width': data[0][i][j]['width'], 'syslength': data[0][i][j]['scale'], 'NN': data[0][i][j]['NN'] , 'in_primary_key': data[0][i][j]['in_primary_key'], 'default_value': data[0][i][j]['default_value'], 'column_kind': data[0][i][j]['column_kind'], 'remarks': data[0][i][j]['remarks']});
                        }
                        console.log(self.tableNameDetails())
                        var blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                        var fileName = 'Table_Report'+ '.csv';
                        self.excelBlob(blob);
                        self.excelFileName(fileName);
                    }
                    for (var i = 0; i < data[1].length; i++) {
                        for (var j = 0; j < data[1][i].length; j++) {
                            self.errorTableNameDetails.push({ 'id' : i ,'tname': data[1][i][j]['tname'],'cname': data[1][i][j]['cname'] , 'coltype': data[1][i][j]['coltype'], 'width': data[1][i][j]['width'], 'syslength': data[1][i][j]['scale'], 'NN': data[1][i][j]['NN'] , 'in_primary_key': data[1][i][j]['in_primary_key'], 'default_value': data[1][i][j]['default_value'], 'column_kind': data[1][i][j]['column_kind'], 'remarks': data[1][i][j]['remarks']});
                        }
                    }
                    self.buttonValReport(false)
                    self.tableNameDetails.valueHasMutated();
                    self.errorTableNameDetails.valueHasMutated();
                    document.querySelector('#SelectSchemaDialog').close();
                    document.querySelector('#viewTableModalDlg').open();
                    return self;
                }
            })
        }

        self.downloadTableReport = ()=>{
            if(self.excelBlob() != undefined && self.excelFileName() != undefined){
                if (window.navigator && window.navigator.msSaveOrOpenBlob) {
                    window.navigator.msSaveOrOpenBlob(self.excelBlob(), self.excelFileName());
                } else {
                    var link = document.createElement('a');
                    link.href = window.URL.createObjectURL(self.excelBlob());
                    link.download = self.excelFileName();
                    link.style.display = 'none';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                }
            }
        }

        self.tableNameDetailsDP = new PagingDataProviderView(new ArrayDataProvider(self.tableNameDetails, {keyAttributes: 'id'}));     
        self.filter = ko.observable('');
        // self.tableNameDetailsDP = ko.computed(function () {
        //     let filterCriterion = null;
        //     if (self.filter() && self.filter() != '') {
        //         filterCriterion = ojdataprovider_1.FilterFactory.getFilter({
        //             filterDef: { text: self.filter() }
        //         });
        //     }
        
        //     const arrayDataProvider = new ArrayDataProvider(self.tableNameDetails, { keyAttributes: 'tname' });
        //     return new PagingDataProviderView(new ListDataProviderView(arrayDataProvider, { filterCriterion: filterCriterion }));
        // });

        self.handleValueChanged = () => {
            self.filter(document.getElementById('filter').rawValue);
        };
        
        self.errorTableNameDetailsDP = new PagingDataProviderView(new ArrayDataProvider(self.errorTableNameDetails, {keyAttributes: 'id'}));     
        
        self.reportClose =  function(data, event) {
            document.querySelector('#viewTableModalDlg').close();
        }

        self.viewReportModal =  function(data, event) {
            document.querySelector('#viewTableModalDlg').open();
        }

        self.downloadReport = function () {
            const tableId = 'dbDetListtable';  // Replace with the specific table ID
        
            const data = [];
            const table = document.getElementById(tableId);
        
            // Capture headers
            const headers = Array.from(table.querySelectorAll('thead th')).map(header => header.textContent);
            data.push(headers);
        
            // Modify the table header style here
            const headerRow = table.querySelector('thead tr');
            headerRow.style.fontWeight = 'bold';
            headerRow.style.color = 'blue';
        
            const rows = table.querySelectorAll('tr');
        
            rows.forEach(row => {
                const rowData = [];
                const cells = row.querySelectorAll('td');
        
                cells.forEach(cell => {
                    rowData.push(cell.textContent);
                });
        
                data.push(rowData);
            });
        
            function convertToText(data) {
                const text = data.map(row => row.join('\t|')).join('\n');
                return text;
            }
        
            const textData = convertToText(data);
        
            const blob = new Blob([textData], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
        
            const a = document.createElement('a');
            a.href = url;
            a.download = self.currentDB() + '.txt'; // Change the file extension to .txt
        
            a.click();
            URL.revokeObjectURL(url);
        };
        
        

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

        self.DepType = ko.observable("");
        self.connected = function () {
            if (sessionStorage.getItem("userName")==null) {
                oj.Router.rootInstance.go('signin');
            }
            else{
                app.onAppSuccess();
                var DepType = sessionStorage.getItem("Dep_Type");
                if(DepType == 'sybase'){
                    self.DepType('Sybase');
                }
                else if (DepType == 'bda'){
                    self.DepType('BigData Targets');
                }                      
                getDB();
            }
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