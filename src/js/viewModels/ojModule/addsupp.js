
define(['ojs/ojcore', 'knockout', 'jquery', 'appController',"ojs/ojpagingdataproviderview", 'ojs/ojarraydataprovider', 'ojs/ojarraytreedataprovider',"ojs/ojkeyset", 
'ojs/ojbutton', 'ojs/ojtable', 'ojs/ojdialog', 'ojs/ojinputtext', 'ojs/ojselectsingle','ojs/ojprogress-bar','ojs/ojtable','ojs/ojhighlighttext',
"ojs/ojpagingcontrol",'ojs/ojvalidationgroup'],
function (oj, ko, $, app,PagingDataProviderView, ArrayDataProvider,ArrayTreeDataProvider,ojkeyset_1) {

    class addsuppViewModel {
        constructor(context) {
        var self = this;
        self.DepName = context.DepName;
        self.dbSuppInfo = ko.observableArray([]);

        self.DBDet = ko.observableArray([]);
        self.currentDB = ko.observable();
        self.schemaNameList = ko.observableArray([]);
        self.currentPDB = ko.observable();

        self.selectedDomCategory = ko.observable();
        self.selectedAliascategory = ko.observable();
        self.selectedUsercategory = ko.observable();
        self.aliascategories = ko.observableArray([]);
        self.unamecategories = ko.observable();
        self.gatherMeta = ko.observable(false);

        self.selectionInfo = ko.observable("");
        self.tabNameList = ko.observableArray([]);

        self.CDBCheck = ko.observable();

        self.buttonStates = ko.observable(true);
        self.groupValid = ko.observable();
        self.OPError = ko.observableArray([]);


        function getDB() {
            self.DBDet([]);
            $.ajax({
                url: self.DepName() + "/dbdet",
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
                    for (var i = 0; i < data[0].length; i++) {
                        self.DBDet.push({'value' : data[0][i].dbname, 'label' : data[0][i].dbname});
                }

                self.DBDet.valueHasMutated();
                return self;
            }
            })
        }

        self.DBDetDP = new ArrayDataProvider(self.DBDet, { keyAttributes: 'value' });
        


        self.dberr = ko.observable();
        self.CancelBehaviorOpt = ko.observable('icon');
        
        self.DBParam = ko.observable();
        self.getSuppLog = function(event,data)  {
            if(self.currentDB()){
            //self.connected();
            document.querySelector('#SuppLogDialog').open();
            self.dbSuppInfo([]);
            self.CDBCheck('');
            $.ajax({
                url: self.DepName() + "/supplog",
                type: 'POST',
                dataType: 'json',
                data: JSON.stringify({
                    dbname : self.currentDB()
                }),
                timeout: sessionStorage.getItem("timeInetrval"),
                context: self,
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                        //console.log(textStatus)
                        document.querySelector('#SuppLogDialog').close();
                        document.querySelector('#TimeoutSup').open();
                    }
                },
                success: function (data) {
                    
                            self.dbSuppInfo.push({ 'DBName': data[0].name , 'Status' : data[0].Truncation})
                             getDomains();
                             document.querySelector('#SuppLogDialog').close();
                             return self;
                    }
                    
            })
        }
        }

        self.dbsupplogDP = new ArrayDataProvider(self.dbSuppInfo, { keyAttributes: 'DBUnique' });
        self.SchemaName = ko.observable();

        self.supplogcolumnArray = [{
            headerText: 'Database Name',
            field: 'DBName'
        },
        {
            headerText: 'Status',
            field: 'Status'
        }

        ];

        self.openListener = function (event) {
            oj.Router.rootInstance.go('incidents');
        };

        self.username1 = ko.observableArray([]);
        self.aliasname1 = ko.observableArray([]);
        self.domname1 = ko.observableArray([]);
        self.othdom = ko.observableArray([]);
        self.alias = ko.observable();
        self.user = ko.observable();
        self.valdom = ko.observable();
        self.uName = ko.observable();
        self.uPasswd = ko.observable();
        self.uRepPass = ko.observable();

        self.buttonValue = ko.observable("add");
        self.dombuttonValue = ko.observable("existDom");
        self.domName = ko.observable();
        self.allcols = ko.observable();
        self.schema = ko.observable();
        self.AddSuppMsg = ko.observableArray([]);


        function getDomains() {
            self.username1([]);
            self.othdom([]);
            self.aliasname1([]);
            self.domname1([]);
            self.selectedAliascategory('');
            self.selectedUsercategory('');
            $.ajax({
                url: self.DepName() + "/ggcredstore",
                type: 'GET',
                dataType: 'json',
                timeout: sessionStorage.getItem("timeInetrval"),
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                        document.querySelector('#TimeoutSup').open();
                    }
                },
                success: function (data) {
                    for (var i = 0; i < data[1].length; i++) {
                        self.othdom.push({ dom: data[1][i].value });
                    }
                    self.aliasname1(data[4]);

                    for (var i = 0; i < data[2].length; i++) {
                        self.domname1.push({ label: data[2][i], value: data[2][i] });
                    }
                    for (var i = 0; i < data[0].length; i++) {
                        self.username1.push({ label: data[0][i].alias, value: data[0][i].alias, 'children': [{ label: data[0][i].uname, value: data[0][i].uname }] });
                    }
                    //console.log(self)
                    return self;
                }
            })
        }



        let getAliascategories = (category) => {
            let found = self.aliasname1().find(c => c.value === category);
            return found ? found.children : null;
        };
        let getUnamecategories = (category) => {
            let found = self.username1().find(c => c.value === category);
            return found ? found.children : null;
        };
        self.domSelectionChanged = (event) => {
            self.selectedAliascategory('');
            let children = getAliascategories(event.detail.value);
            self.aliascategories(children);
        };


        self.OthDomProvider = new ArrayDataProvider(self.othdom, { keyAttributes: 'value' });

        self.tranlevelVal = ko.observable('trandata');

        var tranlevel = [
            { value: 'trandata', label: 'Trandata' }
        ];

        self.tranlevelDP = new ArrayDataProvider(tranlevel, { keyAttributes: 'value' });


        self.STVal = ko.observable('');

        var STOptions = [
            { value: 'ALLCOLS', label: 'ALLCOLS' },
            { value: 'NOSCHEDULINGCOLS', label: 'NOSCHEDULINGCOLS' },
            { value: '', label: 'Default' },
        ];

        self.STOptionsDP = new ArrayDataProvider(STOptions, { keyAttributes: 'value' });


        self.pdbName = ko.observable('');

        self.suppLogSchema = function (data, event) {
            self.schemaNameList([]);
            $.ajax({
                url: self.DepName() + "/supplogschema",
                type: 'POST',
                data: JSON.stringify({
                    dbname : self.currentPDB(),
                    cdbCheck : self.CDBCheck(),
                    pdbName : self.pdbName()
                }),
                dataType: 'json',
                timeout: sessionStorage.getItem("timeInetrval"),
                context: self,
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                        document.querySelector('#TimeoutSup').open();
                    }
                },
                success: function (data) {
                    for (var i = 0; i < data[0].length; i++) {
                        self.schemaNameList.push({ 'label': data[0][i].username, 'value': data[0][i].username });
                    }
                    self.schemaNameList.valueHasMutated();
                    return self;
                }

            })
        }

        self.schemaListDP = new ArrayDataProvider(self.schemaNameList, { keyAttributes: 'label' });

        self.schemaList = ko.observableArray([]);

        self.tableNameList = ko.observableArray([]);

        self.TableFetch = function (data, event) {
            if (self.schemaList().length>0){
            document.querySelector('#SelectSchemaDialog').open();
            self.tableNameList([]);
            $.ajax({
                url: self.DepName() + "/tablelist",
                type: 'POST',
                data: JSON.stringify({
                    dbname : self.currentPDB(),
                    schemaList : self.schemaList(),
                    cdbCheck : self.CDBCheck(),
                    pdbName : self.pdbName(),
                    gatherMeta : self.gatherMeta()
                }),
                dataType: 'json',
                timeout: sessionStorage.getItem("timeInetrval"),
                context: self,
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                        document.querySelector('#TimeoutSup').open();
                    }
                },
                success: function (data) {
                    document.getElementById('tableTrandata').refresh();
                    for (var i = 0; i < data[0].length; i++) {
                        self.tableNameList.push({'TABLE_NAME': data[0][i].owner + '.' + data[0][i].table_name , 'ROWCNT' : data[0][i].num_rows ,'AVGSPC': data[0][i].avg_space,'ANALYZETIME' : data[0][i].last_analyzed});
                    }
                    self.tableNameList.valueHasMutated();
                    //console.log(self);
                    document.querySelector('#SelectSchemaDialog').close();
                    return self;
                }

            })
        }
    }
        self.tableNameListDP = new PagingDataProviderView(new ArrayDataProvider(self.tableNameList, {idAttribute: 'TABLE_NAME'}));   
        

        self.tableListcolumnArray = [
            {headerText: 'Schema.Table Name',
            field: 'TABLE_NAME'},
            {headerText: 'Row Count',
            field: 'ROWCNT'},
            {headerText: 'Average Size(MB)',
            field: 'AVGSPC'},
            {headerText: 'Analyze Time',
            field: 'ANALYZETIME'} ]


            self.popUpResizeSM = (value) => {
                document.getElementById(value).style.width="500px";
                document.getElementById(value).style.height="70vh";
            }


            this.selectedItems = ko.observable({
                row: new ojkeyset_1.KeySetImpl(),
                column: new ojkeyset_1.KeySetImpl(),
            });
            
            this.selectedSelectionMode = ko.observable({
                row: "multiple",
                column: "none",
            });
            this.selectionModes = [
                { value: { row: "multiple", column: "none" }, label: "Multiple Row" }
            ];
            this.selectionModeDP = new ArrayDataProvider(this.selectionModes, {
                keyAttributes: "value",
            });

            this.selectedChangedListener = (event) => {
                let selectionText = "";
                if (event.detail.value.row.isAddAll()) {
                    const row=self.tableNameList();
                    for(var i=0;i<row.length;i++) {
                        selectionText = selectionText +  row[i].TABLE_NAME + ", " ;
                    }
                    if(event.detail.value.row._keys.size>0){
                        event.detail.value.row._keys.forEach(function (key) {
                            selectionText = selectionText.replace(key+",", "");
                        });
                        
                       }
                       selectionText = selectionText.replace(/,\s*$/,"");
                }
                else {
                    const row = event.detail.value.row;
                    const column = event.detail.value.column;
                    if (row.values().size > 0) {
                        row.values().forEach(function (key) {
                            selectionText += selectionText.length === 0 ? key : ", " + key;
                        });
                        selectionText = '' + selectionText;
                    }
                    if (column.values().size > 0) {
                        column.values().forEach(function (key) {
                            selectionText += selectionText.length === 0 ? key : ", " + key;
                        });
                        selectionText = "Column Selection:\nColumn Keys: " + selectionText;
                    }
                }
                this.selectionInfo(selectionText);
                if(self.selectionInfo().length>0){
                    self.buttonStates(false)
                }
                else{
                    self.buttonStates(true);
                }

            };
            this.selectedSelectionMode.subscribe((newValue) => {
                // Reset selected Items on selection mode change.
                this.selectedItems({ row: new ojkeyset_1.KeySetImpl(), column: new ojkeyset_1.KeySetImpl() });
            });


            self.currentTabList = ko.computed( { 
                read:function() {
                    self.tabNameList([]);
                    var currentTabList ='';
                    if (self.selectionInfo().length > 0){
                    let selectedData = self.selectionInfo().split(",");
                    for(var i =0 ; i< selectedData.length; i++){
                        self.tabNameList.push(selectedData[i]);
                    }
                }
                  return currentTabList;
                    
              },
              write: function(newVal) {
                  var currentTabList = newVal;
                  return newVal;
              }
              });

            var data;
            var params = {
                url: self.DepName() + "/addsupplog",
                type: 'POST',
                data: data,
                dataType: 'json',
                context: self,
                error: function (e) {
                    //console.log(e);
                },
                success: function (data) {
                    document.querySelector('#SuppLogDialog').close();
                    self.popUpResizeSM('AddTranSuppDialog');
                    document.querySelector('#AddTranSuppDialog').open();
                    self.AddSuppMsg(data[0]);
                    self.AddSuppMsg.valueHasMutated();
                    return self;
                }
            }

           self.addSuppLog = function (data, event) {
       
            if(self.tranlevelVal() == 'schematrandata'){
                document.querySelector('#DeleteSupp').close();
                let valid = self._checkValidationGroup("tracker");
                if (valid) {
                document.querySelector('#SuppLogDialog').open();
                    self.AddSuppMsg([]);
                    params.data = JSON.stringify({
                                    domain : self.selectedDomCategory(),
                                    alias : self.currentPDB(),
                                    tranlevel : self.tranlevelVal(),
                                    SchemaName : self.SchemaName(),
                                    buttonValue : self.buttonValue() ,
                                    opts : self.STVal()
                                })
                    $.ajax(params)
                            }
                            }
            else if(self.tranlevelVal() == 'trandata') {
                document.querySelector('#SuppLogDialog').open();
                self.AddSuppMsg([]);
                    params.data = JSON.stringify({
                                    domain : self.selectedDomCategory(),
                                    alias : self.currentPDB(),
                                    tranlevel : self.tranlevelVal(),
                                    tabNameList : self.tabNameList(),
                                    buttonValue : self.buttonValue() ,
                                    opts : self.STVal()
                            })
                    $.ajax(params)
                }
            }


        self._checkValidationGroup = (value) => {
            var tracker = document.getElementById(value);
            if (tracker.valid === "valid") {
                return true;
            }
            else {
                // show messages on all the components
                // that have messages hidden.
                tracker.showMessages();
                tracker.focusOn("@firstInvalidShown");
                return false;
            }
        };

self.openDelSuppLog = function (){
    if(self.tranlevelVal() == 'schematrandata'){
        let valid = self._checkValidationGroup("tracker");
        if (valid) {
        document.querySelector('#DeleteSupp').open();
        }
    }else{
        document.querySelector('#DeleteSupp').open();
    }
}


        self.addsuppOKClose = function (event) {
            document.querySelector('#AddTranSuppDialog').close();
        };

        self.CloseOkaddSuppLog =  function (event) {
            document.querySelector('#DeleteSupp').close();
        };

        //console.log(self);

        self.connected = function () {
            app.onAppSuccess();
            getDB() ;
            self.dbSuppInfo([]);
            self.gatherMeta(false);
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
     * Returns a constructor for the ViewModel so that the ViewModel is constructed
     * each time the view is displayed.  Return an instance of the ViewModel if
     * only one instance of the ViewModel is needed.
     */
    return addsuppViewModel;
}
);
