define([
  "ojs/ojcore",
  "knockout",
  "jquery",
  "appController",
  "ojs/ojarraydataprovider",
  "ojs/ojconverter-number",
  "ojs/ojknockout",
  "ojs/ojselectsingle",
  "ojs/ojinputtext",
  "ojs/ojlabel",
  "ojs/ojformlayout",
  "ojs/ojbutton",
  "ojs/ojlabelvalue",
  "ojs/ojdialog",
  "ojs/ojprogress-bar",
  "ojs/ojradioset",
  "ojs/ojinputnumber",
  "ojs/ojvalidationgroup",
  "oj-c/buttonset-single",
  "oj-c/input-text",
  "oj-c/input-number",
  "oj-c/input-password",
  "oj-c/select-single",
  "oj-c/button",
], function (oj, ko, $, app, ArrayDataProvider, NumberConverter) {
  class chkTblViewModel {
    constructor(context) {
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
      self.depOption = ko.observable("ld");
      self.onePHost = ko.observable();
      self.onepPort = ko.observable();
      self.onepUName = ko.observable();
      self.onepPasswd = ko.observable();
      self.groupValid = ko.observable();
      self.CancelBehaviorOpt = ko.observable("icon");

      self.dbButton = ko.observable("addDB");
      self.userButton = ko.observable("addUser");
      self.username = ko.observable();
      self.dbDepurl = ko.observable();
      self.username(sessionStorage.getItem("userName"));
      self.userRole = ko.observable();
      self.userRole(sessionStorage.getItem("userRole"));

      self._HELP_DBService = "hostname.domainname:dbport/dbservice";

      self._HELP_Role = "OnePlace User Role";

      self._HELP_SOURCE = "Additional information about this field";
      self._HELP_DEF = "Remote OneP deployment connection details";

      self.onepDepName = ko.observable();

      self.onepDepList = ko.observableArray([]);

      self.dbItems = [
        { label: "Add DB", value: "addDB" },
        { label: "Edit DB", value: "editDB" },
        { label: "Delete DB", value: "delDB" },
      ];

      self.userItems = [
        { label: "Add User", value: "addUser" },
        { label: "Edit User", value: "editUser" },
      ];

      if (self.userRole() == "admin") {
        self.userItems.push({ label: "Delete User", value: "delUser" });
      }

      self.getOnepDep = function () {
        self.onepDepList([]);
        $.ajax({
          url: self.DepName() + "/api/v2/onep/dep",
          type: "GET",
          dataType: "json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Fetching deployment list",
          error: function (xhr, textStatus, errorThrown) {
            app.showGlobalError(
              app.extractErrorMessage(xhr),
              "Deployment List Error",
            );
          },
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
      };

      self.onepDepListDP = new ArrayDataProvider(self.onepDepList, {
        keyAttributes: "value",
      });

      self.getOnepDepUrl = () => {
        $.ajax({
          url: self.DepName() + "/api/v2/onep/depurl",
          type: "POST",
          contentType: "application/json",
          data: JSON.stringify({
            dep: self.onepDepName(),
          }),
          dataType: "json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Resolving deployment URL",
          error: function (xhr, textStatus, errorThrown) {
            app.showGlobalError(
              app.extractErrorMessage(xhr),
              "Deployment Error",
            );
          },
          success: function (data) {
            self.dbDepurl(data[0]);
            return self;
          },
        });
      };
      self.isFormReadonly = ko.observable(false);
      self.isRequired = ko.observable(true);
      self.checkboxValues = ko.observableArray([
        "required",
        "helpSource",
        "helpDef",
      ]);

      self.isRequired = ko.computed(function () {
        return self.checkboxValues.indexOf("required") !== -1;
      });
      self.helpDBService = ko.computed(function () {
        return self.checkboxValues.indexOf("helpDef") !== -1
          ? self._HELP_DBService
          : null;
      });
      self.helpRole = ko.computed(function () {
        return self.checkboxValues.indexOf("helpDef") !== -1
          ? self._HELP_Role
          : null;
      });
      self.helpSource = ko.computed(function () {
        return self.checkboxValues.indexOf("helpSource") !== -1
          ? self._HELP_SOURCE
          : null;
      });

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

      self.DBDet = ko.observableArray([]);
      self.currentDB = ko.observable();

      function getDB() {
        self.DBDet([]);
        $.ajax({
          url: self.DepName() + "/api/v2/db-det",
          type: "GET",
          dataType: "json",
          context: self,
          progressMessage: "Fetching database list",
          error: function (xhr, textStatus, errorThrown) {
            app.showGlobalError(
              app.extractErrorMessage(xhr),
              "Database List Error",
            );
          },
          success: function (data) {
            for (var i = 0; i < data[0].length; i++) {
              self.DBDet.push({
                value: data[0][i].dbname,
                label: data[0][i].dbname,
              });
            }
          },
        });
      }

      self.DBDetDP = new ArrayDataProvider(self.DBDet, {
        keyAttributes: "value",
      });
      self.dialogTitle = ko.observable();

      var dbOpMessages = {
        addDB: "Adding database",
        editDB: "Updating database",
        delDB: "Deleting database",
      };

      self.addDB = function (data, event) {
        let valid = self._checkValidationGroup("dbcred");
        if (valid) {
          self.AddDBMsg(null);
          $.ajax({
            url: self.DepName() + "/api/v2/db/conn",
            type: "POST",
            data: JSON.stringify({
              dbname: self.dbname(),
              username: self.adduname(),
              passwd: self.addupasswd(),
              servicename: self.addservicename(),
              dbButton: self.dbButton(),
            }),
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage:
              dbOpMessages[self.dbButton()] || "Updating database",
            error: function (xhr, textStatus, errorThrown) {
              app.showGlobalError(
                app.extractErrorMessage(xhr),
                "Database Error",
              );
            },
            success: function (data) {
              self.dialogTitle("Add CredentialStore User");
              document.querySelector("#DBDialog").open();
              self.AddDBMsg(data[0]);
              getDB();
              return self;
            },
          });
        }
      };

      self.editDB = function (data, event) {
        let valid = self._checkValidationGroup("editcred");
        if (valid) {
          self.AddDBMsg(null);
          $.ajax({
            url: self.DepName() + "/api/v2/db/conn",
            type: "PUT",
            data: JSON.stringify({
              dbname: self.currentDB(),
              username: self.eduname(),
              passwd: self.edupasswd(),
              servicename: self.edservicename(),
              dbButton: self.dbButton(),
            }),
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage:
              dbOpMessages[self.dbButton()] || "Updating database",
            error: function (xhr, textStatus, errorThrown) {
              app.showGlobalError(
                app.extractErrorMessage(xhr),
                "Database Error",
              );
            },
            success: function (data) {
              self.dialogTitle("Edit CredentialStore User");
              document.querySelector("#DBDialog").open();
              self.AddDBMsg(data[0]);
              getDB();
              return self;
            },
          });
        }
      };

      self.delDB = function (data, event) {
        let valid = self._checkValidationGroup("delcred");
        if (valid) {
          self.AddDBMsg(null);
          document.querySelector("#DeleteDb").close();
          $.ajax({
            url: self.DepName() + "/api/v2/db/conn",
            type: "DELETE",
            data: JSON.stringify({
              dbname: self.currentDB(),
              username: self.eduname(),
              servicename: self.edservicename(),
              dbButton: self.dbButton(),
            }),
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage:
              dbOpMessages[self.dbButton()] || "Updating database",
            error: function (xhr, textStatus, errorThrown) {
              app.showGlobalError(
                app.extractErrorMessage(xhr),
                "Database Error",
              );
            },
            success: function (data) {
              self.dialogTitle("Delete CredentialStore User");
              document.querySelector("#DBDialog").open();
              self.AddDBMsg(data[0]);
              getDB();
              return self;
            },
          });
        }
      };

      self.valueChangedHandler = function (data, event) {
        if (self.currentDB() == null) return;
        $.ajax({
          url: self.DepName() + "/api/v2/select-db-det",
          type: "POST",
          data: JSON.stringify({
            dbname: self.currentDB(),
          }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Fetching database details",
          error: function (xhr, textStatus, errorThrown) {
            app.showGlobalError(
              app.extractErrorMessage(xhr),
              "Database Details Error",
            );
          },
          success: function (data) {
            if (data[0].length > 0) {
              self.eduname(data[0][0].user);
              self.edservicename(data[0][0].servicename);
            }
            return self;
          },
        });
      };
      self.delDBDlg = function () {
        let valid = self._checkValidationGroup("delcred");
        if (valid) {
          document.querySelector("#DeleteDb").open();
        }
      };

      self.CloseOkDlt = function (event) {
        self.currentDB(null);
        self.eduname(null);
        self.edservicename(null);
        document.querySelector("#DeleteDb").close();
      };

      self.AddDBMsgOKClose = function (event) {
        self.dbname(null);
        self.adduname(null);
        self.addupasswd(null);
        self.addservicename(null);
        self.currentDB(null);
        self.eduname(null);
        self.edupasswd(null);
        self.edservicename(null);
        document.querySelector("#DBDialog").close();
      };

      self.uname = ko.observable();
      self.upasswd = ko.observable();
      self.role = ko.observable();
      self.AddUserMsg = ko.observable();

      // NOTE: isFormReadonly / isRequired / checkboxValues were already
      // declared above -- removed the duplicate re-declaration here to
      // avoid silently discarding the first computed observables.
      self.helpDef = ko.computed(function () {
        return self.checkboxValues.indexOf("helpDef") !== -1
          ? self._HELP_DEF
          : null;
      });
      self.currentRole = ko.observable();
      var onepRoles = [
        { label: "Admin", value: "admin" },
        { label: "Data Operator", value: "dataoper" },
        { label: "Reader", value: "reader" },
      ];
      self.OneRoleDP = new ArrayDataProvider(onepRoles, {
        keyAttributes: "value",
      });

      self.currentProtocol = ko.observable("http");
      self.onepProtocol = [
        { value: "http", label: "HTTP" },
        { value: "https", label: "HTTPS" },
      ];
      self.onepProtocolDP = new ArrayDataProvider(self.onepProtocol, {
        keyAttributes: "value",
      });

      self.decimalHalfDownConverter = new NumberConverter.IntlNumberConverter({
        style: "decimal",
        roundingMode: "HALF_DOWN",
        maximumFractionDigits: 0,
        useGrouping: false,
      });

      // NOTE: removed a dead if/else block here that built a `parameter`
      // JSON string on every ViewModel construction but never used it
      // anywhere (the real request bodies are built inline inside
      // addUser/editUser/delUser below).

      self.usrUpdateMsg = ko.observable();

      var userOpMessages = {
        add: "Adding user",
        edit: "Updating user",
        del: "Deleting user",
      };

      self.addUser = function (data, event) {
        let valid = self._checkValidationGroup("add_user");
        if (valid) {
          self.AddUserMsg(null);
          $.ajax({
            url: self.DepName() + "/api/v2/onep/conn",
            type: "POST",
            data: JSON.stringify({
              onepOps: "add",
              user: self.onepUName(),
              passwd: self.onepPasswd(),
              role: self.currentRole(),
              dep_type: self.depOption(),
              dep_url:
                self.currentProtocol() +
                "://" +
                self.onePHost() +
                ":" +
                self.onepPort(),
            }),
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: userOpMessages["add"],
            error: function (xhr, textStatus, errorThrown) {
              app.showGlobalError(app.extractErrorMessage(xhr), "User Error");
            },
            success: function (data) {
              self.usrUpdateMsg("Add MigDB User");
              document.querySelector("#OnePDialog").open();
              self.AddUserMsg(data[0]);
              return self;
            },
          });
        }
      };

      self.editUser = function (data, event) {
        let valid = self._checkValidationGroup("editUser");
        if (valid) {
          self.AddUserMsg(null);
          $.ajax({
            url: self.DepName() + "/api/v2/onep/conn",
            type: "POST",
            data: JSON.stringify({
              onepOps: "edit",
              user: self.username(),
              passwd: self.onepPasswd(),
              dep_url: self.dbDepurl(),
              dep: self.onepDepName(),
              dep_type: self.depOption(),
            }),
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: userOpMessages["edit"],
            error: function (xhr, textStatus, errorThrown) {
              app.showGlobalError(app.extractErrorMessage(xhr), "User Error");
            },
            success: function (data) {
              self.usrUpdateMsg("MigDB User Update");
              document.querySelector("#OnePDialog").open();
              self.AddUserMsg(data[0]);
              return self;
            },
          });
        }
      };

      self.delUser = function (data, event) {
        document.querySelector("#DeleteUser").close();
        self.AddUserMsg(null);
        $.ajax({
          url: self.DepName() + "/api/v2/onep/conn",
          type: "POST",
          data: JSON.stringify({
            onepOps: "del",
            user: self.onepUName(),
            dep_type: self.depOption(),
          }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: userOpMessages["del"],
          error: function (xhr, textStatus, errorThrown) {
            app.showGlobalError(app.extractErrorMessage(xhr), "User Error");
          },
          success: function (data) {
            self.usrUpdateMsg("MigDB User Delete");
            document.querySelector("#OnePDialog").open();
            self.AddUserMsg(data[0]);
            return self;
          },
        });
      };

      self.delUserDlg = function () {
        let valid = self._checkValidationGroup("delUser");
        if (valid) {
          document.querySelector("#DeleteUser").open();
        }
      };

      self.CloseOkDltUser = function (event) {
        document.querySelector("#DeleteUser").close();
      };

      self.AddUserMsgOKClose = function (event) {
        self.onepUName(null);
        self.onepPasswd(null);
        self.currentRole(null);
        self.currentProtocol(null);
        self.onePHost(null);
        self.onepPort(null);
        document.querySelector("#OnePDialog").close();
      };

      //console.log(self);

      self.connected = function () {
        if (sessionStorage.getItem("userName") == null) {
          oj.Router.rootInstance.go("signin");
        } else {
          app.onAppSuccess();
          self.onepUName(null);
          self.getOnepDep();
          self.onepPasswd(null);
          self.currentRole(null);
          self.depOption("ld");
          self.onePHost(null);
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
  return chkTblViewModel;
});
