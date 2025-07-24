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

                self.TgtOnePDepName = ko.observable();

                self.TGTcurrentPDB = ko.observable();

                self.isFormReadonly = ko.observable(false);

                self.TGTonepDepUrl = ko.observable();

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
                    //console.log(e);
                },
                success: function (data) {
                    // console.log(data[0])
                    self.viewDetail([]);
                    for (var i = 0; i < data[0].length; i++) {
                         self.viewDetail.push({'owner': data[0][i][0],'procname':   data[0][i][1]});
                     }
        
                    // console.log(self.viewDetail())
                    self.schemaList([]);
                    for (var i = 0; i < data[1].length; i++) {
                        self.schemaList.push({'label': data[1][i], 'value': data[1][i]})
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
            document.querySelector('#SelectSchemaDialog').open();
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
                                    document.querySelector('#SelectSchemaDialog').close();
                                    document.querySelector('#TimeoutInLoad').open();
                                }
                            },
                success: function (data) {
                    // console.log(data[0])
                         self.viewNameDet([]);
                    for (var i = 0; i < data[0].length; i++) {
                        for (var j = 0; j < data[0][i].length; j++) {
                        self.viewNameDet.push({ 'vname': data[0][i][j][0]});
                        }
                    }
                    self.viewNameDet.valueHasMutated();
                    // console.log(self.viewNameDet())
                document.querySelector('#SelectSchemaDialog').close();
                    return self;
                    
                }

            })
        }

        self.viewNameDetDP = new ArrayDataProvider(self.viewNameDet, {keyAttributes: 'vname'});

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
            // console.log(self.getDisplayValue(self.selectedView())[0])
            // console.log(self.firstSelectedItem())
            self.procConvertedText('');
            document.querySelector('#SelectSchemaDialog').open();
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
                                    document.querySelector('#SelectSchemaDialog').close();
                                    document.querySelector('#TimeoutInLoad').open();
                                }
                            },
                success: function (data) {
                    // console.log(data[0])
                         self.viewText('');
                         self.viewText(data[0]);
                document.querySelector('#SelectSchemaDialog').close();
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
            //    console.log( self.TgtDBDet())
               return self;
           }
           })
       }


       self.TgtDBDetDP = new ArrayDataProvider(self.TgtDBDet, { keyAttributes: 'value' });

       self.SelectTGTDeployment = (event,data) =>{
          if (self.TgtOnePDepName()){
              document.querySelector('#SelectSchemaDialog').open();
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
                document.querySelector('#SelectSchemaDialog').close();
                return self;
            }
        })
          }
    
       };

       self.dbTgtDetList =  ko.observableArray([]);


       self.DBTgtSchema = function (data, event) {
        if(self.TGTcurrentPDB()){
        document.querySelector('#SelectSchemaDialog').open();
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
                                document.querySelector('#SelectSchemaDialog').close();
                                document.querySelector('#TimeoutInLoad').open();
                            }
                        },
            success: function (data) {
           
                    self.dbTgtDetList.push({ 'DBNAME': data[0].dbName,'ProductName' : data[0].prodName,'ProductVersion' : data[0].prodVersion, 'platform': data[0].osPlat ,'OSVer' : data[0].osVer });
                self.dbTgtDetList.valueHasMutated();
                document.querySelector('#SelectSchemaDialog').close();
                // console.log(self.dbTgtDetList())
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
            document.querySelector('#SelectSchemaDialog').open();
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
                    //console.log(e);
                },
                success: function (data) {
                    document.querySelector('#SelectSchemaDialog').close();
                    document.querySelector('#openDialog').open();
                    self.saveViewMsg(data[0]);
                    //console.log(self);
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
            document.querySelector('#SelectSchemaDialog').open();
            $.ajax({
                url: self.TGTonepDepUrl() + "/pgconvertprocedure",
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
                    document.querySelector('#SelectSchemaDialog').close();
                    self.procConvertedText(data[0]);
                    //console.log(self);
                    return self;
                }
            })
        };


        self.clickRetryConvert = function (data, event) {
            document.querySelector('#openDialog').close();
            self.procConvertedText('');  
            document.querySelector('#SelectSchemaDialog').open();
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
                    document.querySelector('#SelectSchemaDialog').close();
                    self.procConvertedText(data[0]);
                    //console.log(self);
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