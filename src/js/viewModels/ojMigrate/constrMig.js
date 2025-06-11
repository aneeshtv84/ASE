define([
    'knockout',
    'jquery',
    'appController',"ojs/ojconverter-number","ojs/ojpagingdataproviderview",
    'ojs/ojarraydataprovider', 
    "ojs/ojlistdataproviderview", 
    "ojs/ojkeyset",
    "ojs/ojdataprovider",
    'ojs/ojknockout',
    'ojs/ojinputtext',
    'ojs/ojtable',
    'ojs/ojlabel',
    'ojs/ojformlayout','ojs/ojdialog','ojs/ojprogress-bar' ,"ojs/ojpagingcontrol",
    'ojs/ojselectsingle','ojs/ojselectcombobox', "ojs/ojlistview"],
    function (ko, $,app,ojconverter_number_1, PagingDataProviderView, ArrayDataProvider, ListDataProviderView, ojkeyset_1, ojdataprovider_1) {
        class ConstraintMigrateViewModel {
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
                    for (var i = 0; i < data[0].length; i++) {
                        self.DBDet.push({'value' : data[0][i].dbname, 'label' : data[0][i].dbname});
                    }
                }
            })
        }

        self.DBDetDP = new ArrayDataProvider(self.DBDet, {keyAttributes: 'value'});


        self.tableDetail = ko.observableArray([]);
        self.schemaList = ko.observableArray([]);

        self.dbchangeActionHandler = function (data, event) {
            $.ajax({
                url: self.DepName() + "/getschemaname",
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
                    self.schemaList([]);
                    for (var i = 0; i < data[0].length; i++) {
                        self.schemaList.push({'label': data[0][i], 'value': data[0][i]})
                    }
                   return self;
                }
            })

        };

        self.schemachangeActionHandler = function (data, event) {
            $.ajax({
                url: self.DepName() + "/getKeyConstrants",
                type: 'GET',
                dataType: 'json',
                context: self,
                error: function (e) {
                    console.log(e);
                },
                success: function (data) {               
                    self.tableDetail([]);
                    for (var i=0; i<=data.length; i++) {
                        self.tableDetail.push({'tabname': data[i]});
                    }
                    console.log(self.tableDetail());                    
                    return self;
                }
            })

        };

        self.filter = ko.observable('');
        self.handleValueChanged = () => {
            self.filter(document.getElementById('filter').rawValue);
        };
        self.tableDetailDP = ko.computed(function () {
            let filterCriterion = null;
            if (self.filter() && self.filter() != '') {
                filterCriterion = ojdataprovider_1.FilterFactory.getFilter({
                    filterDef: { text: self.filter() }
                });
            }
            const arrayDataProvider = new ArrayDataProvider(self.tableDetail, { keyAttributes: 'tabname' });
            return new PagingDataProviderView(new ListDataProviderView(arrayDataProvider, { filterCriterion: filterCriterion }));
        }, self);
        // self.tableDetailDP = new PagingDataProviderView(new ArrayDataProvider(self.tableDetail, {keyAttributes: 'tabname'}));

        self.schemaListDP = new ArrayDataProvider(self.schemaList, {keyAttributes: 'value'});

        self.schemaListSelected = ko.observableArray([]);


        self.CountDetailcolumnArray = 
        [
        {headerText: 'Table Name',
        field: 'tabname' }
        ];

        self.selectedItems = ko.observable({
            row: new ojkeyset_1.KeySetImpl(),
            column: new ojkeyset_1.KeySetImpl()
        });
        self.isDisabled = ko.observable(true);
        self.selectionInfo = ko.observable('');
        self.selectedSelectionMode = ko.observable({
            row: 'multiple',
            column: 'none'
        });
        self.selectionModes = [
            { value: { row: 'single', column: 'none' }, label: 'No Exclusion Mode' },
            { value: { row: 'multiple', column: 'none' }, label: 'Exclusion Mode' }
        ];
        self.selectionModeDP = new ArrayDataProvider(this.selectionModes, {
            keyAttributes: 'value'
        });

        self.excludeData = ko.observableArray();
        self.includedData = ko.observableArray();

        self.selectedChangedListener = (event) => {
            self.buttonVal(false);
            let selectionText = '';
            self.constraintDDL('');
            if (event.detail.value.row.isAddAll()) {
                self.isDisabled(false);
                const iterator = event.detail.value.row.deletedValues();
                const row=self.tableDetail();
                for(var i=0;i<row.length;i++) {
                    selectionText = selectionText +  row[i].tabname + ", " ;
                }
                if(event.detail.value.row._keys.size>0){
                    event.detail.value.row._keys.forEach(function (key) {
                        newInclude.push({ tabname: key })
                        selectionText = selectionText.replace(key+",", "");
                    });                    
                }
                const excludeItems = selectionText.split(',').map(item => item.trim()).filter(item => item !== '');
                excludeItems.forEach(item => {
                    newExclude.push({ name: item });
                });            
                selectionText = selectionText.replace(/,\s*$/,"");
                if(self.selectedSelectionMode().row === 'multiple'){
                    self.excludeData(newExclude);
                    self.includedData(newInclude)
                }
            }
            else {
                const row = event.detail.value.row;
                const column = event.detail.value.column;
                const rowKeys = []      
                const newExclude = [];    
                const newInclude = [];   
                const tables=self.tableDetail(); 
                for(var i=0;i<tables.length;i++) {
                    newInclude.push({ tabname: tables[i].tabname }); 
                }  
                if (row.values().size > 0) {
                    row.values().forEach(function (key) {
                        rowKeys.push(key)
                        newExclude.push({ name: key });
                        const index = newInclude.findIndex(obj => obj.tabname === key);
                        if (index > -1) {
                            newInclude.splice(index, 1);
                        }
                        selectionText += selectionText.length === 0 ? key : ', ' + key;
                    });
                    if(self.selectedSelectionMode().row === 'multiple'){
                        self.excludeData(newExclude);
                        self.includedData(newInclude)
                    }
                }
                if (column.values().size > 0) {
                    column.values().forEach(function (key) {
                        selectionText += selectionText.length === 0 ? key : ', ' + key;
                    });
                    selectionText = 'Column Keys: ' + selectionText;
                }
                self.isDisabled(row.values().size === 0 && column.values().size === 0);   
                if(rowKeys.length===1){
                    self.selectionInfo(selectionText)  
                    self.clickTableGetDetails()        
                }               
            }
            self.selectionInfo(selectionText);
        };
        self.clearSelection = () => {
            self.selectedItems({ row: new ojkeyset_1.KeySetImpl(), column: new ojkeyset_1.KeySetImpl() });
        };
        this.selectedSelectionMode.subscribe((newValue) => {
            // Reset selected Items on selection mode change.
            self.selectedItems({ row: new ojkeyset_1.KeySetImpl(), column: new ojkeyset_1.KeySetImpl() });
        });

        self.excludeDataProvider = new ArrayDataProvider(self.excludeData, {
            keyAttributes: 'name'
        });
        
        self.ExcludeTableGetDetails = ()=>{
            document.querySelector('#autoMateExcludeDlg').close();
            self.automateTable(self.includedData())
        }

        self.constraintDDL = ko.observable();

        self.excelBlob = ko.observable();
        self.excelFileName = ko.observable();

        self.clickTableGetDetails  =  function(data, event) {
            document.querySelector('#SelectSchemaDialog').open();
            console.log(self.selectionInfo());            
            if(self.selectionInfo()!=="" && self.currentDB()!==""){
                $.ajax({
                    url: self.DepName()  + "/getKeyConstraintsLines",
                    type: 'POST',
                    data: JSON.stringify({
                        dbname : self.currentDB(),
                        tableName : self.selectionInfo(),
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
                        let cleanLines = data.map(line => line.trim()).filter(line => line.length);
                        self.constraintDDL(cleanLines);
                        self.constraintDDLConvertedText('');
                        document.querySelector('#SelectSchemaDialog').close();
                        return self;
                    }
                })
            }
        }

        self.buttonValAutomate = ko.observable(false)
        
        self.automateModal =  (data, event) => {
            document.querySelector('#autoMateDlg').open();
        }

        self.automateExcludeModal = (data, event) => {
            document.querySelector('#autoMateExcludeDlg').open();
        }

        self.automateClose =  function(data, event) {
            document.querySelector('#autoMateDlg').close();
        }

        self.automateExcludeClose =  function(data, event) {
            document.querySelector('#autoMateExcludeDlg').close();
        }

        self.progressValue = ko.observable(0);
        self.automateTable = (tableList)=>{
            document.querySelector('#autoMateDlg').close();            
            var intervalId = setInterval(fetchAutomateResults, 1000);
            self.progressValue(-1)
            let procNameList = self.tableDetail()
            if(tableList && tableList.length > 0){
                procNameList = tableList
            }
            $.ajax({
                url: self.DepName()  + "/automateTable",
                type: 'POST',
                data: JSON.stringify({
                    sourceDbname : self.currentDB(),
                    targetDbname : self.TGTcurrentPDB(),
                    procNameList : procNameList,
                    targetDep : self.TGTonepDepUrl(),
                    sourceDep : self.DepName(),
                }),
                dataType: 'json',
                timeout: sessionStorage.getItem("timeInetrval"),
                context: self,
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                        document.querySelector('#SelectSchemaViewDialog').close();
                        document.querySelector('#TimeoutInLoad').open();
                    }
                },
                success: function (data) {
                    setTimeout(() => {
                        self.progressValue(100)
                    }, 3000);
                    fetchAutomateResults();
                    clearInterval(intervalId);
                    self.buttonValReport(false)
                }
            })
        }

        self.listFunction = ko.observableArray([]);
        function fetchAutomateResults() {
            $.ajax({
                url: self.DepName()  + "/fetchAutomateTableExcel",
                type: 'POST',
                data: JSON.stringify({
                    sourceDbname : self.currentDB(),
                }),
                dataType: 'json',
                timeout: sessionStorage.getItem("timeInetrval"),
                context: self,
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                        document.querySelector('#SelectSchemaViewDialog').close();
                        document.querySelector('#TimeoutInLoad').open();
                    }
                },
                success: function (data) {
                    self.listFunction([])
                    var csvContent = '';
                    var headers = ['No', 'Function', 'Result'];
                    csvContent += headers.join(',') + '\n';
                    for (var i =0; i<data.length;i++) {
                        if(data[i].Function == self.tableDetail()[i].tabname) {
                            if(data[i].Output == "Created" ||  data[i].Output == "Already Exist") {
                                self.tableDetail()[i].output = 'Success';
                            } else if (data[i].Output == "Error"){
                                self.tableDetail()[i].output = 'Error';
                            } else{
                                self.tableDetail()[i].output = 'Error';
                            }
                        } else {
                            for (var j =0; j<self.tableDetail().length;j++) {
                                if (self.tableDetail()[j].tabname == data[i].Function ) {
                                    if(data[i].Output == "Created" ||  data[i].Output == "Already Exist") {
                                        self.tableDetail()[j].output = 'Success';
                                    } else if (data[i].Output == "Error"){
                                        self.tableDetail()[j].output = 'Error';
                                    }
                                    else{
                                        self.tableDetail()[i].output = 'Error';
                                    }
                                }
                            }
                        }
                        self.tableDetail.valueHasMutated();
                        var rowData = [i+1, data[i].Function,data[i].Output]
                        csvContent += rowData.join(',') + '\n';
                        self.listFunction.push({ 'No': i+1,'Function Name': data[i].Function,'Output':data[i].Output});
                        self.listFunction.valueHasMutated();
                    }
                    var blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                    var fileName = 'DBA_Table_Report'+ '.csv';
                    self.excelBlob(blob);
                    self.excelFileName(fileName);
                    document.querySelector('#SelectSchemaViewDialog').close();
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

   //     self.tableNameDetailsDP = new PagingDataProviderView(new ArrayDataProvider(self.tableNameDetails, {keyAttributes: 'id'}));     
        
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
        
        

        self.excludeButtonVal = ko.observable(true);
        self.buttonVal = ko.observable(true);
        self.valueChangedHandler = (event) => {
            self.buttonVal(false);
        };


               
        self.TgtOnePDepName = ko.observable();
        self.TGTcurrentPDB = ko.observable();

        self.isFormReadonly = ko.observable(false);

       self.SelectTGTDeployment = (event,data) =>{
          if (self.TgtOnePDepName()){
              document.querySelector('#SelectSchemaViewDialog').open();
          self.TGTonepDepUrl('');
          $.ajax({
            url: self.DepName() + "/onepdepurl",
            type: 'POST',
            data: JSON.stringify({
              dep: self.TgtOnePDepName()
          }),
            dataType: 'json',
            timeout: sessionStorage.getItem("timeInetrval"),
              context: self,
              error: function (xhr, textStatus, errorThrown) {
                  if(textStatus == 'timeout' || textStatus == 'error'){
                      document.querySelector('#TimeoutInLoad').open();
                  }
              },
            success: function (data) {
                self.TGTcurrentPDB('');
                self.TGTonepDepUrl(data[0]);
                getTgtDB(data[0]);
                document.querySelector('#SelectSchemaViewDialog').close();
                return self;
            }
        })
          }
    
       };


      self.onepDepList = ko.observableArray([]);

        function getOnepDep() {
            self.onepDepList([]);
            $.ajax({
                url: self.DepName() + "/onepdep",
                type: 'GET',
                dataType: 'json',
                timeout: sessionStorage.getItem("timeInetrval"),
                context: self,
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                        document.querySelector('#TimeoutInLoad').open();
                    }
                },
                success: function (data) {
                    for (var i = 0; i < data[0].length; i++) {
                    self.onepDepList.push({'label' : data[0][i].dep , value :  data[0][i].dep} );
                    }
                    self.onepDepList.valueHasMutated();
                    return self;
                }

            })
        }

        self.onepDepListDP = new ArrayDataProvider(self.onepDepList, {keyAttributes: 'value'});




        self.TgtDBDet = ko.observableArray([]);

        function getTgtDB(depurl) {
           $.ajax({
               url: depurl + "/dbdet",
               type: 'GET',
               dataType: 'json',
               timeout: sessionStorage.getItem("timeInetrval"),
               context: self,
               error: function (xhr, textStatus, errorThrown) {
                   if(textStatus == 'timeout' || textStatus == 'error'){
                       document.querySelector('#TimeoutSup').open();
                   }
               },
               success: function (data) {
                   self.TgtDBDet([]);
                   for (var i = 0; i < data[0].length; i++) {
                       self.TgtDBDet.push({'value' : data[0][i].dbname, 'label' : data[0][i].dbname});
               }

               self.TgtDBDet.valueHasMutated();
               return self;
           }
           })
       }


       self.TgtDBDetDP = new ArrayDataProvider(self.TgtDBDet, { keyAttributes: 'value' });


 self.dbTgtDetList =  ko.observableArray([]);

                self.TGTonepDepUrl = ko.observable();

       self.DBTgtSchema = function (data, event) {
        if(self.TGTcurrentPDB()){
        document.querySelector('#SelectSchemaViewDialog').open();
        self.dbTgtDetList([]);
        $.ajax({
            url: self.TGTonepDepUrl() + "/cdbcheck",
            type: 'POST',
            data: JSON.stringify({
                dbname : self.TGTcurrentPDB()
            }),
            dataType: 'json',
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#SelectSchemaViewDialog').close();
                                document.querySelector('#TimeoutInLoad').open();
                            }
                        },
            success: function (data) {
                self.dbTgtDetList([]);
                for (var i = 0; i < data[3].length; i++) {
                                self.dbTgtDetList.push({ 'dbid': data[3][i].DBID,'dbname' : data[3][i].DBNAME,'pdbname' : data[3][i].PDBNAME,'platform' : data[3][i].PLATFORM_NAME  ,'host' : data[3][i].HOST,'version' : data[3][i].VERSION,'dbedition' : data[3][i].DB_EDITION , 'db_role' : data[3][i].DATABASE_ROLE , 'current_scn' : data[3][i].CURRENT_SCN , 'cdb' : data[3][i].CDB});
                            }
                self.dbTgtDetList.valueHasMutated();
                document.querySelector('#SelectSchemaViewDialog').close();
                return self;
                
            }

        })
    }
    }


    self.dbTgtDetListDP = new ArrayDataProvider(self.dbTgtDetList, {keyAttributes: 'dbid'});    
    self.TgtdbDetcolumnArray = [
        {headerText: 'DB Name', field: 'dbname'},
        {headerText: 'PDB Name', field: 'pdbname'},
        {headerText: 'Platform', field: 'platform'},
        {headerText: 'Host', field: 'host'},
        {headerText: 'Version', field: 'version'} ,
        {headerText: 'DB Edition', field: 'dbedition'} ,
        {headerText: 'DB Role', field: 'db_role'} ,
        {headerText: 'Current SCN', field: 'current_scn'} ,
        {headerText: 'CDB', field: 'cdb'} ,
    ]

    self.constraintDDLConvertedText = ko.observable('');
        
    self.clickConvert = function (data, event) {
        self.constraintDDLConvertedText('');  
        document.querySelector('#SelectSchemaViewDialog').open();
        // const output = self.constraintDDL().map(line => line.replace(/\b\w+\.(dbo\.\w+)/g, '$1'));
        $.ajax({
            url: self.DepName() + "/constraintDDLGenAi",
            data: JSON.stringify({
                constraintDDL : self.constraintDDL()
            }),
            type: 'POST',
            dataType: 'json',
            context: self,
            error: function (e) {
                console.log(e);
            },
            success: function (data) {
                document.querySelector('#SelectSchemaViewDialog').close();
                // const singleLine = data.converted_lines.replace(/[\r\n]+/g, '');
                const updatedLines = data.converted_lines.map(line => {
                    let cleanedLine = line.replace(/\bmy_db\./g, '');

                    cleanedLine = cleanedLine.replace(
                        /\b(ALTER TABLE|REFERENCES)\s+([a-zA-Z0-9_\.]+)/gi,
                        (match, clause, fullTable) => {
                            if (fullTable.includes('.')) return `${clause} ${fullTable}`;
                            return `${clause} dbo.${fullTable}`;
                        }
                    );

                    return cleanedLine;
                });
                const singleLine = updatedLines.join(',').replace(/[\r\n]+/g, '');
                self.constraintDDLConvertedText(singleLine);
                return self;
            }
        })
    };

         self.saveDDLMsg = ko.observable();

         self.SaveDDL = function (data, event) {
            self.saveDDLMsg('');  
            document.querySelector('#SelectSchemaViewDialog').open();
            console.log(self.constraintDDLConvertedText())
            console.log(self.TGTcurrentPDB())
            $.ajax({
                url: self.TGTonepDepUrl() + "/saveConstraints",
                data: JSON.stringify({
                    dbname : self.TGTcurrentPDB(),
                    constraintDDLConvertedText : self.constraintDDLConvertedText()
                }),
                type: 'POST',
                dataType: 'json',
                context: self,
                error: function (e) {
                    //console.log(e);
                },
                success: function (data) {
                    document.querySelector('#SelectSchemaViewDialog').close();
                    document.querySelector('#openDialog').open();
                    self.saveDDLMsg(data.msg);
                    updateExcel(data.msg)
                    return self;
                }
            })
        };

        self.saveOKTable= function (data, event) {
            document.querySelector('#openDialog').close();
        }


        self.connected = function () {
            getDB();
            getOnepDep();
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
        return ConstraintMigrateViewModel;
    }
);