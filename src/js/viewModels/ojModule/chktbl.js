define([
  "ojs/ojcore",
  "knockout",
  "jquery",
  "appController",
  "ojs/ojarraydataprovider",
  "ojs/ojarraytreedataprovider",
  "oj-c/input-text",
  "ojs/ojlabel",
  "oj-c/form-layout",
  "oj-c/button",
  "oj-c/select-single",
  "oj-c/input-number",
  "ojs/ojlabelvalue",
  "ojs/ojdialog",
  "ojs/ojprogress-bar",
  "ojs/ojvalidationgroup",
  "oj-c/buttonset-single",
  "oj-c/checkbox",
], function (oj, ko, $, app, ArrayDataProvider, ArrayTreeDataProvider, keySet) {
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

      self.isPartitioned = ko.observable(false);
      self.HBTblFrequency = ko.observable(60);
      self.HBTblRetention = ko.observable(30);
      self.HBTblPurgeFrequency = ko.observable(1);
      self.selectedHBDomCategory = ko.observable();
      self.selectedHBAliascategory = ko.observable();
      self.CancelBehaviorOpt = ko.observable("icon");
      self.TblButton = ko.observable("addTable");

      self.HBItems = [
        {
          label: "Add",
          value: "addTable",
        },
        {
          label: "Edit",
          value: "edTable",
        },
        {
          label: "Delete",
          value: "delTable",
        },
      ];

      self.targetOnlyVal = ko.observable("targetonly");
      var targetOnly = [
        { value: "source", label: "Source" },
        { value: "targetonly", label: "Uni-Directional" },
        { value: "source_target", label: "Bi-Directional" },
      ];
      self.targetOnlyDP = new ArrayDataProvider(targetOnly, {
        keyAttributes: "value",
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

      self.domainLoading = ko.observable(false);

      function getDomains() {
        self.username1([]);
        self.othdom([]);
        self.aliasname1([]);
        self.domname1([]);
        self.selectedAliascategory(null);
        self.selectedUsercategory(null);
        self.uName(null);
        self.uPasswd(null);
        self.uRepPass(null);
        self.valdom(null);
        $.ajax({
          url: self.DepName() + "/api/v2/vault/info/all",
          type: "GET",
          dataType: "json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Fetching credential domains",
          error: function (xhr, textStatus, errorThrown) {
            app.showGlobalError(
              app.extractErrorMessage(xhr),
              "Credential Domain Error",
            );
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

      self.domname1DP = new ArrayTreeDataProvider(self.domname1, {
        keyAttributes: "value",
      });

      let getAliascategories = (category) => {
        let found = self.aliasname1().find((c) => c.value === category);
        return found ? found.children : null;
      };

      self.aliascategoriesDP = new ArrayTreeDataProvider(self.aliascategories, {
        keyAttributes: "value",
      });

      let getUnamecategories = (category) => {
        let found = self.username1().find((c) => c.value === category);
        return found ? found.children : null;
      };
      this.domSelectionChanged = (event) => {
        self.selectedAliascategory(null);
        let children = getAliascategories(event.detail.value);
        self.aliascategories(children);
      };

      self.aliasSelectionChanged = (event) => {
        infoChkpt();
        self.SchemaName(null);
        self.chkptTblName(null);
        // self.selectedUsercategory(null);
        // let children = getUnamecategories(event.detail.value);
        // self.unamecategories(children);
      };

      self._HELP_DEF = "SCHEMA.TABLENAME";

      self._HELP_FRE =
        "Specifies how often the heartbeat seed table and heartbeat table are updated";
      self._HELP_RET =
        "Specifies when heartbeat entries older than the retention time in the history table are purged";
      self._HELP_PURGE =
        "Specifies how often the purge scheduler is run to delete table entries that are older than the retention time from the heartbeat history";
      self.isFormReadonly = ko.observable(false);
      this.isRequired = ko.observable(true);
      this.checkboxValues = ko.observableArray([
        "required",
        "helpSource",
        "helpDef",
      ]);

      this.isRequired = ko.computed(
        function () {
          return this.checkboxValues.indexOf("required") !== -1;
        }.bind(this),
      );
      this.helpDef = ko.computed(
        function () {
          return this.checkboxValues.indexOf("helpDef") !== -1
            ? this._HELP_DEF
            : null;
        }.bind(this),
      );
      this.helpDef1 = ko.computed(
        function () {
          return this.checkboxValues.indexOf("helpDef") !== -1
            ? this._HELP_FRE
            : null;
        }.bind(this),
      );
      this.helpDef2 = ko.computed(
        function () {
          return this.checkboxValues.indexOf("helpDef") !== -1
            ? this._HELP_RET
            : null;
        }.bind(this),
      );
      this.helpDef3 = ko.computed(
        function () {
          return this.checkboxValues.indexOf("helpDef") !== -1
            ? this._HELP_PURGE
            : null;
        }.bind(this),
      );
      this.helpSource = ko.computed(
        function () {
          return this.checkboxValues.indexOf("helpSource") !== -1
            ? this._HELP_SOURCE
            : null;
        }.bind(this),
      );

      self.CkptTblButton = ko.observable("Add");
      self.ckptItems = [
        {
          label: "Add",
          value: "Add",
        },
        {
          label: "View",
          value: "View",
        },
        {
          label: "Upgrade",
          value: "Upgrade",
        },
        {
          label: "Delete",
          value: "Delete",
        },
      ];

      self.pdbName = ko.observable(null);
      self.SchemaName = ko.observable();
      self.schemaNameList = ko.observableArray([]);

      self.suppLogSchema = function (data, event) {
        self.schemaNameList([]);
        $.ajax({
          url: self.DepName() + "/api/v2/db/supplogschema",
          type: "POST",
          data: JSON.stringify({
            dbname: self.selectedAliascategory(),
            cdbCheck: "YES",
            pdbName: self.pdbName(),
          }),
          contentType: "application/json",
          dataType: "json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Fetching schema list",
          error: function (xhr, textStatus, errorThrown) {
            app.showGlobalError(
              app.extractErrorMessage(xhr),
              "Schema List Error",
            );
          },
          success: function (data) {
            if (Array.isArray(data[0])) {
              const schemas = data[0]
                .filter(
                  (item) =>
                    item.schema_name !== null &&
                    item.schema_name !== undefined &&
                    item.schema_name.trim() !== "",
                )
                .map((item) => ({
                  label: item.schema_name,
                  value: item.schema_name,
                }));
              self.schemaNameList(schemas);
            }
            self.schemaNameList.valueHasMutated();
            return self;
          },
        });
      };

      self.schemaListDP = new ArrayDataProvider(self.schemaNameList, {
        keyAttributes: "label",
      });

      self.chkptTblArr = ko.observableArray([]);

      self.chkpttblLoading = ko.observable(false);
      function infoChkpt() {
        self.chkptTblName(null);
        self.chkptTblArr([]);
        if (!self.selectedDomCategory() || !self.selectedAliascategory())
          return;
        $.ajax({
          url: self.DepName() + "/api/v2/chkpt/info",
          type: "POST",
          contentType: "application/json",
          data: JSON.stringify({
            domain: self.selectedDomCategory(),
            alias: self.selectedAliascategory(),
          }),
          dataType: "json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Fetching checkpoint table info",
          error: function (xhr, textStatus, errorThrown) {
            app.showGlobalError(
              app.extractErrorMessage(xhr),
              "Checkpoint Table Error",
            );
          },
          success: function (data) {
            self.chkptTblArr([]);
            for (var i = 0; i < data[0].length; i++) {
              if (data[0][i]) {
                self.chkptTblArr.push({
                  label: data[0][i],
                  value: data[0][i],
                });
              }
            }
            self.chkptTblArr.valueHasMutated();
            return self;
          },
        });
      }
      self.chkptTblArrDP = new ArrayDataProvider(self.chkptTblArr, {
        keyAttributes: "value",
      });

      self.AddChkptTblMsg = ko.observable();

      self.addChkptTbl = function (data, event) {
        let valid = self._checkValidationGroup("chktbl");
        if (valid) {
          self.AddChkptTblMsg(null);

          var operation = self.CkptTblButton();
          var opMessages = {
            Add: "Adding checkpoint table",
            View: "Fetching checkpoint table details",
            Upgrade: "Upgrading checkpoint table",
            Delete: "Deleting checkpoint table",
          };
          var progressMsg =
            opMessages[operation] || "Updating checkpoint table";
          $.ajax({
            url: self.DepName() + "/api/v2/chkpt/add",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({
              domain: self.selectedDomCategory(),
              alias: self.selectedAliascategory(),
              chkpttbl: self.chkptTblName(),
              operation: self.CkptTblButton(),
            }),
            dataType: "json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: progressMsg,
            error: function (xhr, textStatus, errorThrown) {
              app.showGlobalError(
                app.extractErrorMessage(xhr),
                "Checkpoint Table Error",
              );
            },
            success: function (data) {
              document.querySelector("#ChkptTblDialog").open();
              if (self.CkptTblButton() === "View") {
                var lastMsg = data[0][data[0].length - 1];
                self.AddChkptTblMsg(lastMsg);
                return self;
              } else if (self.CkptTblButton() === "Clean") {
                var lastMsg = data[0][data[0].length - 2];
                self.AddChkptTblMsg(lastMsg);
                return self;
              }
              self.AddChkptTblMsg(data[0]);
              // getDomains();
              return self;
            },
          });
        }
      };

      self.AddChkptTblMsgOKClose = function (event) {
        (self.selectedDomCategory(null),
          self.selectedAliascategory(null),
          self.chkptTblName(null));
        document.querySelector("#ChkptTblDialog").close();
      };

      self.AddHBTblMsg = ko.observable();

      self.addHBTbl = function (data, event) {
        let valid = self._checkValidationGroup("hbtbl");
        if (valid) {
          self.AddHBTblMsg(null);
          var operation = self.TblButton();
          var opMessages = {
            addTable: "Adding heartbeat table",
            edTable: "Updating heartbeat table",
            delTable: "Deleting heartbeat table",
          };
          var progressMsg = opMessages[operation] || "Updating heartbeat table";
          $.ajax({
            url: self.DepName() + "/api/v2/heartbeat/manage",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({
              domain: self.selectedHBDomCategory(),
              alias: self.selectedHBAliascategory(),
              HBTblFrequency: self.HBTblFrequency(),
              HBTblRetention: self.HBTblRetention(),
              HBTblPurgeFrequency: self.HBTblPurgeFrequency(),
              targetOnly: self.targetOnlyVal(),
              hbTblOps: self.TblButton(),
              partitioned: self.isPartitioned(),
            }),
            dataType: "json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: progressMsg,
            error: function (xhr, textStatus, errorThrown) {
              app.showGlobalError(
                app.extractErrorMessage(xhr),
                "Heartbeat Table Error",
              );
            },
            success: function (data) {
              document.querySelector("#HBTblDialog").open();

              var rawLines = data[0];
              var parsed = rawLines.map(function (line) {
                var match = line.match(
                  /^\S+\s+\S+\s+(INFO|ERROR|WARN)\s+(\S+)\s+(.+)$/,
                );
                if (match) {
                  return { level: match[1], code: match[2], message: match[3] };
                }
                return { level: "INFO", code: "", message: line };
              });
              self.AddHBTblMsg(parsed);
              return self;
            },
          });
        }
      };
      self.AddHBTblMsgOKClose = function (event) {
        (self.selectedHBDomCategory(null),
          self.selectedHBAliascategory(null),
          document.querySelector("#HBTblDialog").close());
      };

      self.delHBTbl = function (data, event) {
        document.querySelector("#DeleteTable").close();
        self.AddHBTblMsg(null);
        document.querySelector("#HBTblDialog").open();
      };

      self.delUserDlg = function () {
        let valid = self._checkValidationGroup("delTableGrp");
        if (valid) {
          document.querySelector("#DeleteTable").open();
        }
      };

      self.CloseOkDltTbl = function (event) {
        document.querySelector("#DeleteTable").close();
      };

      //console.log(self);

      self.connected = function () {
        if (sessionStorage.getItem("userName") == null) {
          oj.Router.rootInstance.go("signin");
        } else {
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
  return chkTblViewModel;
});
