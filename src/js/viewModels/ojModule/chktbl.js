
define(['ojs/ojcore', 'knockout', 'jquery','appController','ojs/ojknockout', 'ojs/ojarraydataprovider', 'ojs/ojarraytreedataprovider', 'ojs/ojinputtext', 'ojs/ojlabel', 'ojs/ojformlayout','ojs/ojbutton', 
        'ojs/ojlabelvalue','ojs/ojdialog', 'ojs/ojprogress-bar','ojs/ojvalidationgroup'],
        function (oj, ko, $, app, ArrayDataProvider, ArrayTreeDataProvider, keySet) {

            class chkTblViewModel {
                constructor(context) {
                var self = this;
                self.DepName = context.DepName;                
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
                self.groupValid = ko.observable();
                
                self.selectedDomCategory = ko.observable();
                self.selectedAliascategory = ko.observable();
                self.selectedUsercategory = ko.observable();
                self.aliascategories = ko.observableArray([]);
                self.unamecategories = ko.observable();
                
                self.chkptTblName = ko.observable();

                self.HBTblFrequency = ko.observable(60);
                self.HBTblRetention = ko.observable(30);
                self.HBTblPurgeFrequency = ko.observable(1);
                self.selectedHBDomCategory = ko.observable();
                self.selectedHBAliascategory = ko.observable();
                self.CancelBehaviorOpt = ko.observable('icon');
                self.TblButton = ko.observable('addTable');
                
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

                
                function getDomains() {
                    self.username1([]);
                    self.othdom([]);
                    self.aliasname1([]);
                    self.domname1([]);
                    self.selectedAliascategory('');
                    self.selectedUsercategory('');
                    self.uRepPass()
                    self.uName('');
                    self.uPasswd('');
                    self.uRepPass('');
                    self.valdom('')
                    $.ajax({
                        url: self.DepName() + "/ggcredstore",
                        type: 'GET',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#TimeoutChk').open();
                            }
                        },
                        success: function (data) {

                                             
                            for (var i = 0; i < data[1].length; i++) {
                                self.othdom.push({dom : data[1][i].value});
                                       }

                                       self.aliasname1(data[4]);


                                         for (var i = 0; i < data[2].length; i++) {
                                 self.domname1.push({label:data[2][i], value:data[2][i] }); 
                             }
    
                          for (var i = 0; i < data[0].length; i++) {
                                 self.username1.push({label:data[0][i].alias, value:data[0][i].alias,'children': [{label:data[0][i].uname,value:data[0][i].uname}] }); 
                             }

                            //console.log(self)

                            return self;
                        }
                    })
                }

                self.domname1DP = new ArrayTreeDataProvider(self.domname1, { keyAttributes: 'value' });

                
                                let getAliascategories = (category) => {
                    let found = self.aliasname1().find(c => c.value === category);
                    return found ? found.children : null;
                };

                self.aliascategoriesDP = new ArrayTreeDataProvider(self.aliascategories, { keyAttributes: 'value' });

                let getUnamecategories = (category) => {
                    let found = self.username1().find(c => c.value === category);
                    return found ? found.children : null;
                };
                this.domSelectionChanged = (event) => {
                    self.selectedAliascategory('');
                    let children = getAliascategories(event.detail.value);
                    self.aliascategories(children);
                };


                self.aliasSelectionChanged = (event) => {
                    self.selectedUsercategory('');
                    let children = getUnamecategories(event.detail.value);
                    self.unamecategories(children);
                };

                self._HELP_DEF = 'SCHEMA.TABLENAME';

                self._HELP_FRE = 'Specifies how often the heartbeat seed table and heartbeat table are updated';
                self._HELP_RET = 'Specifies when heartbeat entries older than the retention time in the history table are purged';
                self._HELP_PURGE = 'Specifies how often the purge scheduler is run to delete table entries that are older than the retention time from the heartbeat history'
                self.isFormReadonly = ko.observable(false);
                this.isRequired = ko.observable(true);
                this.checkboxValues = ko.observableArray(['required', 'helpSource', 'helpDef']);

                this.isRequired = ko.computed(function () {
                    return this.checkboxValues.indexOf('required') !== -1;
                }.bind(this));
                this.helpDef = ko.computed(function () {
                    return (this.checkboxValues.indexOf('helpDef') !== -1) ? this._HELP_DEF : null;
                }.bind(this));
                this.helpDef1 = ko.computed(function () {
                    return (this.checkboxValues.indexOf('helpDef') !== -1) ? this._HELP_FRE : null;
                }.bind(this));
                this.helpDef2 = ko.computed(function () {
                    return (this.checkboxValues.indexOf('helpDef') !== -1) ? this._HELP_RET : null;
                }.bind(this));
                this.helpDef3 = ko.computed(function () {
                    return (this.checkboxValues.indexOf('helpDef') !== -1) ? this._HELP_PURGE : null;
                }.bind(this));
                this.helpSource = ko.computed(function () {
                    return (this.checkboxValues.indexOf('helpSource') !== -1) ? this._HELP_SOURCE : null;
                }.bind(this));
            

self.AddChkptTblMsg = ko.observable();

                self.addChkptTbl = function (data, event) {
                    let valid = self._checkValidationGroup("chktbl");
                    if (valid) {
                    self.AddChkptTblMsg('');
                    document.querySelector('#addChkTblDialog').open();
                    $.ajax({
                        url: self.DepName() + "/ggaddchkpttbl",
                        type: 'POST',
                        data: JSON.stringify({
                            domain: self.selectedDomCategory(),
                            alias: self.selectedAliascategory(),
                            chkpttbl : self.chkptTblName()
                        }),
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#addChkTblDialog').close();
                                document.querySelector('#TimeoutChk').open();
                            }
                        },
                        success: function (data) {
                            document.querySelector('#addChkTblDialog').close();
                            document.querySelector('#ChkptTblDialog').open();
                            self.AddChkptTblMsg(data[0]);
                            return self;
                        }

                    })
                }
                }

                self.AddChkptTblMsgOKClose = function (event) {
                    self.selectedDomCategory(''),
                    self.selectedAliascategory(''),
                    self.chkptTblName('')
                    document.querySelector('#ChkptTblDialog').close();
                };



                self.AddHBTblMsg = ko.observable();

                self.addHBTbl = function (data, event) {
                    let valid = self._checkValidationGroup("hbtbl");
                    if (valid) {
                    self.AddHBTblMsg('');
                    document.querySelector('#addHBTblDialog').open();
                    $.ajax({
                        url: self.DepName() + "/ggaddhbtbl",
                        type: 'POST',
                        data: JSON.stringify({
                            domain: self.selectedHBDomCategory(),
                            alias: self.selectedHBAliascategory(),
                            HBTblFrequency : self.HBTblFrequency(),
                            HBTblRetention : self.HBTblRetention(),
                            HBTblPurgeFrequency : self.HBTblPurgeFrequency()
                        }),
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#addHBTblDialog').close();
                                document.querySelector('#TimeoutChk').open();
                            }
                        },
                        success: function (data) {
                            document.querySelector('#addHBTblDialog').close();
                            document.querySelector('#HBTblDialog').open();
                            self.AddHBTblMsg(data[0]);
                            return self;
                        }

                    })
                }
                }

                self.AddHBTblMsgOKClose = function (event) {
                    self.selectedHBDomCategory(''),
                    self.selectedHBAliascategory(''),
                    document.querySelector('#HBTblDialog').close();
                };

                self.editHBTbl = function (data, event) {
                     let valid = self._checkValidationGroup("edTableGrp");
                     if (valid) {
                        //console.log("edit")
                    self.AddHBTblMsg('');
                    document.querySelector('#addHBTblDialog').open();
                //     $.ajax({
                //         url: self.DepName() + "/ggaddhbtbl",
                //         type: 'POST',
                //         data: JSON.stringify({
                //             domain: self.selectedHBDomCategory(),
                //             alias: self.selectedHBAliascategory(),
                //             HBTblFrequency : self.HBTblFrequency(),
                //             HBTblRetention : self.HBTblRetention(),
                //             HBTblPurgeFrequency : self.HBTblPurgeFrequency()
                //         }),
                //         dataType: 'json',
                //         timeout: sessionStorage.getItem("timeInetrval"),
                //         context: self,
                //         error: function (xhr, textStatus, errorThrown) {
                //             if(textStatus == 'timeout' || textStatus == 'error'){
                //                 document.querySelector('#addHBTblDialog').close();
                //                 document.querySelector('#TimeoutChk').open();
                //             }
                //         },
                //         success: function (data) {
                //             document.querySelector('#addHBTblDialog').close();
                //             document.querySelector('#HBTblDialog').open();
                //             self.AddHBTblMsg(data[0]);
                //             return self;
                //         }

                //     })
                 }
                }

                self.delHBTbl = function (data, event) {
                    //console.log("dlt")
                    document.querySelector('#DeleteTable').close();
                     self.AddHBTblMsg('');
                     document.querySelector('#HBTblDialog').open();
                     //document.querySelector('#addHBTblDialog').open();
                //     $.ajax({
                //         url: self.DepName() + "/ggaddhbtbl",
                //         type: 'POST',
                //         data: JSON.stringify({
                //             domain: self.selectedHBDomCategory(),
                //             alias: self.selectedHBAliascategory()
                //         }),
                //         dataType: 'json',
                //         timeout: sessionStorage.getItem("timeInetrval"),
                //         context: self,
                //         error: function (xhr, textStatus, errorThrown) {
                //             if(textStatus == 'timeout' || textStatus == 'error'){
                //                 document.querySelector('#addHBTblDialog').close();
                //                 document.querySelector('#TimeoutChk').open();
                //             }
                //         },
                //         success: function (data) {
                //             document.querySelector('#addHBTblDialog').close();
                //             document.querySelector('#HBTblDialog').open();
                //             self.AddHBTblMsg(data[0]);
                //             return self;
                //         }

                //     })
                }

                self.delUserDlg = function (){
                    let valid = self._checkValidationGroup("delTableGrp");
                    if (valid) {
                    document.querySelector('#DeleteTable').open();
                    }
                }
        
                self.CloseOkDltTbl =  function (event) {
                    document.querySelector('#DeleteTable').close();
                };


                //console.log(self);

                self.connected = function () { 
                    if (sessionStorage.getItem("userName")==null) {
                        oj.Router.rootInstance.go('signin');
                    }
                    else
                    {
                      app.onAppSuccess();
                      getDomains();
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
