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
    'ojs/ojlabel', 'ojs/ojswitch',
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
                self.listFunction = ko.observableArray([]);
                self.buttonValAutomate = ko.observable(true)
                self.buttonValReport = ko.observable(true)
                self.gettraildet = ko.observable(true);

                

                self.DBDet = ko.observableArray([]);
                self.currentDB = ko.observable();

                self.TgtOnePDepName = ko.observable();

                self.TGTcurrentPDB = ko.observable();

                self.isFormReadonly = ko.observable(false);

                self.TGTonepDepUrl = ko.observable();
                self.progressValue = ko.observable(0);

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


        self.viewDetail = ko.observableArray([]);
        self.schemaList = ko.observableArray([]);

        self.clickViewGetDet = function (data, event) {
            document.querySelector('#SelectSchemaViewDialog').open();
            $.ajax({
                url: self.DepName() + "/getviewname",
                data: JSON.stringify({
                    dbname: self.currentDB()
                }),
                type: 'POST',
                dataType: 'json',
                context: self,
                error: function (e) {
                    document.querySelector('#SelectSchemaViewDialog').close();
                },
                success: function (data) {
                    document.querySelector('#SelectSchemaViewDialog').close();
                    console.log(data)
                    self.viewDetail([]);
                    for (var i = 0; i < data.views.length; i++) {
                         self.viewDetail.push({'owner': data.views[i].vcreator,'viewname':   data.views[i].viewtext});
                     }
        
                    // console.log(self.viewDetail())
                    self.schemaList([]);
                    for (var i = 0; i < data.schemas.length; i++) {
                        self.schemaList.push({'label': data.schemas[i], 'value': data.schemas[i]})
                    }
                   return self;
                }
            })

        };


        self.viewDetailDP = new PagingDataProviderView(new ArrayDataProvider(self.viewDetail, {keyAttributes: 'tabname'}));

        self.schemaListDP = new ArrayDataProvider(self.schemaList, {keyAttributes: 'value'});

        self.schemaListSelected = ko.observableArray([]);


        self.CountDetailcolumnArray = 
        [
            {headerText: 'Creator',
            field: 'owner' } ,
        {headerText: 'View Name',
        field: 'viewname' }
        ];
        



        self.viewNameDet = ko.observableArray([]);

        self.clickViewGetDetails  =  function(data, event) {
            document.querySelector('#SelectSchemaViewDialog').open();
            $.ajax({
                url: self.DepName()  + "/getviewnamefromschema",
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
                        document.querySelector('#SelectSchemaViewDialog').close();
                        document.querySelector('#TimeoutInLoad').open();
                    }
                },
                success: function (data) {
                    console.log(data)
                    self.viewNameDet([]);
                    for (var i = 0; i < data.length; i++) {
                        self.viewNameDet.push({ 'vname': data[i].owner, 'output': 'none'});
                    }
                    console.log(self.viewNameDet())
                    document.querySelector('#SelectSchemaViewDialog').close();
                    self.viewNameDet.valueHasMutated();
                    self.buttonValAutomate(false)
                    fetchAutomateResults();
                    return self;
                    
                }

            })
        }

        self.viewNameDetDP = new PagingDataProviderView(new ArrayDataProvider(self.viewNameDet, {keyAttributes: 'vname'}));
        
        self.downloadDBAReport = ()=>{
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
        
            function convertToCSV(data) {
                const csv = data.map(row => row.join(',')).join('\n');
                return csv;
            }
        
            const csvData = convertToCSV(data);
        
            const blob = new Blob([csvData], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
        
            const a = document.createElement('a');
            a.href = url;
            a.download = self.currentDB() + '.csv';
        
            a.click();
            URL.revokeObjectURL(url);
        };

        self.buttonVal = ko.observable(true);
        
        self.valueChangedHandler = (event) => {
            self.buttonVal(false);
        };

        self.reportClose =  function(data, event) {
            document.querySelector('#viewReportModalDlg').close();
        }

        self.viewReportModal =  function(data, event) {
            document.querySelector('#viewReportModalDlg').open();
        }

        self.automateClose =  function(data, event) {
            document.querySelector('#autoMateDlg').close();
        }

        self.automateModal =  function(data, event) {
            document.querySelector('#autoMateDlg').open();
        }

        function updateExcel (data) {
            console.log(data)
            for (var j =0; j<self.viewNameDet().length;j++) {
                if (self.viewNameDet()[j].vname == self.firstSelectedItem().data.vname ) {
                    if (data == "Created" || data.includes("already used")) {
                        self.viewNameDet()[j].output = "Success";
                        var output = 'Created';
                        if(data.includes("already used")) {
                            var output = 'Already Exist';
                        }
                    }
                    else { 
                        self.viewNameDet()[j].output = 'Error';
                        var output = 'Error';
                    }
                } 
            }
            self.viewNameDet.valueHasMutated();
            $.ajax({
                url: self.DepName()  + "/updateExcelView",
                data: JSON.stringify({
                    functionName : self.firstSelectedItem().data.vname,
                    output : output,
                    sourceDbname : self.currentDB(),
                    schemaName : self.schemaListSelected()[0],
                }),
                type: 'POST',
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

        self.excelBlob = ko.observable();
        self.excelFileName = ko.observable();

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
        
        function fetchAutomateResults() {
            $.ajax({
                url: self.DepName()  + "/fetchAutomateViewExcel",
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
                        if(data[i].Function == self.viewNameDet()[i].vname) {
                            console.log(data[i].Output)
                            if(data[i].Output == "Created" ||  data[i].Output == "Already Exist") {
                                self.viewNameDet()[i].output = 'Success';
                            } else if (data[i].Output == "Error"){
                                self.viewNameDet()[i].output = 'Error';
                            } else{
                                self.viewNameDet()[i].output = 'Error';
                            }
                        } else {
                            for (var j =0; j<self.viewNameDet().length;j++) {
                                if (self.viewNameDet()[j].vname == data[i].Function ) {
                                    if(data[i].Output == "Created" ||  data[i].Output == "Already Exist") {
                                        self.viewNameDet()[j].output = 'Success';
                                    } else if (data[i].Output == "Error"){
                                        self.viewNameDet()[j].output = 'Error';
                                    }
                                    else{
                                        self.viewNameDet()[i].output = 'Error';
                                    }
                                }
                            }
                        }
                        self.viewNameDet.valueHasMutated();
                        var rowData = [i+1, data[i].Function,data[i].Output]
                        csvContent += rowData.join(',') + '\n';
                        self.listFunction.push({ 'No': i+1,'Funcation Name': data[i].Function,'Output':data[i].Output});
                        self.listFunction.valueHasMutated();
                    }
                    var blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                    var fileName = 'DBA_View_Report'+ '.csv';
                    self.excelBlob(blob);
                    self.excelFileName(fileName);
                    document.querySelector('#SelectSchemaViewDialog').close();
                }
            })
        }

        self.automateGetDetails  =  function(data, event) {
            document.querySelector('#autoMateDlg').close();            
            var intervalId = setInterval(fetchAutomateResults, 1000);
            self.progressValue(-1)
            console.log(self.viewNameDet());
            
            $.ajax({
                url: self.DepName()  + "/automateOracleView",
                type: 'POST',
                data: JSON.stringify({
                    sourceDep : self.DepName(),
                    sourceDbname : self.currentDB(),
                    targetDbname : self.TGTcurrentPDB(),
                    procNameList : self.viewNameDet(),
                    targetDep : self.TGTonepDepUrl(),
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
                                }
                            },
                success: function (data) {
                   console.log("out====") 
                   console.log(data)
                   setTimeout(() => {
                        self.progressValue(100)
                   }, 3000);
                   fetchAutomateResults();
                   clearInterval(intervalId);
                   self.buttonValReport(false)
                }
            })
        }

        self.functionColumnArray = [
            {headerText: 'No',
                    field: 'No'},
                    {headerText: 'Funcation Name',
                    field: 'Funcation Name'},
                    {headerText: 'Output',
                    field: 'Output'}
        ]
        self.listFunctionDP = new PagingDataProviderView(new ArrayDataProvider(self.listFunction, {keyAttributes: 'dbid'}));

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

     
        self.viewText = ko.observable();

        self.getViewText  =  function(data, event) {
            console.log(self.getDisplayValue(self.selectedView())[0])
            console.log(self.firstSelectedItem())
            document.querySelector('#SelectSchemaViewDialog').open();
            $.ajax({
                url: self.DepName()  + "/getviewtext",
                type: 'POST',
                data: JSON.stringify({
                    dbname : self.currentDB(),
                    viewName : self.getDisplayValue(self.selectedView())[0],
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
                    self.viewText('');
                    self.procConvertedText('');
                    self.viewText(data.viewText);
                    document.querySelector('#SelectSchemaViewDialog').close();
                    return self;                    
                }

            })
        }


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
               console.log( self.TgtDBDet())
               return self;
           }
           })
       }


       self.TgtDBDetDP = new ArrayDataProvider(self.TgtDBDet, { keyAttributes: 'value' });

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

       self.dbTgtDetList =  ko.observableArray([]);


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
                // self.dbTgtDetList.push({ 'DBNAME': data[1].DBNAME,'ProductName' : data[1].ProductName,'ProductVersion' : data[1].ProductVersion, 'platform': data[1].platform ,'OSVer' : data[1].OSVer });
                self.dbTgtDetList.valueHasMutated();
                document.querySelector('#SelectSchemaViewDialog').close();
                console.log(self.dbTgtDetList())
                return self;
                
            }

        })
    }
    }

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


           
    self.dbTgtDetListDP = new ArrayDataProvider(self.dbTgtDetList, {keyAttributes: 'DBNAME'});    

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

    self.convertIntervalId = null;

    self.closeConvertResultDialog = ()=>{
        document.querySelector('#convertResultDialog').close();
    } 

    self.cancelConvertResultDialog = ()=>{
        document.querySelector('#convertResultDialog').close();
        if (self.convertIntervalId) {
            clearInterval(self.convertIntervalId);
            self.convertIntervalId = null;
        }
    } 

    self.procConvertedText = ko.observable('');
        
    self.clickConvert = function (data, event) {
        self.procConvertedText('');  
        document.querySelector('#SelectSchemaViewDialog').open();
        const viewProcString = self.viewText().join(' ')
        self.convertIntervalId = setInterval(()=>self.fetchConvertResult(), 1000);
        document.getElementById("log-progressBar").style.display = "block"
        $.ajax({
            // url: self.TGTonepDepUrl() + "/convertViewProc",
            url: self.DepName() + "/viewDDLGenAi",
            data: JSON.stringify({
                dbName : self.TGTcurrentPDB(),
                viewProc : viewProcString,
                s3BucketChecked : self.s3BucketChecked(),
                s3Bucket : self.s3Bucket(),
                viewName : self.getDisplayValue(self.selectedView())[0],
                sourceDep : self.DepName(),
            }),
            type: 'POST',
            dataType: 'json',
            context: self,
            error: function (e) {
                console.log(e);
            },
            success: function (data) {
                clearInterval(self.convertIntervalId);
                self.convertIntervalId = null;
                document.querySelector('#convertResultDialog').close();
                setTimeout(()=>{
                    document.querySelector('#convertResultDialog').close();
                }, 1000)
                document.getElementById("log-progressBar").style.display = "none"
                // const singleLine = data.converted_lines.replace(/[\r\n]+/g, '');
                self.procConvertedText(data.converted_lines);
                return self;
            }
        })
    };

    self.clickRetryConvert = function (data, event) {
        document.querySelector('#openDialog').close();
        self.procConvertedText('');  
        document.querySelector('#SelectSchemaViewDialog').open();
        $.ajax({
            url: self.TGTonepDepUrl() + "/pgRetryConvert",
            data: JSON.stringify({
                dbName : self.TGTcurrentPDB(),
                viewProc : self.viewText()[0]
            }),
            type: 'POST',
            dataType: 'json',
            context: self,
            error: function (e) {
                //console.log(e);
            },
            success: function (data) {
                document.querySelector('#SelectSchemaViewDialog').close();
                self.procConvertedText(data[0]);
                //console.log(self);
                return self;
            }
        })
    };




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
         

         self.saveViewMsg = ko.observable();

         self.pgSaveView = function (data, event) {
            self.saveViewMsg('');  
            document.querySelector('#SelectSchemaViewDialog').open();
            $.ajax({
                url: self.TGTonepDepUrl() + "/pgCreateView",
                data: JSON.stringify({
                    dbName : self.TGTcurrentPDB(),
                    viewText : self.procConvertedText()
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
                    self.saveViewMsg(data.msg);
                    updateExcel(data.msg)
                    return self;
                }
            })
        };
        self.trailfileDP = new ArrayDataProvider(self.trailFiles, {idAttribute: 'trail'});
        self.processDP = new ArrayDataProvider(self.ProcessName, {keyAttributes: 'value'});


        self.saveOKView = function (data, event) {
            document.querySelector('#openDialog').close();
        }

        self.clickUpload = function (data, event) {
            console.log(self.procConvertedText())
            document.querySelector('#openDialog').close();
            document.querySelector('#SelectSchemaProcessDialog').open();
            console.log(self.getDisplayValue(self.selectedView())[0])
            $.ajax({
                url: self.TGTonepDepUrl() + "/clickUploadFile1",
                data: JSON.stringify({
                    viewProc : self.procConvertedText(),
                    procName : self.getDisplayValue(self.selectedView())[0],
                    objectType : 'View'
                }),
                type: 'POST',
                dataType: 'json',
                context: self,
                error: function (e) {
                    //console.log(e);
                },
                success: function (data) {
                    console.log(data)
                    document.querySelector('#SelectSchemaProcessDialog').close();
                    return self;
                }
            })
        };

        self.selectedView = new keySet.ObservableKeySet(); // observable bound to selection option to monitor current selections
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
        return LoadBalanceViewModel;
    }
);