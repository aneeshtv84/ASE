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
    'ojs/ojlabel', 'ojs/ojswitch',
    'ojs/ojformlayout','ojs/ojdialog','ojs/ojprogress-bar' ,"ojs/ojpagingcontrol",
    'ojs/ojselectsingle','ojs/ojselectcombobox', "ojs/ojlistview"],
    function (ko, $,app,ojconverter_number_1, PagingDataProviderView, ArrayDataProvider, ListDataProviderView, ojkeyset_1, ojdataprovider_1) {
        class IndexigrateViewModel {
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

                self.firstSelectedItem = ko.observable();


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
            document.querySelector('#SelectSchemaDialog').open();
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
                    document.querySelector('#SelectSchemaDialog').close();
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
                url: self.DepName() + "/getIndexConstraints",
                type: 'GET',
                dataType: 'json',
                context: self,
                error: function (e) {
                    console.log(e);
                },
                success: function (data) {               
                    self.tableDetail([]);
                    self.buttonValAutomate(false);
                    for (var i=0; i<=data.length; i++) {
                        if(data[i] == undefined || data[i]== "")
                            continue;
                        self.tableDetail.push({'tabname': data[i]});
                    }                  
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
        {headerText: 'Indexes',
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
                
                selectionText = selectionText.replace(/,\s*$/,"");
                if(self.selectedSelectionMode().row === 'multiple'){
                    self.includedData(newInclude)
                }
            }
            else {
                const row = event.detail.value.row;
                const column = event.detail.value.column;
                const rowKeys = []      
                const newInclude = [];   
                const tables=self.tableDetail(); 
                for(var i=0;i<tables.length;i++) {
                    newInclude.push({ tabname: tables[i].tabname }); 
                }  
                if (row.values().size > 0) {
                    row.values().forEach(function (key) {
                        rowKeys.push(key)
                        self.firstSelectedItem({ tabname: key })
                        const index = newInclude.findIndex(obj => obj.tabname === key);
                        if (index > -1) {
                            newInclude.splice(index, 1);
                        }
                        selectionText += selectionText.length === 0 ? key : ', ' + key;
                    });
                    if(self.selectedSelectionMode().row === 'multiple'){
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
        
        self.constraintDDL = ko.observable();

        self.excelBlob = ko.observable();
        self.excelFileName = ko.observable();

        self.clickTableGetDetails  =  function(data, event) {
            document.querySelector('#SelectSchemaDialog').open();
            // console.log(self.selectionInfo());    
            
            if(self.selectionInfo()!=="" && self.currentDB()!==""){                
                $.ajax({
                    url: self.DepName()  + "/getIndexConstraintsLines",
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
                        // console.log(data);
                        let indexBlocks = [];
                        let buffer = [];
                        data.constraintText.forEach(line => {
                            if (/^create\s+unique\s+(clustered|nonclustered)?\s*index/i.test(line.trim())) {
                                if (buffer.length > 0) {
                                    indexBlocks.push(buffer.join('').trim());
                                    buffer = [];
                                }
                            }
                            buffer.push(line);
                        });

                        if (buffer.length > 0) {
                           indexBlocks.push(buffer.join('').trim());
                        }
                        // console.log(indexBlocks)
                        self.constraintDDL(indexBlocks);
                        self.constraintDDLConvertedText('');
                        document.querySelector('#SelectSchemaDialog').close();
                        return self;
                    }
                })
            }
        }

        self.buttonValAutomate = ko.observable(true)
        
        self.automateModal =  (data, event) => {
            document.querySelector('#autoMateDlg').open();
        }

        self.automateClose =  function(data, event) {
            document.querySelector('#autoMateDlg').close();
        }

        self.s3BucketChecked = ko.observable(false);        
        self.s3BucketList = ko.observableArray([]);
        self.s3Bucket = ko.observable("")

        self.getS3BucketList = ()=>{
            self.s3BucketList([]);
            $.ajax({
                url: self.DepName()  + "/getS3BucketLists",
                type: 'GET',
                dataType: 'json',
                timeout: sessionStorage.getItem("timeInetrval"),
                context: self,
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                        console.log(textStatus);                       
                    }
                },
                success: function (data) {
                    let bucketLists = data.buckets                    
                    bucketLists.forEach(element => {
                        self.s3BucketList.push({'value' : element, 'label' : element})
                    });                
                }
            })
        }
        self.s3BucketListDp = new ArrayDataProvider(self.s3BucketList, {keyAttributes: 'value'});

        self.s3BucketChecked.subscribe(function (newValue) {
            if (newValue) {
                self.getS3BucketList();
            }
        });

        self.progressValue = ko.observable(0);
        self.automateConstraints = (tableList)=>{
            document.querySelector('#autoMateDlg').close();            
            var intervalId = setInterval(fetchAutomateResults, 1000);
            self.progressValue(-1)
            let procNameList = self.tableDetail()
            if(tableList && tableList.length > 0){
                procNameList = tableList
            }
            $.ajax({
                url: self.DepName()  + "/automateIndexes",
                type: 'POST',
                data: JSON.stringify({
                    sourceDbname : self.currentDB(),
                    targetDbname : self.TGTcurrentPDB(),
                    procNameList : procNameList,
                    targetDep : self.TGTonepDepUrl(),
                    sourceDep : self.DepName(),
                    s3BucketChecked : self.s3BucketChecked(),
                    s3Bucket : self.s3Bucket(),
                }),
                dataType: 'json',
                timeout: sessionStorage.getItem("timeInetrval"),
                context: self,
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                        document.querySelector('#SelectSchemaViewDialog').close();
                        document.querySelector('#TimeoutInLoad').open();
                        setTimeout(() => {
                            self.progressValue(100)
                        }, 3000);
                        clearInterval(intervalId);
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
                url: self.DepName()  + "/fetchAutomateIndexesExcel",
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
                    var fileName = 'DBA_Index_Report'+ '.csv';
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
                    self.dbTgtDetList.push({ 'dbid': data[3][i].dbid,'dbname' : data[3][i].dbname,'pdbname' : data[3][i].pdbname,'platform' : data[3][i].platform_name  ,'host' : data[3][i].host,'version' : data[3][i].version,'dbedition' : data[3][i].db_edition , 'db_role' : data[3][i].database_role , 'current_scn' : data[3][i].current_scn , 'cdb' : data[3][i].cdb});
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

    self.convertResult = ko.observable('');
    self.fetchConvertResult = ()=> {
        $.ajax({
            url: self.DepName()  + "/readConvertFile",
            type: 'GET',
            dataType: 'json',
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            error: function (xhr, textStatus, errorThrown) {
                console.log(textStatus)
            },
            success: function (data) {
                if (data && data.length !== 0) {
                    document.querySelector('#SelectSchemaViewDialog').close();
                    document.querySelector('#convertResultDialog').open();
                    let formattedText = Array.isArray(data)
                        ? data.join('\n')
                        : data.toString().replace(/\r?\n/g, '\n');
                    self.convertResult(formattedText)

                    setTimeout(function () {
                        const dialogBody = document.getElementById("convertResultDialog");
                        dialogBody.scrollTop = dialogBody.scrollHeight;
                    }, 100);
                }   
                else{
                    document.querySelector('#SelectSchemaViewDialog').open();   
                }
            }
        })
    }

    self.closeConvertResultDialog = ()=>{
        document.querySelector('#convertResultDialog').close();
    } 

    self.constraintDDLConvertedText = ko.observable('');
        
    self.clickConvert = function (data, event) {
        self.constraintDDLConvertedText('');  
        document.querySelector('#SelectSchemaViewDialog').open();
        var intervalId = setInterval(()=>self.fetchConvertResult(), 1000);
        $.ajax({
            url: self.DepName() + "/indexDDLGenAi",
            data: JSON.stringify({
                constraintDDL : self.constraintDDL(),
                s3BucketChecked : self.s3BucketChecked(),
                s3Bucket : self.s3Bucket(),
                indexName : self.selectionInfo(),
                sourceDep : self.DepName(),
            }),
            type: 'POST',
            dataType: 'json',
            context: self,
            error: function (e) {
                console.log(e);
                document.querySelector('#SelectSchemaViewDialog').close();
            },
            success: function (data) {
                let converted_lines = data.converted_lines
                clearInterval(intervalId);
                document.querySelector('#convertResultDialog').close();
                setTimeout(()=>{
                    document.querySelector('#convertResultDialog').close();
                }, 1000)
                let cleanLines = converted_lines.map(line => line.trim()).filter(line => line.length);
                const formatted = cleanLines
                                    .map((line, index) => index < cleanLines.length - 1 ? line + ',' : line)
                                    .join('\n');
                self.constraintDDLConvertedText(formatted);
                return self;
            }
        })
    };

    function updateExcel (data) {
        for (var j =0; j<self.tableDetail().length;j++) {
            if (self.tableDetail()[j].tabname == self.firstSelectedItem().tabname ) {
                if (data == "Created" || data.includes("already used by an existing")) {
                    self.tableDetail()[j].output = "Success";
                    var output = 'Created';
                    if(data.includes("already used")) {
                        var output = 'Already Exist';
                    }
                }
                else { 
                    self.tableDetail()[j].output = 'Error';
                    var output = 'Error';
                }
            } 
        }
        self.tableDetail.valueHasMutated();
        // console.log(self.firstSelectedItem().tabname);        
        $.ajax({
            url: self.DepName()  + "/updateExcelIndexes",
            data: JSON.stringify({
                functionName : self.firstSelectedItem().tabname,
                output : output,
                sourceDbname : self.currentDB(),
                schemaName : self.schemaListSelected()[0],
            }),
            type: 'POST',
            contentType: 'application/json', 
            dataType: 'json',
            context: self,
            error: function (e) {
                ////(e);
            },
            success: function (data) {
                return self;
            }
        })
    }

    self.saveDDLMsg = ko.observable();

        self.SaveDDL = function (data, event) {
            self.saveDDLMsg('');  
            document.querySelector('#SelectSchemaViewDialog').open();
            // console.log(self.constraintDDLConvertedText())
            // console.log(self.TGTcurrentPDB())
            const indexArray = self.constraintDDLConvertedText()
                                    .split(/(?=CREATE UNIQUE INDEX)/i)
                                    .map(item => item.trim().replace(/,\s*$/, ''))
                                    .filter(block => block);
            // console.log(indexArray);
            $.ajax({
                url: self.TGTonepDepUrl() + "/saveIndexes",
                data: JSON.stringify({
                    dbname : self.TGTcurrentPDB(),
                    constraintDDLConvertedText : indexArray
                }),
                type: 'POST',
                dataType: 'json',
                context: self,
                error: function (e) {
                    //console.log(e);
                },
                success: function (data) {
                    // console.log(data);                    
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
        return IndexigrateViewModel;
    }
);