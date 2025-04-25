
define(['knockout', 'jquery', 'appController', 'ojs/ojarraydataprovider','ojs/ojarraytreedataprovider','ojs/ojflattenedtreedatagriddatasource','ojs/ojjsontreedatasource','ojDiagram/viewModels/CircleLayout','ojs/ojattributegrouphandler','ojs/ojknockouttemplateutils','ojs/ojdiagram','ojs/ojformlayout','ojs/ojdatagrid', 'ojs/ojbutton', 'ojs/ojtable', 'ojs/ojdialog', 'ojs/ojinputtext', 'ojs/ojselectsingle','ojs/ojformlayout','ojs/ojanimation','ojs/ojradioset','ojs/ojtreeview'],
function (ko, $,app, ArrayDataProvider ,ArrayTreeDataProvider,flattenedModule,JsonTreeDataSource,layout,attributeGroupHandler,KnockoutTemplateUtils) {

    class prtshootViewModel {
        constructor(context){
        var self = this;
        self.DepName = context.DepName;
        self.KnockoutTemplateUtils = KnockoutTemplateUtils;
        self.DBMainVer = ko.observable();
        self.DBMinorVer = ko.observable();
        self.DBDet = ko.observableArray([]);
        self.RepDet = ko.observableArray([]);
        self.PRSession = ko.observableArray([]);
        self.repName = ko.observable();
        self.SchedInfo = ko.observableArray([]);
        self.RunningTxnInfo = ko.observableArray([]);
        self.NodeData = ko.observableArray([]);
        self.LinkData = ko.observableArray([]);
        self.TxnData = ko.observableArray([]);
        self.WaitTxnData =  ko.observableArray([]);
        self.Pstack =  ko.observableArray([]);
        self.currentFormat = ko.observable('tab');
        self.PStackChilden = ko.observableArray([]);
        self.ButtonVal = ko.observable(true);

        self.isRequired = ko.observable(true);
        self.checkboxValues = ko.observableArray(['required', 'helpSource', 'helpDef']);

        self.isRequired = ko.computed(function () {
            return self.checkboxValues.indexOf('required') !== -1;
        });

        self.helpDef = ko.computed(function () {
            return (self.checkboxValues.indexOf('helpDef') !== -1) ? self._HELP_DEF : null;
        });

        self.helpSource = ko.computed(function () {
            return (self.checkboxValues.indexOf('helpSource') !== -1) ? self._HELP_SOURCE : null;
        });

        function getRep() {
            self.RepDet([]);
            $.ajax({
                url: self.DepName() + "/reptype",
                type: 'GET',
                dataType: 'json',
                context: self,
                error: function (e) {
                    //console.log(e);
                },
                success: function (data) {

                    for (var i = 0; i < data[0].length; i++) {
                        if (data[0][i].RepType == 'PARALLEL') {
                        self.RepDet.push({value:data[0][i].RepName,label:data[0][i].RepName});
                        }
                }
                self.RepDet.valueHasMutated();
                self.ButtonVal(true);
            }
            })
        }

        self.RepDetDP = new ArrayDataProvider(self.RepDet, {keyAttributes: 'value'});

    self.PRTShoot =     function(data,event) {
            self.DBDet([]);
            self.PRSession([]);
            self.SchedInfo([]);
            self.RunningTxnInfo([]);
            self.TxnData([]);
            self.WaitTxnData([]);
            self.LinkData([]);
            self.Pstack([]);
            $.ajax({
                url: self.DepName() + "/prtshoot",
                type: 'POST',
                data: JSON.stringify({
                    repName: self.repName()
                }),
                dataType: 'json',
                context: self,
                error: function (e) {
                    //console.log(e);
                },
                success: function (data) {

                 for (var i = 0; i < data[0].length; i++) {
                    self.DBDet.push({
                    'DATABASE_ROLE': data[0][i].DATABASE_ROLE,
                    'DBID': data[0][i].DBID,
                    'DB_EDITION': data[0][i].DB_EDITION,
                    'HOST': data[0][i].HOST,
                    'INSTANCE': data[0][i].INSTANCE,
                    'DBNAME' : data[0][i].DBNAME,
                    'PDB' : data[0][i].PDB,
                    'PLATFORM_NAME': data[0][i].PLATFORM_NAME,
                    'VERSION': data[0][i].VERSION
                });
            }
            for (var i = 0; i < data[1].length; i++) {
                self.PRSession.push({'SID' : data[1][i].SID,
                                     'SERIAL' : data[1][i].SERIAL,
                                     'SPID' : data[1][i].SPID,
                                     'SQL_ID' : data[1][i].SQL_ID,
                                     'EVENT' : data[1][i].EVENT,
                                     'CALL' : data[1][i].CALL,
                                     'NAME' : data[1][i].NAME });
            }

            for (var i = 0; i < data[2].length; i++) {
                self.SchedInfo.push({'attr' : { 'id' :  data[2][i].Group , 'name' : data[2][i].Group},"children": [{'attr' : { 'id' :  data[2][i].Group , 'name' : data[2][i].Group}}]});
            }
            for (var i = 0; i < data[3].length; i++) {
                self.RunningTxnInfo.push({'id' :  data[3][i].Group ,  'Txn' : data[3][i].Txn});
            }
            for (var i = 0; i < data[4].length; i++) {
                if (data[4][i].category === 'Txn'){
                self.NodeData.push({'id' : data[4][i].id + '-X' , 'category' : data[4][i].category})
                }
                else if (data[4][i].category === 'WaitTxn') {
                self.NodeData.push({'id' : data[4][i].id + '-Y', 'category' : data[4][i].category})
                }
            }

            for (var i = 0; i < data[5].length; i++) {
                self.LinkData.push({'id':data[5][i].id,'category' : data[5][i].category,'start' : data[5][i].start + '-X' , 'end' :data[5][i].end + '-Y','Wait' : 'Waiting on'});
            }


            for(var key in data[6]) {
                self.PStackChilden([]);
                        for( var i = 0; i < data[6][key].length; i++ ) {
                self.PStackChilden.push({'title' : data[6][key][i]})
                        }
                self.Pstack.push({'id' : key , 'title' : 'Thread ' + key , "children": self.PStackChilden()});
            }

                

                    self.DBDet.valueHasMutated();
                    self.PRSession.valueHasMutated();
                    self.SchedInfo.valueHasMutated();
                    self.RunningTxnInfo.valueHasMutated();
                    self.TxnData.valueHasMutated();
                    self.WaitTxnData.valueHasMutated();
                    self.LinkData.valueHasMutated();

                    //console.log(self);
                    return self;
                }

            })

        }


        self.dataSource = ko.observable();
        var options = {
          expanded: 'all',
          rowHeader: 'name',
          columns: ['Txn']
        };
        var flattenedData = new flattenedModule.FlattenedTreeDataGridDataSource(new JsonTreeDataSource(self.RunningTxnInfo), options);
        this.dataSource(flattenedData);
    
        self.DBDetDP = new ArrayDataProvider(self.DBDet,{keyAttributes: 'DBID'});
        self.PRSessionDP = new ArrayDataProvider(self.PRSession,{keyAttributes: 'SPID'});
        self.RunningTxnInfoDP = new ArrayDataProvider(self.RunningTxnInfo,{keyAttributes: 'Group'});
        self.LinkDataDP = new ArrayDataProvider(self.LinkData,{keyAttributes: 'id'});
        self.PstackDataDP = new ArrayTreeDataProvider(self.Pstack,{keyAttributes: 'id'});


        self.PRDBDetcolumnArray = [{headerText: 'Database Name',
                            field: 'DBNAME'},
                            {headerText: 'PDB Name',
                            field: 'PDB'},
                            {headerText: 'DBID',
                            field: 'DBID'},
                            {headerText: 'Instance ID',
                            field: 'INSTANCE'},
                            {headerText: 'Database|Edition',
                            field: 'DB_EDITION'},
                            {headerText: 'Host',
                            field: 'HOST'},
                            {headerText: 'Database|Role',
                            field: 'DATABASE_ROLE'},
                            {headerText: 'Version',
                            field: 'VERSION'}
                            ];    

        self.PRSessioncolumnArray = [{headerText: 'Session ID',
                            field: 'SID'},
                            {headerText: 'Serial#',
                            field: 'SERIAL'},
                            {headerText: 'Database PID',
                            field: 'SPID'},
                            {headerText: 'SQL ID',
                            field: 'SQL_ID'},
                            {headerText: 'Database Wait Event',
                            field: 'EVENT'},
                            {headerText: 'Last Call ET',
                            field: 'CALL'},
                            {headerText: 'Process',
                            field: 'NAME'}
                            ];    

        self.WaitTxncolumnArray = [{headerText: 'Transaction ID',
                            field: 'start'},
                            {headerText: 'Wait',
                            field: 'Wait'},
                            {headerText: 'Transaction ID',
                            field: 'end'}
                            ];   

        self.RunningTxncolumnArray = [{headerText: 'Group',
                            field: 'id'},
                            {headerText: 'Transaction ID',
                            field: 'Txn'}];  

        self.PstackcolumnArray = [{headerText: 'Thread',
                            field: 'Thread'},
                            {headerText: 'Stack',
                            field: 'Stack'},
                        ];          

                              self.colorHandler = new attributeGroupHandler.ColorAttributeGroupHandler();
                              self.layoutFunc = layout.layout;
                              self.highlightedCategoriesValue = ko.observable(null);
                              self.hoverBehaviorValue = ko.observable("dim");
                              self.hoverBehaviorValueChange = function(event) {
                                // reset initial highlighted categories
                                if (event.detail.value === 'none')
                                self.highlightedCategoriesValue(null);
                              };
                              self.nodeDataProvider = new ArrayDataProvider(self.NodeData, {keyAttributes: 'id'});
                              self.linkDataProvider = new ArrayDataProvider(self.LinkData, {keyAttributes: 'id'});
                              self.styleDefaults = {
                                nodeDefaults : {
                                  icon : {width :150, shape : "rectangle"}
                                },
                                linkDefaults:{svgStyle: {vectorEffect: 'non-scaling-stroke', opacity: .4}}
                              };
                        
                              self.formatDetails = function(data) {
                                return 'Waiting on ' +  data ;
                              }

                     
                              //use custom tooltip for the object to present data in readable format
                              var tooltipElem = document.createElement('div');
                              
                              tooltipElem.innerHTML='<div style="float:left;padding:10px 8px 10px 3px;"> \
                                                       <span style="font-weight:bold;color:#606060;"></span> \
                                                       <br> \
                                                       <span style="font-style:italic;"></span> \
                                                     </div>';


                              var labelText = tooltipElem.children[0].children[0];
                              var valueText = tooltipElem.children[0].children[2];
                        
                              self.tooltipFunction = function(dataContext) {
                                var id = dataContext.id;
                                dataContext.parentElement.style.borderWidth = "2px";
                                dataContext.parentElement.style.borderColor = "gray";
                                labelText.textContent = dataContext.itemData.start;
                                valueText.textContent = self.formatDetails(dataContext.itemData.end);
                                return {'insert':tooltipElem};
                              };

                              self.valueChangedHandler = (event) => {
                                self.ButtonVal(false);
                            };

                              self.connected = function () { 
                                if (sessionStorage.getItem("userName")==null) {
                                  oj.Router.rootInstance.go('signin');
                              }
                              else
                              { app.onAppSuccess();      
                                self.RepDet([]);      
                                getRep();
                              }
                            };

            
    }
}
    return  prtshootViewModel;
}
)