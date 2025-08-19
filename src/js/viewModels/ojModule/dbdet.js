
define(['ojs/ojcore', 'knockout', 'jquery','appController','ojs/ojarraydataprovider','ojs/ojconverter-number','ojs/ojknockout',
        'ojs/ojselectsingle', 'ojs/ojinputtext', 'ojs/ojlabel', 'ojs/ojformlayout','ojs/ojbutton', 'ojs/ojlabelvalue','ojs/ojdialog', 
        'ojs/ojprogress-bar',"ojs/ojradioset",'ojs/ojinputnumber','ojs/ojvalidationgroup','ojs/ojtable'],
function (oj, ko, $, app, ArrayDataProvider,NumberConverter) {

    class chkTblViewModel {
        constructor(context){
        var self = this;
        self.DepName = context.DepName;
        self.dbname = ko.observable();
        self.adduname = ko.observable();
        self.addupasswd = ko.observable();
        self.addservicename = ko.observable();
        self.eduname = ko.observable();
        self.edupasswd = ko.observable();
        self.edservicename = ko.observable();
        self.AddDBMsg = ko.observable();
        self.viewDBMsg = ko.observableArray([]);
        self.depOption = ko.observable('ld');
        self.onePHost = ko.observable();
        self.onepPort = ko.observable();
        self.onepUName = ko.observable();
        self.onepPasswd = ko.observable();
        self.groupValid = ko.observable();
        self.CancelBehaviorOpt = ko.observable('icon');
        self.dbButton = ko.observable('addDB');
        self.userButton = ko.observable('addUser');
        self.username = ko.observable();
        self.username(sessionStorage.getItem("userName"));
        self.userRole = ko.observable();
        self.userRole(sessionStorage.getItem("userRole"));
        //console.log(self.userRole());

        self._HELP_DBService = 'hostname.domainname:dbport/dbservice';

        self._HELP_Role = 'OnePlace User Role';
      
        self.isFormReadonly = ko.observable(false); 
        self.isRequired = ko.observable(true);
        self.checkboxValues = ko.observableArray(['required', 'helpSource', 'helpDef']);

        self.isRequired = ko.computed(function () {
            return self.checkboxValues.indexOf('required') !== -1;
        });
        self.helpDBService = ko.computed(function () {
            return (self.checkboxValues.indexOf('helpDef') !== -1) ? self._HELP_DBService : null;
        });
        self.helpRole = ko.computed(function () {
            return (self.checkboxValues.indexOf('helpDef') !== -1) ? self._HELP_Role : null;
        });
        self.helpSource = ko.computed(function () {
            return (self.checkboxValues.indexOf('helpSource') !== -1) ? self._HELP_SOURCE : null;
        });      


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
        self.dialogTitle = ko.observable();
        
        self.addDB = function (data, event) {
            let valid = self._checkValidationGroup("dbcred");
            if (valid) {
            self.AddDBMsg('');
            document.querySelector('#addDBDialog').open();
            $.ajax({
                url: self.DepName() + "/dbconn",
                type: 'POST',
                data: JSON.stringify({
                    dbname : self.dbname(),
                    username: self.adduname(),
                    passwd : self.addupasswd(),
                    servicename : self.addservicename(),
                    dbButton : self.dbButton()
                }),
                dataType: 'json',
                timeout: sessionStorage.getItem("timeInetrval"),
                context: self,
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                        document.querySelector('#close').open();
                        document.querySelector('#TimeoutDb').open();
                    }
                },
                success: function (data) {
                    document.querySelector('#addDBDialog').close();
                    self.dialogTitle('Add CredentialStore User');
                    document.querySelector('#DBDialog').open();
                    self.AddDBMsg(data[0]);
                    getDB();
                    return self;
                }

            })
        }
        }

        self.editDB = function (data, event) {
            let valid = self._checkValidationGroup("editcred");
            if (valid) {
            self.AddDBMsg('');
            document.querySelector('#addDBDialog').open();
            $.ajax({
                url: self.DepName() + "/dbconn",
                type: 'POST',
                data: JSON.stringify({
                    dbname : self.currentDB(),
                    username: self.eduname(),
                    passwd : self.edupasswd(),
                    servicename : self.edservicename(),
                    dbButton : self.dbButton()
                }),
                dataType: 'json',
                timeout: sessionStorage.getItem("timeInetrval"),
                context: self,
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                        document.querySelector('#close').open();
                        document.querySelector('#TimeoutDb').open();
                    }
                },
                success: function (data) {
                    document.querySelector('#addDBDialog').close();
                    self.dialogTitle('Edit CredentialStore User');
                    document.querySelector('#DBDialog').open();
                    self.AddDBMsg(data[0]);
                    getDB();
                    return self;
                }

            })
        }
        }



        self.delDB = function (data, event) {
            let valid = self._checkValidationGroup("delcred");
            if (valid) {
            self.AddDBMsg('');
            document.querySelector('#DeleteDb').close();
            document.querySelector('#addDBDialog').open();
            $.ajax({
                url: self.DepName() + "/dbconn",
                type: 'POST',
                data: JSON.stringify({
                    dbname : self.currentDB(),
                    username: self.eduname(),
                    servicename : self.edservicename(),
                    dbButton : self.dbButton()
                }),
                dataType: 'json',
                timeout: sessionStorage.getItem("timeInetrval"),
                context: self,
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                        document.querySelector('#close').open();
                        document.querySelector('#TimeoutDb').open();
                    }
                },
                success: function (data) {
                    document.querySelector('#addDBDialog').close();
                    self.dialogTitle('Delete CredentialStore User');
                    document.querySelector('#DBDialog').open();
                    self.AddDBMsg(data[0]);
                    getDB();
                    return self;
                }

            })
        }
        }

        self.viewDB = function (data, event) {
            document.querySelector('#addDBDialog').open();
            $.ajax({
                url: self.DepName() + "/dbconn",
                type: 'POST',
                data: JSON.stringify({
                    dbname : self.currentDB(),
                    dbButton : self.dbButton()
                }),
                dataType: 'json',
                timeout: sessionStorage.getItem("timeInetrval"),
                context: self,
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                        document.querySelector('#close').open();
                        document.querySelector('#TimeoutDb').open();
                    }
                },
                success: function (data) {
                    document.querySelector('#addDBDialog').close();
                    self.dialogTitle('View Database Details');
                    document.querySelector('#ViewDbDlg').open();
                    self.viewDBMsg([]);
                    
                    let serverInfo = data[0].ProductVersion;
                    let parts = serverInfo.split('/');
                    let productName = parts[0].trim();
                    let productVersion = parts[1].split(' ')[0].trim();
                    let os = parts[5].split(' ')[0].trim();
                    let osbit = parts[4].trim();;
                    let osVersion = parts[5].split(' ')[1].trim();
                    let dbFile = parts[6].trim();
                    let buildID = parts[7].trim();
                    self.viewDBMsg.push({ 'DBNAME': data[0].DBNAME,'ProductName' : productName,'ProductVersion' : productVersion, 'platform': os ,'OSVer' : osVersion , 'OSBIT': osbit, 'DBFile' : dbFile ,'ServerEdition' : buildID });
                    // self.viewDBMsg.push({ 'DBNAME': data[0].DBNAME,'ProductName' : data[0].ProductName,'ProductVersion' : data[0].ProductVersion, 'platform': data[0].Platform ,'OSVer' : data[0].PlatformVer , 'DBFile' : data[0].DBFile ,'ServerEdition' : data[0].ServerEdition  });
                    return self;
                }

            })
        }


        self.viewDBMsgDP = new ArrayDataProvider(self.viewDBMsg, {keyAttributes: 'DBName'}); 

        self.viewDBColumArray = [{headerText: 'DB Name',
        field: 'DBNAME'},
        {headerText: 'Product Name',
        field: 'ProductName'},
        {headerText: 'Product Version',
        field: 'ProductVersion'},
        {headerText: 'OS Platform',
        field: 'platform'},
        {headerText: 'OS Version',
        field: 'OSVer'} ,
        {headerText: 'OS BIT',
            field: 'OSBIT'} ,
        {headerText: 'DB File',
        field: 'DBFile'} ,
        {headerText: 'DB Edition',
        field: 'ServerEdition'} 
     ]


