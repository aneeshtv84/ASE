
define(['knockout', 'jquery', 'appController', 'ojs/ojarraydataprovider','ojs/ojarraytreedataprovider','ojs/ojflattenedtreedatagriddatasource','ojs/ojjsontreedatasource','ojDiagram/viewModels/CircleLayout','ojs/ojattributegrouphandler','ojs/ojknockouttemplateutils','ojs/ojdiagram','ojs/ojformlayout','ojs/ojdatagrid', 'ojs/ojbutton', 'ojs/ojtable', 'ojs/ojdialog', 'ojs/ojinputtext', 'ojs/ojselectsingle','ojs/ojformlayout','ojs/ojanimation','ojs/ojradioset','ojs/ojtreeview'],
function (ko, $,app, ArrayDataProvider ,ArrayTreeDataProvider,KnockoutTemplateUtils) {

    class crtshootViewModel {
      constructor(context){
        var self = this;
        self.DepName = context.DepName;
        this.KnockoutTemplateUtils = KnockoutTemplateUtils;
        self.DBMainVer = ko.observable();
        self.DBMinorVer = ko.observable();
        self.DBDet = ko.observableArray([]);
        self.RepDet = ko.observableArray([]);
        self.PRSession = ko.observableArray([]);
        self.repName = ko.observable();
        self.Pstack =  ko.observableArray([]);
        self.PStackChilden = ko.observableArray([]);
        self.ButtonVal = ko.observable(true);
        self.CRASH = ko.observableArray([]);
        self.CRSQL = ko.observableArray([]);


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


        self.CancelBehaviorOpt = ko.observable('icon');

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
                        if (data[0][i].RepType == 'CLASSIC') {
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
        document.querySelector('#Progress').open();
            self.DBDet([]);
            self.PRSession([]);
            self.Pstack([]);
            self.CRASH([]);
            self.CRSQL([]);
            $.ajax({
                url: self.DepName() + "/crtshoot",
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
                    document.querySelector('#Progress').close();
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

            for(var key in data[2]) {
                self.PStackChilden([]);
                        for( var i = 0; i < data[2][key].length; i++ ) {
                self.PStackChilden.push({'title' : data[2][key][i]})
                        }
                self.Pstack.push({'id' : key , 'title' : 'Thread ' + key , "children": self.PStackChilden()});
            }

            for (var i = 0; i < data[3].length; i++) {
              self.CRASH.push({'INST_ID' : data[3][i].INST_ID ,'EVENT' : data[3][i].EVENT , 'TOTAL_COUNT' : data[3][i].TOTAL_COUNT});
          }

          for (var i = 0; i < data[4].length; i++) {
            self.CRSQL.push({'SQL' : data[4][i].SQL_FULLTEXT });
        }

                    self.DBDet.valueHasMutated();
                    self.PRSession.valueHasMutated();
                    self.CRASH.valueHasMutated();
                    self.CRSQL.valueHasMutated();
                    //console.log(self);
                    return self;
                }

            })

        }


   
        self.DBDetDP = new ArrayDataProvider(self.DBDet,{keyAttributes: 'DBID'});
        self.PRSessionDP = new ArrayDataProvider(self.PRSession,{keyAttributes: 'SPID'});
        self.PstackDataDP = new ArrayTreeDataProvider(self.Pstack,{keyAttributes: 'id'});
        self.RunningSqlInfoDP = new ArrayTreeDataProvider(self.CRSQL,{keyAttributes: 'SQL'});
        self.ActiveSQLInfoDP = new ArrayTreeDataProvider(self.CRASH,{keyAttributes: 'EVENT'});

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


        self.PstackcolumnArray = [{headerText: 'Thread',
                            field: 'Thread'},
                            {headerText: 'Stack',
                            field: 'Stack'},
                        ];         
                        
                        
        self.RunningSqlcolumnArray = [{headerText: 'SQL',
                        field: 'SQL'}];   

        self.ActiveSQLcolumnArray = [{headerText: 'Instance',
                        field: 'INST_ID'},
                        {headerText: 'Event',
                        field: 'EVENT'},
                        {headerText: 'Event Count',
                        field: 'TOTAL_COUNT'}
                      ];                    
                        

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
    return  crtshootViewModel;
}
)