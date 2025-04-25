define(['knockout', 'jquery', 'appController', 'ojs/ojarraydataprovider', 'ojs/ojarraytreedataprovider', 'ojs/ojbutton', 
        'ojs/ojinputtext', 'ojs/ojselectcombobox', 'ojs/ojdialog', 'ojs/ojformlayout', 'ojs/ojtreeview','ojs/ojvalidationgroup'],
  function (ko, $, app, ArrayDataProvider, ArrayTreeDataProvider) {

    class addcredViewModel {
      constructor(context) {
      var self = this;
      self.DepName = context.DepName;
      self.addcred = ko.observableArray([]);
      self.groupValid = ko.observable();

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
      self.onepDepUrl = ko.observable();

      self.buttonValue = ko.observable('add');
      self.dombuttonValue = ko.observable('existDom');
      self.domName = ko.observable();
      self.aliasName = ko.observable();
      self.deluser = ko.observable('Oracle');
      self.credstoreCheck = ko.observable();
      self.MasterKeyList = ko.observableArray([]);
      self.MasterKeyChilden = ko.observableArray([]);
      self.succMsgMasterKey = ko.observableArray([]);
      self.menuActionItem = ko.observable();
      self.CancelBehaviorOpt = ko.observable('icon');
      self.credStoreMsg = ko.observable();

      self.credValues = ko.observableArray([
        { id: 'add', label: 'add' },
        { id: 'edit', label: 'edit' },
        { id: 'del', label: 'del' }
      ]);

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
        self.aliasName('');
        self.uRepPass()
        self.uName('');
        self.uPasswd('');
        self.uRepPass('');
        self.deluser('');
        self.valdom('');
        $.ajax({
          url: self.DepName() + "/ggcredstore",
          type: 'GET',
          dataType: 'json',
          timeout: 10000,
                error: function (xhr, textStatus, errorThrown) {
                  //console.log(textStatus)
                    if(textStatus == 'timeout' || textStatus == 'error'){
                        document.querySelector('#TimeoutCred').open();
                    }
                },
          success: function (data) {
            //console.log(data)

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


      function getMasterKeys() {
        self.MasterKeyList([]);
        $.ajax({
          url: self.DepName() + "/ggmasterkey",
          type: 'GET',
          dataType: 'json',
          timeout: sessionStorage.getItem("timeInetrval"),
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                        document.querySelector('#TimeoutCred').open();
                    }
                },
          success: function (data) {

            for (var key in data[0]) {
              self.MasterKeyChilden([]);
              for (var i = 0; i < data[0][key].length; i++) {
                self.MasterKeyChilden.push({ 'label': data[0][key][i].Version, value: 'Version ' + data[0][key][i].Version + ' (' + data[0][key][i].Status + ')' })
              }
              self.MasterKeyList.push({ 'label': key, 'value': key, "children": self.MasterKeyChilden() });
            }

            self.MasterKeyList.valueHasMutated();
            return self;
          }
        })
      }

      self.MasterKeyListDP = new ArrayTreeDataProvider(self.MasterKeyList, { keyAttributes: 'value' });

      self.clickAddCred = function (data, event) {
        $.ajax({
          url: self.DepName() + "/ggaddcredstore",
          type: 'GET',
          dataType: 'json',

          timeout: sessionStorage.getItem("timeInetrval"),
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                        document.querySelector('#TimeoutCred').open();
                    }
                },
          success: function (data) {
            self.addcred(data[0]);
            document.querySelector('#credStoreDialog').open();
            //console.log(self)
            return self;
          }
        })
      };

      self.clickAddMasterKey =  function (event,data) {
        self.MasterKeyList([]);
      $.ajax({
        url: self.DepName() + "/ggmasterkey",
        type: 'POST',
        data: JSON.stringify({
          menuAction : 'add ',
        }),
        dataType: 'json',
        timeout: sessionStorage.getItem("timeInetrval"),
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                        document.querySelector('#TimeoutCred').open();
                    }
                },
        success: function (data) {
          self.addcred(data[0]);
          document.querySelector('#credStoreDialog').open();
          getMasterKeys();
          return self;
        }
      })
    }

      function credstoreExists() {
        self.credstoreCheck('');
        $.ajax({
          url: self.DepName() + "/credstorecheck",
          type: 'GET',
          dataType: 'json',
          timeout: sessionStorage.getItem("timeInetrval"),
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                        document.querySelector('#TimeoutCred').open();
                    }
                },
          success: function (data) {
            self.credstoreCheck(data[0]);
            //console.log(self)
            return self;
          }
        })
      };

      self.onepDepList = ko.observableArray([]);
      self.onepDepName = ko.observable();

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
                        document.querySelector('#TimeoutCred').open();
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


      self.credStoreOKClose = function (event) {
        credstoreExists();
        getMasterKeys();
        document.querySelector('#credStoreDialog').close();
        //console.log(self)
        return self;
      };

      self.leafOnly = function (itemContext) {
        return itemContext.leaf;
      };

      self.succMsgDBLogin = ko.observable();
      self.selectedMenuItem = ko.observable('(None selected yet)');
      self.selectedMenuItem1 = ko.observable(1);
      self.currentKey = null;
      self.testMenu = ko.observable();
      self.selectedKeyMenuItem1 = ko.observable(1);
      self.selectedKeyMenuItem = ko.observable('(None selected yet)');

      self.menuBeforeOpen = function (event) {
        var target = event.detail.originalEvent.target;
        var treeView = document.getElementById('treeview');
        var context = treeView.getContextByNode(target);
        self.currentKey = context ? context.key : treeView.currentItem;
        var context = treeView.getContextByNode(target);
        var parentKey = context.parentKey;
        self.selectedMenuItem1(parentKey);
      };

      self.menuKeyBeforeOpen = function (event) {
        var target = event.detail.originalEvent.target;
        var treeView = document.getElementById('keytreeview');
        var context = treeView.getContextByNode(target);
        self.currentKey = context ? context.key : treeView.currentItem;
        var context = treeView.getContextByNode(target);
        var parentKey = context.parentKey;
        self.selectedKeyMenuItem1(parentKey);
      };


      var data = data;

      var params = {
        url: self.DepName() + "/ggmasterkeyaction",
        type: 'POST',
        data : data,
        dataType: 'json',
        context: self,
        error: function (e) {
          //console.log(e);
        },
        success: function (data) {
          document.querySelector('#RemoteDeploymentDialog').close();
          document.querySelector('#RenewMasterKeyDialog').open();
          self.succMsgMasterKey(data[0]);
          return self;
        }
      }


      self.menuKeyAction = function (event, node, data) {
        self.menuActionItem(event.target.value);
        self.MasterKeyListDP.fetchByKeys({ keys: new Set([self.currentKey]) }).then(function (e) {
          if (e.results.get(self.currentKey)) {
            self.selectedKeyMenuItem(e.results.get(self.currentKey).data.label);
            self.succMsgMasterKey([]);
            if (self.menuActionItem() == 'info') {
              params.data = JSON.stringify({
                menuAction: self.menuActionItem(),
                version: self.selectedKeyMenuItem()
              })
              $.ajax(params)
            }
            else if (self.menuActionItem() == 'renew') {
              params.data = JSON.stringify({
                menuAction: self.menuActionItem()
              })
              $.ajax(params)
            }
            else if (self.menuActionItem() == 'delete') {
              params.data = JSON.stringify({
                menuAction: self.menuActionItem(),
                version: self.selectedKeyMenuItem()
              })
              $.ajax(params)
            }
            else if (self.menuActionItem() == 'purge') {
              params.data = JSON.stringify({
                menuAction: self.menuActionItem()
              })
              $.ajax(params)
            }
            else if (self.menuActionItem() == 'deploy') {
              getOnepDep();
              document.querySelector('#RmtDeploymentDialog').open();
            }
          }
        })
      };

      self.DeployWallet = function (event,data) {
        self.onepDepUrl('');
        params.data = JSON.stringify({
          menuAction: self.menuActionItem(),
          dep_url : self.onepDepName()
        })
            $.ajax({
              url: self.DepName() + "/onepdepurl",
              type: 'POST',
              data: JSON.stringify({
                dep: self.onepDepName()
            }),
              dataType: 'json',
              timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                        document.querySelector('#TimeoutCred').open();
                    }
                },
              success: function (data) {
                  self.onepDepUrl(data[0]);
                  params.data = JSON.stringify({
                    menuAction: self.menuActionItem(),
                    dep_url : self.onepDepUrl()
                  })
                  $.ajax(params);
                  return self;
              }
      
          })
      
         };


      self.MasterKeyOKClose = function (event) {
        getMasterKeys();
        document.querySelector('#RenewMasterKeyDialog').close();
      };


      self.menuAction = function (event, node, data) {
        self.data.fetchByKeys({ keys: new Set([self.currentKey]) }).then(function (e) {
          if (e.results.get(self.currentKey)) {
            self.selectedMenuItem(e.results.get(self.currentKey).data.value);
            self.credStoreMsg("Working on it..")
            document.querySelector('#addCredProgress').open();
            $.ajax({
              url: self.DepName() + "/testdblogin",
              type: 'POST',
              data: JSON.stringify({
                domain: self.selectedMenuItem1(),
                alias: self.selectedMenuItem()
              }),
              dataType: 'json',
              timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                      document.querySelector('#addCredProgress').close();
                        document.querySelector('#TimeoutCred').open();
                    }
                },
              success: function (data) {
                document.querySelector('#addCredProgress').close();
                document.querySelector('#testDBLoginDialog').open();
                self.succMsgDBLogin(data[0]);
                return self;
              }
            })
          }
        })
      };

      self.DBLoginOKClose = function (event) {
        document.querySelector('#testDBLoginDialog').close();
      };

      self.selectedDomCategory = ko.observable();
      self.selectedDomCategoryExist = ko.observable('OracleGoldenGate');
      self.selectedAliascategory = ko.observable();
      self.selectedUsercategory = ko.observable();
      self.aliascategories = ko.observableArray([]);
      self.unamecategories = ko.observableArray([]);

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
        self.selectedUsercategory('');
        let children = getAliascategories(event.detail.value);
        self.aliascategories(children);
      };


      self.aliasSelectionChanged = (event) => {
        self.selectedUsercategory('');
        let children = getUnamecategories(event.detail.value);
        self.unamecategories(children);
      };



      self.data = new ArrayTreeDataProvider(self.aliasname1, { keyAttributes: 'value' });

      self.OthDomProvider = new ArrayDataProvider(self.othdom, { keyAttributes: 'value' });


      self.succMsgAddUser = ko.observable();

      self.clickAddUsr = function (data, event) {
        let valid = self._checkValidationGroup("add_user");
        self.credStoreMsg("Adding User")
        if (valid) {
          document.querySelector('#addCredProgress').open();
          if(self.dombuttonValue() === 'existDom'){
            var domain = self.selectedDomCategoryExist()
          }else{
            var domain = self.selectedDomCategory()
          }
        $.ajax({
          url: self.DepName() + "/ggaddusralias",
          type: 'POST',
          data: JSON.stringify({
            domain: domain,
            alias: self.aliasName(),
            user: self.uName(),
            passwd: self.uPasswd()
          }),
          dataType: 'json',
          timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                      document.querySelector('#addCredProgress').close();
                        document.querySelector('#TimeoutCred').open();
                    }
                },
          success: function (data) {
            document.querySelector('#addCredProgress').close();
            self.credStoreMsg("")
            document.querySelector('#addUserCredStoreDialog').open();
            self.succMsgAddUser(data[0]);
            return self;
          }

        })
      }
      };

      self.addUserOKClose = function (event) {
        getDomains();
        self.selectedDomCategory(null)
        document.querySelector('#addUserCredStoreDialog').close();
      };


      self.succMsgedUsr = ko.observable();
      self.clickEditUsr = function (data, event) {
        let valid = self._checkValidationGroup("edit_user");
        self.credStoreMsg("Updating User")
        if (valid) {
          document.querySelector('#addCredProgress').open();
        $.ajax({
          url: self.DepName() + "/ggeditusralias",
          type: 'POST',
          data: JSON.stringify({
            domain: self.selectedDomCategory(),
            alias: self.selectedAliascategory(),
            user: self.selectedUsercategory(),
            passwd: self.uRepPass()
          }),
          dataType: 'json',
          timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                      document.querySelector('#addCredProgress').close();
                        document.querySelector('#TimeoutCred').open();
                    }
                },
          success: function (data) {
            document.querySelector('#addCredProgress').close();
            self.credStoreMsg("")
            document.querySelector('#edUserCredStoreDialog').open();
            self.succMsgedUsr(data[0]);
            return self;
          }

        })
      }

      };

      self.edUserOKClose = function (event) {
        getDomains();
        self.selectedDomCategory(null)
        document.querySelector('#edUserCredStoreDialog').close();
      };



      self.openDelSuppLog = function (){
        let valid = self._checkValidationGroup("delete_user");
        if (valid) {
        document.querySelector('#DeleteUser').open();
        }
    }
    self.CloseOkDlt =  function (event) {
      document.querySelector('#DeleteUser').close();
  };


      self.succMsgDelUsr = ko.observable();

      self.clickDelUsr = function (data, event) {
        document.querySelector('#DeleteUser').close();
        self.credStoreMsg("Deleting User")
        document.querySelector('#addCredProgress').open();
        $.ajax({
          url: self.DepName() + "/ggdelusralias",
          type: 'POST',
          data: JSON.stringify({
            domain: self.selectedDomCategory(),
            alias: self.selectedAliascategory(),
            user: self.selectedUsercategory()
          }),
          dataType: 'json',
          timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout' || textStatus == 'error'){
                      document.querySelector('#addCredProgress').close();
                        document.querySelector('#TimeoutCred').open();
                    }
                },
          success: function (data) {
            document.querySelector('#addCredProgress').close();
            self.credStoreMsg("")
            document.querySelector('#delUserCredStoreDialog').open();
            self.succMsgDelUsr(data[0]);
            return self;
          }

        })
      };

      self.delUserOKClose = function (event) {
        getDomains();
        self.selectedDomCategory(null)
        document.querySelector('#delUserCredStoreDialog').close();
      };

      self.connected = function () {
        if (sessionStorage.getItem("userName") == null) {
          oj.Router.rootInstance.go('signin');
        }
        else {
          app.onAppSuccess();
          getDomains();
          getMasterKeys();
          credstoreExists();
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

    return addcredViewModel;

  });