self.valueChangedHandler = function (data, event) {
    document.querySelector('#addDBDialog').open();
    $.ajax({
        url: self.DepName() + "/selectdbdet",
        type: 'POST',
        data: JSON.stringify({
            dbname : self.currentDB()
        }),
        dataType: 'json',
        timeout: sessionStorage.getItem("timeInetrval"),
        context: self,
        error: function (xhr, textStatus, errorThrown) {
            if(textStatus == 'timeout' || textStatus == 'error'){
                document.querySelector('#close').open();
                document.querySelector('#TimeoutDb').open();
            }
        },
        success: function (data) {
            document.querySelector('#addDBDialog').close();
            if (data[0].length > 0){
            self.eduname(data[0][0].user);
            self.edservicename(data[0][0].servicename);
            }
            return self;
        }

    })
}

        self.delDBDlg = function (){
            let valid = self._checkValidationGroup("delcred");
            if (valid) {
            document.querySelector('#DeleteDb').open();
            }
        }



        self.CloseOkDlt =  function (event) {
            self.currentDB('');
            self.eduname('');
            self.edservicename('');
            document.querySelector('#DeleteDb').close();
        };


        self.CloseOkDBDet =  function (event) {
            document.querySelector('#ViewDbDlg').close();
        };

        self.AddDBMsgOKClose = function (event) {
            self.dbname('');
            self.adduname('');
            self.addupasswd('');
            self.addservicename('');
            self.currentDB('');
            self.eduname('');
            self.edupasswd('');
            self.edservicename('');
            document.querySelector('#DBDialog').close();
        };


        self.uname = ko.observable();
        self.upasswd = ko.observable();
        self.role = ko.observable();
        self.AddUserMsg = ko.observable();
      
        self.isFormReadonly = ko.observable(false); 
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
        
        self.currentRole = ko.observable();
        var onepRoles = [{ label  : "Admin" , value : 'admin' },
                            {label: "Data Operator", value : "dataoper"},
                            {label: "Reader", value : "reader"}];
        self.OneRoleDP = new ArrayDataProvider(onepRoles, {keyAttributes: 'value'});

        self.currentProtocol = ko.observable("http");
        self.onepProtocol = [
            { value: "http", label: "HTTP" },
            { value: "https", label: "HTTPS" }
        ];
        self.onepProtocolDP = new ArrayDataProvider(self.onepProtocol, {
            keyAttributes: "value",
        });

        self.decimalHalfDownConverter =
        new NumberConverter.IntlNumberConverter({
            style: 'decimal',
            roundingMode: 'HALF_DOWN',
            maximumFractionDigits: 0,
            useGrouping: false
        });

        self.addUser = function (data, event) {
            //console.log(self.userButton());
            let valid = self._checkValidationGroup("add_user");
            if (valid) {
            self.AddUserMsg('');
            document.querySelector('#addUserDialog').open();
            if(self.userButton() == 'addUser'){
                let parameter = JSON.stringify({
                    onepOps : 'add',
                    user: self.onepUName(),
                    passwd : self.onepPasswd(),
                    role : self.currentRole(),
                    dep_type : self.depOption(),
                    dep_url : self.currentProtocol() + '://' + self.onePHost() + ':' +  self.onepPort() 
                });
            }else if(self.userButton() == 'editUser'){
                let parameter = JSON.stringify({
                    onepOps : 'edit',
                    user: self.username(),
                    passwd : self.onepPasswd(),
                    dep_type : self.depOption()
                });
            }
            else {
                let parameter = JSON.stringify({
                    onepOps : 'del',
                    user: self.onepUName(),
                    dep_type : self.depOption()
                });
            }
            $.ajax({
                url: self.DepName() + "/onepconn",
                type: 'POST',
                data: JSON.stringify({
                    onepOps : 'add',
                    user: self.onepUName(),
                    passwd : self.onepPasswd(),
                    role : self.currentRole(),
                    dep_type : self.depOption(),
                    dep_url : self.currentProtocol() + '://' + self.onePHost() + ':' +  self.onepPort() 
                }),
                dataType: 'json',
                timeout: sessionStorage.getItem("timeInetrval"),
                context: self,
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                        document.querySelector('#addUserDialog').close();
                        document.querySelector('#TimeoutDb').open();
                    }
                },
                success: function (data) {
                    document.querySelector('#addUserDialog').close();
                    document.querySelector('#OnePDialog').open();
                    self.AddUserMsg(data[0]);
                    return self;
                }

            })
        }
        }

        self.editUser = function (data, event) {
            //console.log(self.userButton());
            let valid = self._checkValidationGroup("editUser");
            if (valid) {
                self.AddUserMsg('');
                document.querySelector('#addDBDialog').open();
                $.ajax({
                    url: self.DepName() + "/onepconn",
                    type: 'POST',
                    data: JSON.stringify({
                        onepOps : 'edit',
                        user: self.username(),
                        passwd : self.onepPasswd(),
                        dep_type: self.depOption(),
                        dep_url: self.currentProtocol() + '://' + self.onePHost() + ':' +  self.onepPort() 
                    }),
                    dataType: 'json',
                    timeout: sessionStorage.getItem("timeInetrval"),
                    context: self,
                    error: function (xhr, textStatus, errorThrown) {
                        if(textStatus == 'timeout' || textStatus == 'error'){
                            document.querySelector('#addUserDialog').close();
                            document.querySelector('#TimeoutDb').open();
                        }
                    },
                    success: function (data) {
                        document.querySelector('#addDBDialog').close();
                        document.querySelector('#OnePDialog').open();
                        self.AddUserMsg(data[0]);
                        return self;
                    }
    
                })
            }
            
        }

        self.delUser = function (data, event) {
            document.querySelector('#DeleteUser').close();
                self.AddUserMsg('');
                document.querySelector('#addDBDialog').open();
                $.ajax({
                    url: self.DepName() + "/onepconn",
                    type: 'POST',
                    data: JSON.stringify({
                        onepOps : 'del',
                        user: self.onepUName(),
                    }),
                    dataType: 'json',
                    timeout: sessionStorage.getItem("timeInetrval"),
                    context: self,
                    error: function (xhr, textStatus, errorThrown) {
                        if(textStatus == 'timeout' || textStatus == 'error'){
                            document.querySelector('#addUserDialog').close();
                            document.querySelector('#TimeoutDb').open();
                        }
                    },
                    success: function (data) {
                        document.querySelector('#addDBDialog').close();
                        document.querySelector('#OnePDialog').open();
                        self.AddUserMsg(data[0]);
                        return self;
                    }
    
                })
            
        }

        self.delUserDlg = function (){
            let valid = self._checkValidationGroup("delUser");
            if (valid) {
            document.querySelector('#DeleteUser').open();
            }
        }

        self.CloseOkDltUser =  function (event) {
            document.querySelector('#DeleteUser').close();
        };

        self.AddUserMsgOKClose = function (event) {
                     self.onepUName(''),
                    self.onepPasswd(''),
                    self.currentRole(''),
                    self.currentProtocol(''),
                    self.onePHost(''),
                    self.onepPort(),
            document.querySelector('#OnePDialog').close();
        };

        //console.log(self);


            self.connected = function () { 
                if (sessionStorage.getItem("userName")==null) {
                    oj.Router.rootInstance.go('signin');
                }
                else
                {
                  app.onAppSuccess();
                  self.onepUName('');
                  self.onepPasswd('');
                  self.currentRole('');
                  self.depOption('ld');
                  self.onePHost('');
                  self.onepPort(null); 
                  getDB();
                }
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
    return  chkTblViewModel;
}
);
