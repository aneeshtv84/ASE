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
                self.listFunction = ko.observableArray([]);
                self.CancelBehaviorOpt = ko.observable('icon');

                self.gettraildet = ko.observable(true);
                self.progressValue = ko.observable(0);
                
                self.buttonValAutomate = ko.observable(true)
                self.buttonValReport = ko.observable(true)

                self.DBDet = ko.observableArray([]);
                self.currentDB = ko.observable();

                self.TgtOnePDepName = ko.observable();

                self.TGTcurrentPDB = ko.observable();

                self.isFormReadonly = ko.observable(false);

                self.TGTonepDepUrl = ko.observable();
                self.readLog = ko.observable('yes');
                self.reportFileContent = ko.observableArray([])

        function getDB() {
            self.DBDet([]);
            $.ajax({
                url: self.DepName() + "/dbdet",
                type: 'GET',
                dataType: 'json',
                context: self,
                error: function (e) {
                    ////(e);
                },
                success: function (data) {
                    //(data)
                    for (var i = 0; i < data[0].length; i++) {
                        self.DBDet.push({'value' : data[0][i].dbname, 'label' : data[0][i].dbname});
                }
                // //(self.DBDet())
            }
            })
        }

        self.DBDetDP = new ArrayDataProvider(self.DBDet, {keyAttributes: 'value'});


        self.viewDetail = ko.observableArray([]);
        self.schemaList = ko.observableArray([]);

        self.clickViewGetDet = function (data, event) {
            $.ajax({
                url: self.DepName() + "/getprocname",
                data: JSON.stringify({
                    dbname: self.currentDB()
                }),
                type: 'POST',
                dataType: 'json',
                context: self,
                error: function (e) {
                    ////(e);
                },
                success: function (data) {
                    //(data[0])
                    console.log(data)
                    self.viewDetail([]);
                    for (var i = 0; i < data.proc.length; i++) {
                         self.viewDetail.push({'owner': data.proc[i].owner,'procname':   data.proc[i].procName});
                     }
        
                    // //(self.viewDetail())
                    self.schemaList([]);
                    for (var i = 0; i < data.schemas.length; i++) {
                        self.schemaList.push({'label': data.schemas[i], 'value': data.schemas[i], 'output':'red'})
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
        {headerText: 'Procedure Name',
        field: 'procname' }
        ];
        



        self.viewNameDet = ko.observableArray([]);

        self.clickViewGetDetails  =  function(data, event) {
            document.querySelector('#SelectSchemaProcessDialog').open();
            $.ajax({
                url: self.DepName()  + "/getprocnamefromschema",
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
                            document.querySelector('#SelectSchemaProcessDialog').close();
                            document.querySelector('#TimeoutInLoad').open();
                        }
                    },
                success: function (data) {
                    // console.log(data[0])
                    self.viewNameDet([]);
                    for (var i = 0; i < data[0].length; i++) {
                        self.viewNameDet.push({ 'vname': data[0][i], 'output': 'none'});
                        // for (var j = 0; j < data[0][i].length; j++) {
                        // self.viewNameDet.push({ 'vname': data[0][i][j][0], 'output': 'none'});
                        // }
                    }
                    // fetchAutomateResults();
                    self.viewNameDet.valueHasMutated();
                    // (self.viewNameDet())
                    document.querySelector('#SelectSchemaProcessDialog').close();
                 //   self.buttonValAutomate(false)
                    return self;
                    
                }

            })
        }

        self.reportAction = () => {
            console.log(self.TGTonepDepUrl())
            self.reportFileContent([])
            $.ajax({
              url: self.TGTonepDepUrl() + "/readProcLog",
              type: 'POST',
              data: JSON.stringify({
                procName : self.firstSelectedItem().data.vname
              }),
              timeout: sessionStorage.getItem("timeInetrval"),
              error: function (xhr, textStatus, errorThrown) {
              
              },
              success: function (data) {
                for (var i = 0; i < data[0].length; i++) {
                  self.reportFileContent.push(data[0][i]);
                }
                document.querySelector('#viewLogDlg').open();
              return self;
              }
            })
          };
    
    
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
        

    self.viewReportModal =  function(data, event) {
        document.querySelector('#viewReportModalDlg').open();
    }

    self.reportClose =  function(data, event) {
        document.querySelector('#viewReportModalDlg').close();
    }

    self.reportLogClose =  function(data, event) {
        document.querySelector('#viewLogDlg').close();
    }

    self.automateModal =  function(data, event) {
        document.querySelector('#autoMateDlg').open();
    }

    self.automateClose =  function(data, event) {
        document.querySelector('#autoMateDlg').close();
        // fetchAutomateResults();
    }

    function updateExcel (data) {
        for (var j =0; j<self.viewNameDet().length;j++) {
            if (self.viewNameDet()[j].vname == self.firstSelectedItem().data.vname ) {
                if (data == "Created Succesfully" || data.includes("already exists")) {
                    self.viewNameDet()[j].output = "Success";
                    var output = 'Created';
                    if(data.includes("already exists")) {
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
            url: self.DepName()  + "/updateExcel",
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

    function fetchAutomateResults() {
        $.ajax({
            url: self.DepName()  + "/fetchAutomateExcel",
            type: 'POST',
            data: JSON.stringify({
                sourceDbname : self.currentDB(),
                schemaName : self.schemaListSelected()[0],
            }),
            dataType: 'json',
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#SelectSchemaProcessDialog').close();
                                // document.querySelector('#TimeoutInLoad').open();
                            }
                        },
            success: function (data) {
                self.listFunction([])
              // console.log("excel====") 
            //   console.log(data)
               var csvContent = '';
                var headers = ['No', 'Function', 'Result'];
                csvContent += headers.join(',') + '\n';
               for (var i =0; i<data.length;i++) {
                if(data[i].Function == self.viewNameDet()[i].vname) {
                    if(data[i].Output == "Created" ||  data[i].Output == "Already Exist") {
                        self.viewNameDet()[i].output = 'Success';
                    } else if (data[i].Output == "Error"){
                        self.viewNameDet()[i].output = 'Error';
                    }  else if (data[i].Output == "Not Loaded"){
                        self.viewNameDet()[i].output = 'Not Loaded';
                    }
                } else {
                    for (var j =0; j<self.viewNameDet().length;j++) {
                        if (self.viewNameDet()[j].vname =data[i].Function ) {
                            if(data[i].Output == "Created" ||  data[i].Output == "Already Exist") {
                                self.viewNameDet()[j].output = 'Success';
                            } else if (data[i].Output == "Error"){
                                self.viewNameDet()[j].output = 'Error';
                            }  else if (data[i].Output == "Not Loaded"){
                                self.viewNameDet()[i].output = 'Not Loaded';
                            }
                        }
                    }
                }
                self.viewNameDet.valueHasMutated();
                var rowData = [i+1, data[i].Function,data[i].Output]
                csvContent += rowData.join(',') + '\n';
                self.listFunction.push({'No': i+1, 'Funcation Name': data[i].Function,'Output':data[i].Output});
                self.listFunction.valueHasMutated();
               }
               var blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
               var fileName = 'DBA_Report'+ '.csv';
               self.excelBlob(blob);
                self.excelFileName(fileName);
                self.buttonValAutomate(false)
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


    self.automateGetDetails  =  function(data, event) {
    //    document.querySelector('#autoMateDlg').close();
        self.progressValue(-1)
        

        // let viewNameLength = self.viewNameDet().length;
        // var intervalTime = 1000;

        // switch (true) {
        // case viewNameLength >= 1000:
        //     intervalTime = 3000;
        //     break;

        // case viewNameLength >= 2000:
        //     intervalTime = 5000;;
        //     break;

        // case viewNameLength <= 3000:
        //     intervalTime = 7000;
        //     break;

        // default:
        //     intervalTime = 9000;;
        // }

        // var intervalId = setInterval(fetchAutomateResults, intervalTime);

        var intervalId = setInterval(fetchAutomateResults, 1000);

        $.ajax({
            url: self.DepName()  + "/automateProcess",
            type: 'POST',
            data: JSON.stringify({
                sourceDbname : self.currentDB(),
                targetDbname : self.TGTcurrentPDB(),
                procNameList : self.viewNameDet(),
                targetDep : self.TGTonepDepUrl(),
                schemaName : self.schemaListSelected()[0],
            }),
            dataType: 'json',
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#SelectSchemaProcessDialog').close();
                                document.querySelector('#TimeoutInLoad').open();
                            }
                        },
            success: function (data) {
               console.log("out====") 
            //    console.log(data)
               fetchAutomateResults();
               clearInterval(intervalId);
               setTimeout(() => {
                self.progressValue(100)
               }, 3000);
               
               self.buttonValReport(false)
            }
        })
    }

        
        
        self.viewNameDetDP = new PagingDataProviderView(new ArrayDataProvider(self.viewNameDet, {keyAttributes: 'vname'}));

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

     
        self.viewText = ko.observable();

        self.getViewText  =  function(data, event) {
            console.log(self.getDisplayValue(self.selectedView())[0])
            self.procConvertedText('');
            // document.querySelector('#SelectSchemaProcessDialog').open();
            $.ajax({
                url: self.DepName()  + "/getproctext",
                type: 'POST',
                data: JSON.stringify({
                    dbname : self.currentDB(),
                    procName : self.getDisplayValue(self.selectedView())[0],
                }),
                dataType: 'json',
                timeout: sessionStorage.getItem("timeInetrval"),
                context: self,
                            error: function (xhr, textStatus, errorThrown) {
                                if(textStatus == 'timeout' || textStatus == 'error'){
                                    document.querySelector('#SelectSchemaProcessDialog').close();
                                    document.querySelector('#TimeoutInLoad').open();
                                }
                            },
                success: function (data) {
                    // console.log(data)
                         self.viewText('');
                         self.viewText(data[0]);
                // document.querySelector('#SelectSchemaProcessDialog').close();
                    return data;
                    
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
            //    //( self.TgtDBDet())
               return self;
           }
           })
       }


       self.TgtDBDetDP = new ArrayDataProvider(self.TgtDBDet, { keyAttributes: 'value' });

       self.SelectTGTDeployment = (event,data) =>{
          if (self.TgtOnePDepName()){
            //   document.querySelector('#SelectSchemaProcessDialog').open();
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
                document.querySelector('#SelectSchemaProcessDialog').close();
                return self;
            }
        })
          }
    
       };

       self.dbTgtDetList =  ko.observableArray([]);


       self.DBTgtSchema = function (data, event) {
        if(self.TGTcurrentPDB()){
        document.querySelector('#SelectSchemaProcessDialog').open();
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
                    document.querySelector('#SelectSchemaProcessDialog').close();
                    document.querySelector('#TimeoutInLoad').open();
                }
            },
            success: function (data) {
                self.dbTgtDetList.push({ 'DBNAME': data[1].DBNAME,'ProductName' : data[1].ProductName,'ProductVersion' : data[1].ProductVersion, 'platform': data[1].platform ,'OSVer' : data[1].OSVer });
                self.dbTgtDetList.valueHasMutated();
                document.querySelector('#SelectSchemaProcessDialog').close();
                self.buttonValAutomate(false)
                return self;
                
            }

        })
    }
    }

    self.TgtdbDetcolumnArray = [
        {headerText: 'Product Name',
        field: 'ProductName'},
        {headerText: 'DB Name',
     field: 'DBNAME'},
     {headerText: 'Product Version',
     field: 'ProductVersion'},
     {headerText: 'OS Platform',
     field: 'platform'},
     {headerText: 'OS Version',
     field: 'OSVer'} 
  ]


           
    self.dbTgtDetListDP = new ArrayDataProvider(self.dbTgtDetList, {keyAttributes: 'DBNAME'});    


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
                     ////(e);
                 },
                 success: function (data) {
                     for (var i = 0; i < data[0].length; i++) {
                         self.ProcessName.push({ 'label' : data[0][i].id  ,'value' : data[0][i].category });
                     }
                     self.ProcessName.valueHasMutated();
 
                     ////(self);
                     return self;
                 }
             })
         };
         

         self.saveViewMsg = ko.observable();

         self.pgSaveView = function (data, event) {
            self.saveViewMsg('');  
            document.querySelector('#SelectSchemaProcessDialog').open();
            $.ajax({
                url: self.TGTonepDepUrl() + "/pgcreateprocedure",
                data: JSON.stringify({
                    dbName : self.TGTcurrentPDB(),
                    procText : self.procConvertedText()
                }),
                type: 'POST',
                dataType: 'json',
                context: self,
                error: function (e) {
                    ////(e);
                },
                success: function (data) {
                    document.querySelector('#SelectSchemaProcessDialog').close();
                    document.querySelector('#openDialog').open();
                    self.saveViewMsg(data[0]);
                    updateExcel(data[0])
                    ////(self);
                    return self;
                }
            })
        };
        self.trailfileDP = new ArrayDataProvider(self.trailFiles, {idAttribute: 'trail'});
        self.processDP = new ArrayDataProvider(self.ProcessName, {keyAttributes: 'value'});


        self.saveOKView = function (data, event) {
            document.querySelector('#openDialog').close();
        }

        self.selectedView = new keySet.ObservableKeySet(); // observable bound to selection option to monitor current selections
        self.selectedSelectionRequired = ko.observable(true);
        self.firstSelectedItem = ko.observable();
        self.selectedTrailFile = ko.observableArray([]);

        self.handleSelectedChanged = function (event) {
            self.gettraildet(false);
            self.selectedTrailFile(self.getDisplayValue(event.detail.value)); // show selected list item elements' ids
          };

        self.CountDataProvider = new ArrayDataProvider(self.TrailCount, {idAttribute: 'id'});

        self.procConvertedText = ko.observable('');
        

        self.clickConvert = function (data, event) {
            self.procConvertedText('');  
            document.querySelector('#SelectSchemaProcessDialog').open();
            const viewProcString = self.viewText().join(' ')
            $.ajax({
                url: self.TGTonepDepUrl() + "/convertProcedure",
                data: JSON.stringify({
                    dbName : self.TGTcurrentPDB(),
                    viewProc : viewProcString
                }),
                type: 'POST',
                dataType: 'json',
                context: self,
                error: function (e) {
                    console.log(e);
                },
                success: function (data) {
                    console.log(data)
                    document.querySelector('#SelectSchemaProcessDialog').close();
                    const singleLine = data[0].replace(/[\r\n]+/g, '');
                    self.procConvertedText(singleLine);
                    ////(self);
                    return self;
                }
            })
        };


        self.clickRetryConvert = function (data, event) {
            document.querySelector('#openDialog').close();
            self.procConvertedText('');  
            document.querySelector('#SelectSchemaProcessDialog').open();
            $.ajax({
                url: self.TGTonepDepUrl() + "/pgretryconvertproc",
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
                    document.querySelector('#SelectSchemaProcessDialog').close();
                    self.procConvertedText(data[0]);
                    //console.log(self);
                    return self;
                }
            })
        };
    
   self.clickUpload = function (data, event) {
            console.log(self.procConvertedText())
            document.querySelector('#openDialog').close();
            document.querySelector('#SelectSchemaProcessDialog').open();
            console.log(self.getDisplayValue(self.selectedView())[0])
            $.ajax({
                url: self.TGTonepDepUrl() + "/clickUploadFile",
                data: JSON.stringify({
                    viewProc : self.procConvertedText(),
                    procName : self.getDisplayValue(self.selectedView())[0],
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