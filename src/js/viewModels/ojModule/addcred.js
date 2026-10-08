define([
  "knockout",
  "jquery",
  "appController",
  "ojs/ojasyncvalidator-regexp",
  "ojs/ojarraydataprovider",
  "ojs/ojarraytreedataprovider",
  "ojs/ojbutton",
  "ojs/ojinputtext",
  "ojs/ojselectcombobox",
  "ojs/ojdialog",
  "ojs/ojformlayout",
  "ojs/ojtreeview",
  "ojs/ojvalidationgroup",
  "ojs/ojprogress-circle",
  "ojs/ojfilepicker",
  "ojs/ojtable",
], function (
  ko,
  $,
  app,
  AsyncRegExpValidator,
  ArrayDataProvider,
  ArrayTreeDataProvider,
) {
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
      self.serverName = ko.observable();
      self.dbName = ko.observable();    
      self.edServerName = ko.observable();
      self.edDbName = ko.observable();
      self.onepDepUrl = ko.observable();

      self.buttonValue = ko.observable("add");
      self.dombuttonValue = ko.observable("existDom");
      self.domName = ko.observable();
      self.aliasName = ko.observable();
      self.deluser = ko.observable("Oracle");
      self.credstoreCheck = ko.observable();
      self.MasterKeyList = ko.observableArray([]);
      self.MasterKeyChilden = ko.observableArray([]);
      self.succMsgMasterKey = ko.observableArray([]);
      self.menuActionItem = ko.observable();
      self.CancelBehaviorOpt = ko.observable("icon");
      self.credStoreMsg = ko.observable();

      self.credValues = ko.observableArray([
        { id: "add", label: "add" },
        { id: "edit", label: "edit" },
        { id: "del", label: "del" },
      ]);

      self._checkValidationGroup = (value) => {
        var tracker = document.getElementById(value);
        if (tracker.valid === "valid") {
          return true;
        } else {
          // show messages on all the components
          // that have messages hidden.
          tracker.showMessages();
          tracker.focusOn("@firstInvalidShown");
          return false;
        }
      };

      self.regExpValidator = new AsyncRegExpValidator({
        pattern: "[a-zA-Z0-9,.'-]{1,}",
        hint: "1 or more letters",
        messageDetail: "You must enter at least 1 letter",
      });

      function getDomains() {
        // ...reset observables...
        self.username1([]);
        self.othdom([]);
        self.aliasname1([]);
        self.domname1([]);
        self.selectedAliascategory("");
        self.selectedUsercategory("");
        self.aliasName("");
        self.uName("");
        self.uPasswd("");
        self.uRepPass("");
        self.deluser("");
        self.valdom("");
        self.serverName("");
        self.dbName("");
        self.edServerName("");
        self.edDbName("");

        $.ajax({
          url: self.DepName() + "/api/v2/vault/info/all",
          type: "GET",
          dataType: "json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Refreshing Secure Vault",
          error: function (xhr, textStatus, errorThrown) {
            app.showGlobalError(
              app.extractErrorMessage(xhr),
              "Secure Vault Error",
            );
          },
          success: function (data) {
            for (var i = 0; i < data[1].length; i++) {
              self.othdom.push({
                label: data[1][i].value,
                value: data[1][i].value,
              });
            }
            self.aliasname1(data[4]);
            for (var i = 0; i < data[2].length; i++) {
              self.domname1.push({ label: data[2][i], value: data[2][i] });
            }
            for (var i = 0; i < data[0].length; i++) {
              self.username1.push({
                label: data[0][i].alias,
                value: data[0][i].alias,
                children: [
                  { label: data[0][i].uname, value: data[0][i].uname },
                ],
              });
            }
            return self;
          },
        });
      }

      self.domname1DP = new ArrayDataProvider(self.othdom, {
        keyAttributes: "value",
      });

      function getMasterKeys() {
        self.MasterKeyList([]);
        $.ajax({
          url: self.DepName() + "/api/v2/masterkey/all",
          type: "GET",
          dataType: "json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Loading MasterKey Wallet",
          error: function (xhr, textStatus, errorThrown) {
            app.showGlobalError(
              app.extractErrorMessage(xhr),
              "MasterKey Error",
            );
          },
          success: function (data) {
            for (var key in data[0]) {
              self.MasterKeyChilden([]);
              for (var i = 0; i < data[0][key].length; i++) {
                self.MasterKeyChilden.push({
                  label: data[0][key][i].Version,
                  value:
                    "Version " +
                    data[0][key][i].Version +
                    " (" +
                    data[0][key][i].Status +
                    ")",
                });
              }
              self.MasterKeyList.push({
                label: key,
                value: key,
                children: self.MasterKeyChilden(),
              });
            }
            self.MasterKeyList.valueHasMutated();
            return self;
          },
        });
      }

      self.MasterKeyListDP = new ArrayTreeDataProvider(self.MasterKeyList, {
        keyAttributes: "value",
      });

      self.clickAddCred = function (data, event) {
        $.ajax({
          url: self.DepName() + "/api/v2/vaultAdd",
          type: "GET",
          dataType: "json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Preparing Secure Vault",
          error: function (xhr, textStatus, errorThrown) {
            app.showGlobalError(
              app.extractErrorMessage(xhr),
              "Secure Vault Error",
            );
          },
          success: function (data) {
            self.addcred(data[0]);
            self.credStoreMsg("Add Secure Vault");
            document.querySelector("#credStoreDialog").open();
            return self;
          },
        });
      };
      self.clickAddMasterKey = function (event, data) {
        self.MasterKeyList([]);
        $.ajax({
          url: self.DepName() + "/api/v2/masterkey/recreate",
          type: "POST",
          data: JSON.stringify({ menuAction: "add " }),
          dataType: "json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Adding Wallet",
          error: function (xhr, textStatus, errorThrown) {
            app.showGlobalError(
              app.extractErrorMessage(xhr),
              "MasterKey Error",
            );
          },
          success: function (data) {
            self.addcred(data[0]);
            self.credStoreMsg("Add Wallet");
            $("#MKDialog").ojDialog("open");
            return self;
          },
        });
      };

      function credstoreExists() {
        self.credstoreCheck("");
        $.ajax({
          url: self.DepName() + "/api/v2/vault/check",
          type: "GET",
          dataType: "json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Refreshing Secure Vault",
          error: function (xhr, textStatus, errorThrown) {
            app.showGlobalError(
              app.extractErrorMessage(xhr),
              "Secure Vault Error",
            );
          },
          success: function (data) {
            self.credstoreCheck(data[0]);
            return self;
          },
        });
      }

      self.onepDepList = ko.observableArray([]);
      self.onepDepName = ko.observable();

      function getOnepDep() {
        self.onepDepList([]);
        $.ajax({
          url: self.DepName() + "/api/v2/onep/dep",
          type: "GET",
          dataType: "json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          success: function (data) {
            for (var i = 0; i < data[0].length; i++) {
              self.onepDepList.push({
                label: data[0][i].dep,
                value: data[0][i].dep,
              });
            }
            self.onepDepList.valueHasMutated();
            return self;
          },
        });
      }

      self.onepDepListDP = new ArrayDataProvider(self.onepDepList, {
        keyAttributes: "value",
      });

      self.credStoreOKClose = function (event) {
        credstoreExists();
        document.querySelector("#credStoreDialog").close();
        //console.log(self)
      };

      self.leafOnly = function (itemContext) {
        return itemContext.leaf;
      };

      self.succMsgDBLogin = ko.observable();
      self.selectedMenuItem = ko.observable("(None selected yet)");
      self.selectedMenuItem1 = ko.observable(1);
      self.currentKey = null;
      self.testMenu = ko.observable();
      self.selectedKeyMenuItem1 = ko.observable(1);
      self.selectedKeyMenuItem = ko.observable("(None selected yet)");

      self.menuBeforeOpen = function (event) {
        var target = event.detail.originalEvent.target;
        var treeView = document.getElementById("treeview");
        var context = treeView.getContextByNode(target);
        self.currentKey = context ? context.key : treeView.currentItem;
        var context = treeView.getContextByNode(target);
        var parentKey = context.parentKey;
        self.selectedMenuItem1(parentKey);
      };

      self.menuKeyBeforeOpen = function (event) {
        var target = event.detail.originalEvent.target;
        var treeView = document.getElementById("keytreeview");
        var context = treeView.getContextByNode(target);
        self.currentKey = context ? context.key : treeView.currentItem;
        var context = treeView.getContextByNode(target);
        var parentKey = context.parentKey;
        self.selectedKeyMenuItem1(parentKey);
      };

      var data = data;
      var params = {
        url: "",
        type: "POST",
        data: data,
        dataType: "json",
        contentType: "application/json",
        context: self,
        error: function (e) {
          console.log(e);
        },
        success: function (data) {
          $("#addCredProgress").ojDialog("close");
          document.querySelector("#RemoteDeploymentDialog").close();
          document.querySelector("#RenewMasterKeyDialog").open();
          self.succMsgMasterKey(data[0]);
          return self;
        },
      };

      self.menuKeyAction = function (event, node, data) {
        self.menuActionItem(event.target.value);

        self.MasterKeyListDP.fetchByKeys({
          keys: new Set([self.currentKey]),
        }).then(function (e) {
          if (e.results.get(self.currentKey)) {
            self.selectedKeyMenuItem(e.results.get(self.currentKey).data.label);
            self.succMsgMasterKey([]);
            const baseUrl = self.DepName();
            const version = self.selectedKeyMenuItem();

            if (self.menuActionItem() == "info") {
              $.ajax({
                url:
                  baseUrl +
                  "/api/v2/masterkey/info/" +
                  encodeURIComponent(version),
                type: "GET",
                dataType: "json",
                context: self,
                progressMessage: "Getting Masterkey from Wallet",
                error: function (xhr, textStatus, errorThrown) {
                  app.showGlobalError(
                    app.extractErrorMessage(xhr),
                    "MasterKey Error",
                  );
                },
                success: function (data) {
                  document.querySelector("#RenewMasterKeyDialog").open();
                  self.succMsgMasterKey(data[0]);
                },
              });
            } else if (self.menuActionItem() == "renew") {
              $.ajax({
                url: baseUrl + "/api/v2/masterkey/renew",
                type: "POST",
                contentType: "application/json",
                dataType: "json",
                context: self,
                progressMessage: "Generating new MasterKey",
                error: function (xhr, textStatus, errorThrown) {
                  app.showGlobalError(
                    app.extractErrorMessage(xhr),
                    "MasterKey Error",
                  );
                },
                success: function (data) {
                  document.querySelector("#RemoteDeploymentDialog").close();
                  document.querySelector("#RenewMasterKeyDialog").open();
                  self.succMsgMasterKey(data[0]);
                },
              });
            } else if (self.menuActionItem() == "delete") {
              $.ajax({
                url:
                  baseUrl + "/api/v2/masterkey/" + encodeURIComponent(version),
                type: "DELETE",
                dataType: "json",
                context: self,
                progressMessage: "Deleting Masterkey",
                error: function (xhr, textStatus, errorThrown) {
                  app.showGlobalError(
                    app.extractErrorMessage(xhr),
                    "MasterKey Error",
                  );
                },
                success: function (data) {
                  document.querySelector("#RemoteDeploymentDialog").close();
                  document.querySelector("#RenewMasterKeyDialog").open();
                  self.succMsgMasterKey(data[0]);
                },
              });
            } else if (self.menuActionItem() == "purge") {
              $.ajax({
                url: baseUrl + "/api/v2/masterkey/wallet/purge",
                type: "DELETE",
                dataType: "json",
                context: self,
                progressMessage: "Purging Wallet",
                error: function (xhr, textStatus, errorThrown) {
                  app.showGlobalError(
                    app.extractErrorMessage(xhr),
                    "MasterKey Error",
                  );
                },
                success: function (data) {
                  document.querySelector("#RemoteDeploymentDialog").close();
                  document.querySelector("#RenewMasterKeyDialog").open();
                  self.succMsgMasterKey(data[0]);
                },
              });
            } else if (self.menuActionItem() == "deploy") {
              getOnepDep();
              document.querySelector("#RmtDeploymentDialog").open();
            }
          }
        });
      };
      self.DeployWallet = function (event, data) {
        self.onepDepUrl("");
        $.ajax({
          url: self.DepName() + "/api/v2/onep/depurl",
          type: "POST",
          contentType: "application/json",
          data: JSON.stringify({ dep: self.onepDepName() }),
          dataType: "json",
          timeout: parseInt(sessionStorage.getItem("timeInetrval"), 10),
          context: self,
          progressMessage: "Resolving Deployment",
          error: function (xhr, textStatus, errorThrown) {
            app.showGlobalError(
              app.extractErrorMessage(xhr),
              "Deployment Error",
            );
          },
          success: function (data) {
            self.onepDepUrl(data[0]);
            document.querySelector("#RmtDeploymentDialog").close();

            $.ajax({
              url: self.DepName() + "/api/v2/masterkey/deploy",
              type: "POST",
              contentType: "application/json",
              data: JSON.stringify({
                menuAction: self.menuActionItem(),
                dep_url: self.onepDepUrl(),
              }),
              dataType: "json",
              context: self,
              progressMessage: "Deploying Wallet",
              error: function (xhr, textStatus, errorThrown) {
                app.showGlobalError(
                  app.extractErrorMessage(xhr),
                  "Deployment Error",
                );
              },
              success: function (data) {
                document.querySelector("#RemoteDeploymentDialog").close();
                document.querySelector("#RenewMasterKeyDialog").open();
                self.succMsgMasterKey(data[0]);
                return self;
              },
            });
            return self;
          },
        });
      };

      self.MasterKeyOKClose = function (event) {
        if (self.menuActionItem() != "info") {
          getMasterKeys();
        }
        $("#MKDialog").ojDialog("close");
        document.querySelector("#RenewMasterKeyDialog").close();
      };

      self.menuAction = function (event, node, data) {
        self.data
          .fetchByKeys({ keys: new Set([self.currentKey]) })
          .then(function (e) {
            if (e.results.get(self.currentKey)) {
              self.selectedMenuItem(e.results.get(self.currentKey).data.value);
              $.ajax({
                url: self.DepName() + "/api/v2/vault/testdblogin",
                type: "POST",
                contentType: "application/json",
                data: JSON.stringify({
                  domain: self.selectedMenuItem1(),
                  alias: self.selectedMenuItem(),
                }),
                dataType: "json",
                timeout: sessionStorage.getItem("timeInetrval"),
                context: self,
                progressMessage: "Testing Database Connection",
                error: function (xhr, textStatus, errorThrown) {
                  app.showGlobalError(
                    app.extractErrorMessage(xhr),
                    "Connection Test Failed",
                  );
                },
                success: function (data) {
                  document.querySelector("#testDBLoginDialog").open();
                  self.succMsgDBLogin(data[0]);
                  return self;
                },
              });
            }
          });
      };
      self.DBLoginOKClose = function (event) {
        document.querySelector("#testDBLoginDialog").close();
      };

      self.selectedDomCategory = ko.observable();
      self.selectedDomCategoryExist = ko.observable("SkyliftAI");
      self.selectedAliascategory = ko.observable();
      self.selectedUsercategory = ko.observable();
      self.aliascategories = ko.observableArray([]);
      self.unamecategories = ko.observableArray([]);

      let getAliascategories = (category) => {
        let found = self.aliasname1().find((c) => c.value === category);
        return found ? found.children : null;
      };
      let getUnamecategories = (category) => {
        let found = self.username1().find((c) => c.value === category);
        return found ? found.children : null;
      };
      self.domSelectionChanged = (event) => {
        self.selectedAliascategory("");
        self.selectedUsercategory("");
        let children = getAliascategories(event.detail.value);
        self.aliascategories(children);
      };
      self.aliascategoriesDP = new ArrayTreeDataProvider(self.aliascategories, {
        keyAttributes: "value",
      });

      self.aliasSelectionChanged = (event) => {
        self.selectedUsercategory("");
        self.edServerName("");
        self.edDbName("");
        let children = getUnamecategories(event.detail.value);
        self.unamecategories(children);

        if (!event.detail.value) return;
        $.ajax({
          url: self.DepName() + "/api/v2/select-db-det",
          type: "POST",
          contentType: "application/json",
          data: JSON.stringify({ dbname: event.detail.value }),
          dataType: "json",
          context: self,
          success: function (data) {
            if (data[0] && data[0].length > 0) {
              self.edServerName(data[0][0].servicename || "");
              self.edDbName(data[0][0].sourcedb || "");
            }
          },
        });
      };
      self.unamecategoriesDP = new ArrayTreeDataProvider(self.unamecategories, {
        keyAttributes: "value",
      });

      self.data = new ArrayTreeDataProvider(self.aliasname1, {
        keyAttributes: "value",
      });

      self.OthDomProvider = new ArrayDataProvider(self.othdom, {
        keyAttributes: "value",
      });

      self.succMsgAddUser = ko.observable();

      self.clickAddUsr = function (data, event) {
        let valid = self._checkValidationGroup("add_user");
        if (valid) {
          let domain =
            self.dombuttonValue() === "existDom"
              ? self.selectedDomCategoryExist()
              : self.selectedDomCategory();
          $.ajax({
            url: self.DepName() + "/api/v2/vault/adduseralias",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({
              domain: domain,
              alias: self.aliasName(),
              user: self.uName(),
              passwd: self.uPasswd(),
              servicename: self.serverName(),
              dbname: self.dbName(),
            }),
            dataType: "json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: "Adding User",
            error: function (xhr, textStatus, errorThrown) {
              app.showGlobalError(
                app.extractErrorMessage(xhr),
                "Add User Failed",
              );
            },
            success: function (data) {
              document.querySelector("#addUserCredStoreDialog").open();
              self.succMsgAddUser(data[0]);
              return self;
            },
          });
        }
      };

      self.addUserOKClose = function (event) {
        getDomains();
        self.selectedDomCategory(null);
        document.querySelector("#addUserCredStoreDialog").close();
      };

      self.succMsgedUsr = ko.observable();
      self.clickEditUsr = function (data, event) {
        let valid = self._checkValidationGroup("edit_user");
        if (valid) {
          $.ajax({
            url: self.DepName() + "/api/v2/vault/edituseralias",
            type: "PUT",
            contentType: "application/json",
            data: JSON.stringify({
              domain: self.selectedDomCategory(),
              alias: self.selectedAliascategory(),
              user: self.selectedUsercategory(),
              passwd: self.uRepPass(),
              servicename: self.edServerName(),
              dbname: self.edDbName(),
            }),
            dataType: "json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: "Updating User",
            error: function (xhr, textStatus, errorThrown) {
              app.showGlobalError(
                app.extractErrorMessage(xhr),
                "Update User Failed",
              );
            },
            success: function (data) {
              document.querySelector("#edUserCredStoreDialog").open();
              self.succMsgedUsr(data[0]);
              return self;
            },
          });
        }
      };
      self.edUserOKClose = function (event) {
        getDomains();
        self.selectedDomCategory(null);
        document.querySelector("#edUserCredStoreDialog").close();
      };

      self.openDelSuppLog = function () {
        let valid = self._checkValidationGroup("delete_user");
        if (valid) {
          document.querySelector("#DeleteUser").open();
        }
      };
      self.CloseOkDlt = function (event) {
        document.querySelector("#DeleteUser").close();
      };

      self.succMsgDelUsr = ko.observable();

      self.clickDelUsr = function (data, event) {
        document.querySelector("#DeleteUser").close();
        $.ajax({
          url: self.DepName() + "/api/v2/vault/deluseralias",
          type: "DELETE",
          contentType: "application/json",
          data: JSON.stringify({
            domain: self.selectedDomCategory(),
            alias: self.selectedAliascategory(),
            user: self.selectedUsercategory(),
          }),
          dataType: "json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Deleting User",
          error: function (xhr, textStatus, errorThrown) {
            app.showGlobalError(
              app.extractErrorMessage(xhr),
              "Delete User Failed",
            );
          },
          success: function (data) {
            document.querySelector("#delUserCredStoreDialog").open();
            self.succMsgDelUsr(data[0]);
            return self;
          },
        });
      };
      self.delUserOKClose = function (event) {
        getDomains();
        self.selectedDomCategory(null);
        document.querySelector("#delUserCredStoreDialog").close();
      };

      self.fileObject = null;
      self.fileName = ko.observable();
      self.succMsgBulkUploadUser = ko.observable("");
      self.succMsgBulkUploadErr = ko.observable("");
      self.bulkUploadDetails = ko.observableArray([]);
      self.bulkUploadTotal = ko.observable(0);

      self.bulkUploadFile = (event) => {
        const files = event.detail.files;
        if (files.length > 0) {
          self.fileObject = files[0];
          self.fileName(self.fileObject.name);
        }
      };

      self.clickBulkUploadUsr = async () => {
        let valid = self._checkValidationGroup("bulk_add_user");
        if (!valid) return;

        let domain =
          self.dombuttonValue() === "existDom"
            ? self.selectedDomCategoryExist()
            : self.selectedDomCategory();

        if (!self.fileObject) {
          alert("Please select an Excel file first");
          return;
        }

        try {
          const formData = new FormData();
          formData.append("file", self.fileObject);
          formData.append("domain", domain);

          $.ajax({
            url: self.DepName() + "/api/v2/vault/bulkupload",
            type: "POST",
            data: formData,
            processData: false,
            contentType: false,
            timeout: Number(sessionStorage.getItem("timeInetrval")) || 30000,
            context: self,
            progressMessage: "Uploading Users",
            error: function (xhr, textStatus, errorThrown) {
              if (textStatus === "timeout") {
                app.showGlobalError(
                  "Request timed out. Please try again.",
                  "Bulk Upload Timeout",
                );
                return;
              }
              let errorData;
              try {
                errorData = JSON.parse(xhr.responseText);
              } catch (e) {
                errorData = null;
              }
              self.succMsgBulkUploadUser(
                errorData ? errorData["title"] : "Bulk upload failed",
              );
              self.succMsgBulkUploadErr(
                errorData ? errorData.detail : app.extractErrorMessage(xhr),
              );
              document.querySelector("#bulkUploadUserCredStoreDialog").open();
            },
            success: function (data) {
              self.bulkUploadDetails([]);
              self.succMsgBulkUploadUser(data.message);
              self.bulkUploadTotal(data.total_processed || 0);
              for (var i = 0; i < data.details.length; i++) {
                self.bulkUploadDetails.push({
                  alias: data.details[i].alias,
                  userid: data.details[i].userid,
                  error: data.details[i].output,
                });
              }
              self.bulkUploadDetails.valueHasMutated();
              document.getElementById("bulkUploadUserVaultDialog").open();
              return self;
            },
          });
        } catch (err) {
          console.error("Unexpected error:", err);
          app.showGlobalError(
            "An unexpected error occurred during upload.",
            "Bulk Upload Error",
          );
        }
      };

      self.bulkUploadDetailsDP = new ArrayDataProvider(self.bulkUploadDetails, {
        keyAttributes: "alias",
      });

      self.bulkUploadUserOKClose = () => {
        document.getElementById("bulkUploadUserVaultDialog").close();
        self.fileObject = null;
        self.fileName("");

        self.bulkUploadDetails([]);
        self.bulkUploadTotal(0);
        self.succMsgBulkUploadUser("");

        const filePicker = document.querySelector("oj-file-picker");
        if (filePicker) {
          filePicker.value = null;
        }
        getDomains();
      };

      self.bulkUploadErrOKClose = () => {
        document.getElementById("bulkUploadUserCredStoreDialog").close();
      };

      self.connected = function () {
        if (sessionStorage.getItem("userName") == null) {
          oj.Router.rootInstance.go("signin");
        } else {
          app.onAppSuccess();
          getDomains(true);
          getMasterKeys(true);
          credstoreExists(true);
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
