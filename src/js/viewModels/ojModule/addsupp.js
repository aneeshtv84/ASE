define([
  "ojs/ojcore",
  "knockout",
  "jquery",
  "appController",
  "ojs/ojpagingdataproviderview",
  "ojs/ojarraydataprovider",
  "ojs/ojlistdataproviderview",
  "ojs/ojarraytreedataprovider",
  "ojs/ojkeyset",
  "ojs/ojbutton",
  "ojs/ojtable",
  "ojs/ojdialog",
  "ojs/ojinputtext",
  "ojs/ojselectsingle",
  "ojs/ojprogress-bar",
  "ojs/ojtable",
  "ojs/ojhighlighttext",
  "ojs/ojpagingcontrol",
  "ojs/ojvalidationgroup",
  "ojs/ojinputsearch",
], function (
  oj,
  ko,
  $,
  app,
  PagingDataProviderView,
  ArrayDataProvider,
  ListDataProviderView,
  ArrayTreeDataProvider,
  ojkeyset_1,
) {
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

      self.selectedRows = ko.observableArray();
      self.selectedRowsDP = new ArrayDataProvider(self.selectedRows, {
        keyAttributes: "id",
      });

      self.tabNameList = ko.observableArray([]);

      self.CDBCheck = ko.observable();

      self.buttonStates = ko.observable(true);
      self.groupValid = ko.observable();
      self.OPError = ko.observableArray([]);

      function getDB() {
        self.DBDet([]);
        $.ajax({
          url: self.DepName() + "/api/v2/db-det",
          type: "GET",
          dataType: "json",
          timeout: sessionStorage.getItem("timeInetrval"),
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
            self.DBDet.valueHasMutated();
            return self;
          },
        });
      }

      self.DBDetDP = new ArrayDataProvider(self.DBDet, {
        keyAttributes: "value",
      });

      self.dberr = ko.observable();
      self.CancelBehaviorOpt = ko.observable("icon");

      self.DBParam = ko.observable();
      self.getSuppLog = function (event, data) {
        if (self.currentDB()) {
          self.dbSuppInfo([]);
          self.CDBCheck("");
          $.ajax({
            url: self.DepName() + "/api/v2/db/supplog",
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            data: JSON.stringify({
              dbname: self.currentDB(),
            }),
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: "Fetching supplemental log details",
            error: function (xhr, textStatus, errorThrown) {
              app.showGlobalError(
                app.extractErrorMessage(xhr),
                "Supplemental Log Error",
              );
            },
            success: function (data) {
                self.dbSuppInfo.push({
                    'DBName': data[0].DB_UNIQUE_NAME,
                    'Status': data[0].SUPPLEMENTAL_LOG_DATA_MIN,
                    'RepAgent': data[0].REP_AGENT_THREADS,
                    'TruncChkpt': data[0].TRUNC_LOG_ON_CHKPT
                });
                getDomains();
                return self;
            },
          });
        }
      };
      self.dbsupplogDP = new ArrayDataProvider(self.dbSuppInfo, {
        keyAttributes: "DBUnique",
      });
      self.SchemaName = ko.observable();

      self.supplogcolumnArray = [
            { headerText: 'Database Name', field: 'DBName' },
            { headerText: 'Status', field: 'Status' },
            { headerText: 'Rep Agent Threads', field: 'RepAgent' },
            { headerText: 'Trunc Log on Chkpt', field: 'TruncChkpt' }
        ];

      self.openListener = function (event) {
        oj.Router.rootInstance.go("incidents");
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
      self.AddSuppMsgTab = ko.observableArray([]);
      self.domainLoading = ko.observable(false);

      function getDomains() {
        self.username1([]);
        self.othdom([]);
        self.aliasname1([]);
        self.domname1([]);
        self.selectedAliascategory("");
        self.selectedUsercategory("");
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
        let children = getAliascategories(event.detail.value);
        self.aliascategories(children);
      };

      self.OthDomProvider = new ArrayDataProvider(self.othdom, {
        keyAttributes: "value",
      });

      self.tranlevelVal = ko.observable("trandata");

      var tranlevel = [
        { value: "schematrandata", label: "Schema Trandata" },
        { value: "trandata", label: "Trandata" },
      ];
      self.tranlevelDP = new ArrayDataProvider(tranlevel, {
        keyAttributes: "value",
      });

      self.STVal = ko.observable("");

      var STOptions = [
        { value: "ALLCOLS", label: "ALLCOLS" },
        { value: "NOSCHEDULINGCOLS", label: "NOSCHEDULINGCOLS" },
        { value: "ALLOWNONVALIDATEDKEYS", label: "ALLOWNONVALIDATEDKEYS" },
        { value: "NOVALIDATE", label: "NOVALIDATE" },
        { value: "PARTIALJSON", label: "PARTIALJSON" },
        { value: "", label: "Default" },
      ];
      self.STOptionsDP = new ArrayDataProvider(STOptions, {
        keyAttributes: "value",
      });

      self.pdbName = ko.observable("");

      self.suppLogSchema = function (data, event) {
        self.schemaNameList([]);
        $.ajax({
          url: self.DepName() + "/api/v2/db/supplogschema",
          type: "POST",
          contentType: "application/json",
          data: JSON.stringify({
            dbname: self.currentPDB(),
            cdbCheck: self.CDBCheck(),
            pdbName: self.pdbName(),
          }),
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
            for (var i = 0; i < data[0].length; i++) {
              self.schemaNameList.push({
                label: data[0][i].username,
                value: data[0][i].username,
              });
            }
            self.schemaNameList.valueHasMutated();
            return self;
          },
        });
      };

      self.schemaListDP = new ArrayDataProvider(self.schemaNameList, {
        keyAttributes: "label",
      });
      self.schemaList = ko.observableArray([]);
      self.tableNameList = ko.observableArray([]);

      self.TableFetch = function (data, event) {
        if (self.schemaList().length > 0) {
          
          self.tableNameList([]);
          $.ajax({
            url: self.DepName() + "/api/v2/db/tablelist",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({
              dbname: self.currentPDB(),
              schemaList: self.schemaList(),
              cdbCheck: self.CDBCheck(),
              pdbName: self.pdbName(),
              gatherMeta: self.gatherMeta(),
            }),
            dataType: "json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: "Fetching table list",
            error: function (xhr, textStatus, errorThrown) {
              
              app.showGlobalError(
                app.extractErrorMessage(xhr),
                "Table List Error",
              );
            },
            success: function (data) {
              self.tableNameList([]);
              document.getElementById("tableTrandata").refresh();
              for (var i = 0; i < data[0].length; i++) {
                self.tableNameList.push({
                  TABLE_NAME: data[0][i].owner + "." + data[0][i].table_name,
                  ROWCNT: data[0][i].num_rows,
                  AVGSPC: data[0][i].avg_space,
                  ANALYZETIME: data[0][i].last_analyzed,
                });
              }

              var allNewTableNames = self.tableNameList().map(function (t) {
                return t.TABLE_NAME;
              });

              var previouslySelected = self.selectedRows().map(function (row) {
                return row.Table;
              });

              var isAddAllActive =
                self.selectedItems &&
                self.selectedItems() &&
                self.selectedItems().row &&
                self.selectedItems().row.isAddAll();

              var finalSelectedNames;
              if (isAddAllActive) {
                finalSelectedNames = allNewTableNames.slice();
              } else {
                finalSelectedNames = previouslySelected.filter(function (name) {
                  return allNewTableNames.indexOf(name) !== -1;
                });
              }

              var finalSelected = finalSelectedNames.map(
                function (name, index) {
                  return { id: index + 1, Table: name };
                },
              );

              if (isAddAllActive) {
                self.selectedItems({
                  row: new ojkeyset_1.AllKeySetImpl(),
                  column: new ojkeyset_1.KeySetImpl(),
                });
              } else if (finalSelectedNames.length > 0) {
                var keySet = new ojkeyset_1.KeySetImpl(finalSelectedNames);
                self.selectedItems({
                  row: keySet,
                  column: new ojkeyset_1.KeySetImpl(),
                });
              } else {
                self.selectedItems({
                  row: new ojkeyset_1.KeySetImpl(),
                  column: new ojkeyset_1.KeySetImpl(),
                });
              }

              var selectionText = finalSelectedNames.join(", ");
              self.selectedRows(finalSelected);
              self.selectionInfo(selectionText);
              self.buttonStates(selectionText.length === 0);
              self.selectedRows.valueHasMutated();
              self.tableNameList.valueHasMutated();
              
              return self;
            },
          });
        }
      };
      self.tableSearchTextRaw = ko.observable("");
      self.tableSearchText = ko.observable("");

      let searchDebounceTimer = null;
      self.tableSearchTextRaw.subscribe(function (newVal) {
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(function () {
          self.tableSearchText(newVal);
        }, 250);
      });

      self.tableNameListDP = new PagingDataProviderView(
        new ArrayDataProvider(self.tableNameList, {
          idAttribute: "TABLE_NAME",
        }),
      );

      self.dataproviderView = ko.computed(function () {
        var searchText = self.tableSearchText();
        var options = {};

        if (searchText && searchText.length > 0) {
          options.filterCriterion = oj.FilterFactory.getFilter({
            filterDef: {
              text: searchText,
            },
          });
        }

        return new ListDataProviderView(self.tableNameListDP, options);
      });

      self.tableListcolumnArray = [
        { headerText: "Schema.Table Name", field: "TABLE_NAME" },
        { headerText: "Row Count", field: "ROWCNT" },
        { headerText: "Average Size(MB)", field: "AVGSPC" },
        { headerText: "Analyze Time", field: "ANALYZETIME" },
      ];

      self.popUpResizeSM = (value) => {
        document.getElementById(value).style.width = "900px";
        document.getElementById(value).style.height = "70vh";
      };

      this.selectedItems = ko.observable({
        row: new ojkeyset_1.KeySetImpl(),
        column: new ojkeyset_1.KeySetImpl(),
      });

      this.selectedSelectionMode = ko.observable({
        row: "multiple",
        column: "none",
      });
      this.selectionModes = [
        { value: { row: "multiple", column: "none" }, label: "Multiple Row" },
      ];
      this.selectionModeDP = new ArrayDataProvider(this.selectionModes, {
        keyAttributes: "value",
      });

      this.selectedChangedListener = (event) => {
        let selectionText = "";
        let tableData = [];

        if (event.detail.value.row.isAddAll()) {
          const allRows = self.tableNameList();
          const deletedKeys = new Set();
          event.detail.value.row.deletedValues().forEach(function (key) {
            deletedKeys.add(String(key));
          });
          allRows.forEach(function (row) {
            const tableName = row.TABLE_NAME;
            if (!deletedKeys.has(String(tableName))) {
              tableData.push({ id: tableData.length + 1, Table: tableName });
              selectionText +=
                selectionText.length === 0 ? tableName : ", " + tableName;
            }
          });
        } else {
          const row = event.detail.value.row;
          const column = event.detail.value.column;
          if (row.values().size > 0) {
            row.values().forEach(function (key) {
              const k = String(key);
              selectionText += selectionText.length === 0 ? k : ", " + k;
              tableData.push({ id: tableData.length + 1, Table: k });
            });
          }
          if (column.values().size > 0) {
            column.values().forEach(function (key) {
              selectionText += selectionText.length === 0 ? key : ", " + key;
            });
            selectionText = "Column Selection:\nColumn Keys: " + selectionText;
          }
        }

        self.selectionInfo(selectionText);
        self.buttonStates(selectionText.length === 0);
        self.selectedRows(tableData);
      };

      this.selectedSelectionMode.subscribe(() => {
        this.selectedItems({
          row: new ojkeyset_1.KeySetImpl(),
          column: new ojkeyset_1.KeySetImpl(),
        });
      });

      self.currentTabList = ko.computed({
        read: function () {
          self.tabNameList([]);
          var currentTabList = "";
          if (self.selectionInfo().length > 0) {
            let selectedData = self.selectionInfo().split(",");
            for (var i = 0; i < selectedData.length; i++) {
              self.tabNameList.push(selectedData[i]);
            }
          }
          return currentTabList;
        },
        write: function (newVal) {
          return newVal;
        },
      });

      // ── Dialog state ──────────────────────────────────────────
      self.AddSuppHasWarning = ko.observable(false);
      self.AddSuppWarnings = ko.observableArray([]);
      self.AddSuppStreaming = ko.observable(false);
      self.AddSuppWarningsMinimized = ko.observable(false);

      self.AddSuppWarningsDP = ko.pureComputed(function () {
        return new ArrayDataProvider(self.AddSuppWarnings(), {
          keyAttributes: "id",
        });
      });

      self.AddSuppDialogTitle = ko.computed(function () {
        var btn = self.buttonValue();
        if (btn === "add") return "Enable Supplemental Logging";
        if (btn === "del") return "Disable Supplemental Logging";
        if (btn === "info") return "View Supplemental Logging";
        return "Supplemental Logging";
      });

      // ── Filter (info/view mode only) ──────────────────────────
      self.activeFilter = ko.observable("");

      // Plain computed array — used directly in oj-bind-for-each
      self.filteredSuppMsg = ko.pureComputed(function () {
        var filter = self.activeFilter();
        var all = self.AddSuppMsg();
        if (!filter) return all;
        return all.filter(function (row) {
          return row.status === filter;
        });
      });

      // ── addSuppLog ────────────────────────────────────────────
      self.addSuppLog = () => {
        if (self.tranlevelVal() === "schematrandata") {
          document.querySelector("#DeleteSupp").close();
          const valid = self._checkValidationGroup("tracker");
          if (!valid) return;
        }
        document.querySelector("#DeleteSupp").close();

        self.AddSuppMsg([]);
        self.AddSuppHasWarning(false);
        self.AddSuppWarnings([]);
        self.AddSuppStreaming(true);
        self.activeFilter(""); // reset filter on every new run

        self.popUpResizeSM("AddTranSuppDialog");
        document.querySelector("#AddTranSuppDialog").open();

        var consumed = 0;

        function processLine(line) {
          line = line.trim();
          if (!line || line.indexOf("event:") === 0) return;
          if (line.indexOf("data:") !== 0) return;

          var raw = line.replace(/^data:\s*/, "").trim();
          if (!raw || raw === "__DONE__" || raw === "{}") {
            self.AddSuppStreaming(false);
            return;
          }

          var row;
          try {
            row = JSON.parse(raw);
          } catch (e) {
            console.warn("SSE parse error:", line, e);
            return;
          }

          // Show any warning message (even on an otherwise-successful row)
          if (row.error) {
            self.AddSuppWarnings.push({
              id: self.AddSuppWarnings().length,
              message: (row.tableName || "") + ": " + row.error,
            });
            self.AddSuppHasWarning(true);
          }

          // Still add the row to the main table UNLESS the whole thing
          // truly failed (status === 'Error')
          if (row.status !== "Error") {
            self.AddSuppMsg.push({
              tableName: row.tableName || "",
              status: row.status || "",
              keys: row.keys || "",
              schedulingCols: row.schedulingCols || "",
              allCols: row.allCols || "",
            });
          }
        }

        function processAvailable(fullText) {
          var newText = fullText.substring(consumed);
          if (!newText) return;
          var blocks = newText.split("\n\n");
          var incomplete = blocks.pop();
          blocks.forEach(function (block) {
            block.split("\n").forEach(processLine);
          });
          consumed = fullText.length - incomplete.length;
        }

        function runAjax(url, method, payload) {
          $.ajax({
            url: url,
            type: method,
            dataType: "text",
            contentType: "application/json",
            data: payload ? JSON.stringify(payload) : null,
            timeout: 0,
            context: self,
            showProgress: false, // this has its own streaming dialog already
            xhr: function () {
              var xhr = new window.XMLHttpRequest();
              xhr.onprogress = function () {
                processAvailable(xhr.responseText);
              };
              return xhr;
            },
            success: function (responseText) {
              processAvailable(responseText);
              var remaining = responseText.substring(consumed);
              if (remaining.trim()) {
                remaining.split("\n").forEach(processLine);
              }
              self.AddSuppStreaming(false);
            },
            error: function (xhr, textStatus) {
              self.AddSuppStreaming(false);

              if (
                xhr.status === 200 &&
                xhr.responseText &&
                xhr.responseText.indexOf("data:") >= 0
              ) {
                processAvailable(xhr.responseText);
                var remaining = xhr.responseText.substring(consumed);
                if (remaining.trim()) {
                  remaining.split("\n").forEach(processLine);
                }
                self.AddSuppStreaming(false);
                return;
              }

              document.querySelector("#AddTranSuppDialog").close();

              if (textStatus === "timeout") {
                app.showGlobalError(
                  "Request timed out. Please try again.",
                  "Request Timeout",
                );
              } else {
                app.showGlobalError(
                  app.extractErrorMessage(xhr),
                  "Supplemental Logging Failed",
                );
              }
            },
          });
        }

        if (self.tranlevelVal() === "schematrandata") {
          var btn = self.buttonValue();
          var schemaName = self.SchemaName();
          var alias = self.currentPDB();
          var domain = self.selectedDomCategory();
          var opts = self.STVal() || "";

          if (btn === "add") {
            runAjax(self.DepName() + "/api/v2/supp/schema", "POST", {
              domain: domain,
              alias: alias,
              tranlevel: "schematrandata",
              SchemaName: schemaName,
              buttonValue: btn,
              opts: opts,
            });
          } else if (btn === "info") {
            runAjax(
              self.DepName() +
                "/api/v2/supp/schema/" +
                encodeURIComponent(schemaName) +
                "?alias=" +
                encodeURIComponent(alias) +
                "&domain=" +
                encodeURIComponent(domain),
              "GET",
              null,
            );
          } else if (btn === "del") {
            runAjax(
              self.DepName() +
                "/api/v2/supp/schema/" +
                encodeURIComponent(schemaName) +
                "?alias=" +
                encodeURIComponent(alias) +
                "&domain=" +
                encodeURIComponent(domain) +
                "&opts=" +
                encodeURIComponent(opts),
              "DELETE",
              null,
            );
          }
        } else if (self.tranlevelVal() === "trandata") {
          runAjax(self.DepName() + "/api/v2/supp/trandata", "POST", {
            domain: self.selectedDomCategory(),
            alias: self.currentPDB(),
            tranlevel: "trandata",
            buttonValue: self.buttonValue(),
            opts: self.STVal() || "",
            tabNameList: self.tabNameList(),
          });
        }
      };

      self.AddSuppMsgTabcolumnArray = [
        { headerText: "Schema.Table Name", field: "table" },
        { headerText: "Status", field: "level" },
        { headerText: "Key Columns", field: "keys" },
      ];

      self._checkValidationGroup = (value) => {
        var tracker = document.getElementById(value);
        if (tracker.valid === "valid") {
          return true;
        } else {
          tracker.showMessages();
          tracker.focusOn("@firstInvalidShown");
          return false;
        }
      };

      self.openDelSuppLog = function () {
        if (self.tranlevelVal() == "schematrandata") {
          let valid = self._checkValidationGroup("tracker");
          if (valid) {
            document.querySelector("#DeleteSupp").open();
          }
        } else {
          document.querySelector("#DeleteSupp").open();
        }
      };

      self.addsuppOKClose = function (event) {
        document.querySelector("#AddTranSuppDialog").close();
      };

      self.CloseOkaddSuppLog = function (event) {
        document.querySelector("#DeleteSupp").close();
      };

      self.connected = function () {
        app.onAppSuccess();
        getDB();
        self.dbSuppInfo([]);
        self.gatherMeta(false);
      };

      self.disconnected = function () {
        // Implement if needed
      };

      self.transitionCompleted = function () {
        // Implement if needed
      };
    }
  }
  return addsuppViewModel;
});
