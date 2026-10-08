define([
  "ojs/ojcore",
  "knockout",
  "jquery",
  "appController",
  "ojDiagram/viewModels/ggLayout",
  "ojs/ojknockout-keyset",
  "ojs/ojattributegrouphandler",
  "ojs/ojconverter-number",
  "ojs/ojconverterutils-i18n",
  "ojs/ojconverter-datetime",
  "ojs/ojarraydataprovider", "ojs/ojlistdataproviderview",
  "ojs/ojarraytreedataprovider",
  "ojs/ojinputnumber",
  "ojs/ojdatetimepicker",
  "ojs/ojinputtext",
  "ojs/ojformlayout",
  "ojs/ojknockout",
  "ojs/ojactioncard",
  "ojs/ojdiagram",
  "ojs/ojdialog",
  "ojs/ojprogress-bar",
  "ojs/ojselectcombobox",
  "ojs/ojtable",
  "ojs/ojselectsingle",
  "ojs/ojradioset",
  "ojs/ojinputsearch",
], function (
  oj,
  ko,
  $,
  app,
  layout,
  keySet,
  attributeGroupHandler,
  NumberConverter,
  ConverterUtilsI18n,
  DateTimeConverter,
  ArrayDataProvider, ListDataProviderView,
  ArrayTreeDataProvider,
) {
  class InitManageViewModel {
    constructor(args) {

      var self = this;
      self.DepName = args.routerState.detail.dep_url;

      self.NodeData = ko.observableArray([]);
      self.LinkData = ko.observableArray([]);
      self.ExtData = ko.observableArray([]);
      self.RepData = ko.observableArray([]);
      self.ExpandedNodes = ko.observableArray([]);
      self.CancelBehaviorOpt = ko.observable("icon");
      self.styleExt = ko.observable();
      self.styleRep = ko.observable();
      self.ILStats = ko.observableArray([]);
      self.ILTables = ko.observableArray([]);
      self.ILStatsComplete = ko.observableArray([]);
      self.NodeExt = ko.observableArray([]);
      self.NodeRep = ko.observableArray([]);
      self.expandedNodes = new keySet.ObservableKeySet();
      self.ILJobData = ko.observableArray([]);
      self.currentILJOb = ko.observable();
      self.ILException = ko.observable();
      self.PrmWrite = ko.observable();
      let interval = 30000;

      self.onepDepList = ko.observableArray([]);
      self.TgtOnePDepName = ko.observable();
      self.TgtonepDepType = ko.observable(); 

      self.tgtTokenKey = function () {
        return "Tgt_" + self.TgtOnePDepName() + "_AccessToken";
      };

      self.fetchTgtDepToken = function (depName, callback, force) {
        $.ajax({
          url: self.DepName() + "/api/v2/onep/deptoken",   // goes to SOURCE agent, source token
          type: "POST",
          data: JSON.stringify({ dep: depName, force: !!force }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") { if (callback) callback(false); return; }
            if (xhr.status === 401 && !xhr.responseJSON) {   // source session itself expired
              app.handleSessionExpired();
              return;
            }
            var msg = app.extractErrorMessage(xhr);
            if (callback) callback(false, msg);
            else app.showGlobalError(`Unable to authenticate to target deployment "${depName}". ${msg}`, "Target Auth Error");
          },
          success: function (data) {
            sessionStorage.setItem("Tgt_" + depName + "_AccessToken", data.access_token);
            sessionStorage.setItem("Tgt_" + depName + "_DepUrl", data.dep_url);
            sessionStorage.setItem("Tgt_" + depName + "_DbType", data.dbtype);
            if (callback) callback(true);
          },
        });
      };

      self.tgtAuthHeader = function () {
        var token = sessionStorage.getItem(self.tgtTokenKey());
        return token ? { Authorization: "Bearer " + token } : undefined;
      };

      self.tgtAjax = function (ajaxOpts) {
        var originalError = ajaxOpts.error;
        var depName = self.TgtOnePDepName();
        var alreadyRetried = false;

        ajaxOpts.isTargetCall = true;     
        ajaxOpts.headers = self.tgtAuthHeader();

        ajaxOpts.error = function (xhr, textStatus, errorThrown) {
          if (textStatus === "abort") {
            if (originalError) originalError(xhr, textStatus, errorThrown);
            return;
          }
          if (xhr.status === 503) {
            app.showGlobalError(
              "SQL Server Service Manager is not started on deployment \"" + depName +
              "\". Please start the Service Manager and try again.",
              "Service Manager Not Started"
            );
            return;
          }
          if (xhr.status === 401) {
            if (!alreadyRetried && sessionStorage.getItem(self.tgtTokenKey())) {
              alreadyRetried = true;
              self.fetchTgtDepToken(depName, function (ok, msg) {
                if (ok) {
                  ajaxOpts.headers = self.tgtAuthHeader();
                  $.ajax(ajaxOpts);
                } else {
                  app.showGlobalError(`Target deployment "${depName}" rejected the login. ${msg || ""}`, "Target Auth Error");
                }
              }, true);
              return;
            }
            app.showGlobalError(`Not authorized on target deployment "${depName}".`, "Target Auth Error");
            return;
          }
          if (originalError) originalError(xhr, textStatus, errorThrown);
        };
        $.ajax(ajaxOpts);
      };

      function getOnepDep() {
        self.onepDepList([]);
        $.ajax({
          url: self.DepName() + "/api/v2/onep/dep",
          type: "GET",
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Fetching deployment list",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to fetch deployment list. ${msg}`,
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
      }

      self.resolveTgtContext = function (depName, callback) {
        self.TgtOnePDepName(depName);
        var cached = self.tgtCtxCache[depName];
        if (cached) {
          self.TGTonepDepUrl(cached.url);
          self.TgtonepDepType(cached.dbtype);
          callback();
          return;
        }
        $.ajax({
          url: self.DepName() + "/api/v2/onep/depurl",
          type: "POST",
          data: JSON.stringify({ dep: depName }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          progressMessage: `Resolving deployment ${depName}`,
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401) { app.handleSessionExpired(); return; }
            app.showGlobalError(app.extractErrorMessage(xhr), "Deployment Error");
          },
          success: function (data) {
            var key = "Tgt_" + depName + "_AccessToken";
            if (data[3]) sessionStorage.setItem(key, data[3]);   // remote target token
            else sessionStorage.removeItem(key);                 // local target -> source token
            var ctx = { url: data[0], dbtype: (data[2] || "").toLowerCase() };
            self.tgtCtxCache[depName] = ctx;
            self.TGTonepDepUrl(ctx.url);
            self.TgtonepDepType(ctx.dbtype);
            callback();
          },
        });
      };


      self.TGTonepDepUrl = ko.observable("");
      self.tgtCtxCache = {};
      self.SelectTGTDeployment = function () {
        if (self.TgtOnePDepName()) {
          delete self.tgtCtxCache[self.TgtOnePDepName()];
          self.resolveTgtContext(self.TgtOnePDepName(), function () {});
        }
      };

      self.isMsTarget = function () {
        return ["mongodb", "sqlserver"].includes(self.TgtonepDepType());
      };

      self.formatOggResult = function (data) {
        var payload = Array.isArray(data) ? data[0]
                    : (data && data.data !== undefined ? data.data : data);
        var out = [];
        (function walk(x) {
          if (Array.isArray(x)) { x.forEach(walk); return; }
          if (x && typeof x === "object" && x.title) {
            out.push("[" + (x.severity || "INFO") + "] " + (x.code || "") + "  " +
                     (x.issued || "") + "\n" + x.title);
          } else if (x !== null && x !== undefined && x !== "") {
            out.push(typeof x === "object" ? JSON.stringify(x, null, 2) : String(x));
          }
        })(payload);
        if (data && data.status === "error" && data.message) out.unshift(data.message);
        return out.join("\n\n");
      };

            // ---------- Statistics table ----------
      self.statsRows = ko.observableArray([]);
      self.statsHideZero = ko.observable(false);
      self.statsTitle = ko.observable("");

      self.statsDP = ko.computed(function () {
        var rows = self.statsRows();
        if (self.statsHideZero()) {
          rows = rows.filter(function (r) { return Number(String(r.raw).replace(/,/g, "")) !== 0; });
        }
        return new ArrayDataProvider(rows, { keyAttributes: "id" });
      });

      self.statsColumns = [
        { headerText: "Table / Process", field: "table",  sortable: "enabled" },
        { headerText: "Statistic",       field: "metric", sortable: "enabled" },
        { headerText: "Value",           field: "value",  style: "text-align:right", headerStyle: "text-align:right" },
      ];

      function humanize(key) {
        return String(key)
          .replace(/_/g, " ")
          .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
          .replace(/\s+/g, " ")
          .trim()
          .replace(/^./, function (c) { return c.toUpperCase(); });
      }

      function parseMaybeJson(x) {
        if (typeof x === "string") {
          var t = x.trim();
          if (t.charAt(0) === "{" || t.charAt(0) === "[") {
            try { return JSON.parse(t); } catch (e) { /* not JSON */ }
          }
        }
        return x;
      }

      function fmt(v) {
        var n = Number(String(v).replace(/,/g, ""));
        return (v !== "" && v !== null && !isNaN(n)) ? n.toLocaleString() : String(v);
      }

      // Accepts: JSON string, flat object (mpoints), {table: {op: n}}, arrays, or report text
      self.buildStatsRows = function (raw, procName) {
        var rows = [], id = 0;

        function add(table, metric, value) {
          rows.push({ id: id++, table: table, metric: humanize(metric), value: fmt(value), raw: value });
        }

        function walk(x, table) {
          x = parseMaybeJson(x);
          if (x === null || x === undefined || x === "") return;

          if (Array.isArray(x)) { x.forEach(function (i) { walk(i, table); }); return; }

          if (typeof x === "object") {
            Object.keys(x).forEach(function (k) {
              if (k.charAt(0) === "$" || k === "links" || k === "messages") return;
              var v = parseMaybeJson(x[k]);
              if (v !== null && typeof v === "object") walk(v, k);   // nested block = per table
              else add(table, k, v);
            });
            return;
          }

          // Report text: "Extracting from dbo.orders to dbo.orders:" / "Total inserts   6.00"
          String(x).split(/\r?\n/).forEach(function (line) {
            var l = line.trim();
            if (!l) return;
            var t = l.match(/^(?:Extracting|Replicating)\s+from\s+(\S+)/i);
            if (t) { table = t[1]; return; }
            var m = l.match(/^(.+?)\s{2,}([\d.,]+)$/);
            if (m) add(table, m[1], m[2]);
          });
        }

        walk(raw, procName);
        return rows;
      };

      self.showStats = function (raw, procName, procType) {
        self.statsRows(self.buildStatsRows(raw, procName));
        self.statsTitle((procType === "Rep" ? "Replicat " : "Extract ") + procName + " Statistics");
        self.statsHideZero(false);
        document.querySelector("#StatsDialog").open();
      };

      self.closeStats = function () {
        document.querySelector("#StatsDialog").close();
      };

      self.onepDepListDP = new ArrayDataProvider(self.onepDepList, {
        keyAttributes: "value",
      });

      function getILData() {
        $.ajax({
          url: self.DepName() + "/api/v2/il/dataset",
          type: "GET",
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          progressMessage: "Fetching initial load jobs",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to fetch initial load jobs. ${msg}`,
              "Job List Error",
            );
          },
          success: function (data) {
            self.ILJobData([]);
            for (var i = 0; i < data[0].length; i++) {
              self.ILJobData.push({
                label: data[0][i].jobname,
                value: data[0][i].jobname,
              });
            }
            return self;
          },
        });
      }

      self.getNodeFlow = function (event, data) {
        $.ajax({
          url: self.DepName() + "/api/v2/gg-il-processes",
          type: "POST",
          data: JSON.stringify({ JobName: self.currentILJOb() }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          progressMessage: `Fetching process flow for ${self.currentILJOb()}`,
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to fetch process flow. ${msg}`,
              "Process Flow Error",
            );
          },
          success: function (data) {
            self.NodeExt([]);
            self.NodeRep([]);
            for (var key in data[3]) {
              for (var i = 0; i < data[3][key].length; i++) {
                var n = data[3][key][i];
                var node = { id: n.procname + " " + key, url: n.dep_url, type: n.type, depName: key };
                if (n.type == "Ext") self.NodeExt.push(node);
                if (n.type == "Rep") self.NodeRep.push(node);
              }
            }
            self.NodeData([]);
            self.NodeData.push(
              { id: "Extracts", nodes: self.NodeExt() },
              { id: "Replicats", nodes: self.NodeRep() },
            );

            self.expandedNodes.add(["Extracts", "Replicats"]);
            self.LinkData([]);
            for (var i = 0; i < data[0].length; i++) {
              self.LinkData.push({
                start: data[0][i].extname + " " + data[0][i].dep_src,
                trail: data[0][i].trail,
                end: data[0][i].repname + " " + data[0][i].dep_tgt,
                id: i,
              });
            }

            self.ExtData([]);
            self.RepData([]);
            for (var i = 0; i < data[1].length; i++) {
              if (data[1][i].extstat == "STOPPED") {
                self.ExtData.push({
                  ExtName: data[1][i].extname,
                  ExtStat: data[1][i].extstat,
                  styleExt: { "background-color": "Chocolate" },
                });
              } else if (
                data[1][i].extstat == "RUNNING" ||
                data[1][i].extstat == "STARTING"
              ) {
                self.ExtData.push({
                  ExtName: data[1][i].extname,
                  ExtStat: data[1][i].extstat,
                  styleExt: { "background-color": "ForestGreen" },
                });
              } else if (data[1][i].extstat == "ABENDED") {
                self.ExtData.push({
                  ExtName: data[1][i].extname,
                  ExtStat: data[1][i].extstat,
                  styleExt: { "background-color": "IndianRed" },
                });
              }
            }
            for (var i = 0; i < data[4].length; i++) {
              if (data[4][i].repstat.toUpperCase()  == "STOPPED") {
                self.RepData.push({
                  RepName: data[4][i].repname,
                  RepStat: data[4][i].repstat,
                  styleExt: { "background-color": "Chocolate" },
                });
              } else if (
                data[4][i].repstat.toUpperCase()  == "RUNNING" ||
                data[4][i].repstat.toUpperCase()  == "STARTING"
              ) {
                self.RepData.push({
                  RepName: data[4][i].repname,
                  RepStat: data[4][i].repstat,
                  styleExt: { "background-color": "ForestGreen" },
                });
              } else if (data[4][i].repstat.toUpperCase()  == "ABENDED") {
                self.RepData.push({
                  RepName: data[4][i].repname,
                  RepStat: data[4][i].repstat,
                  styleExt: { "background-color": "IndianRed" },
                });
              }
            }
            self.ExtData.valueHasMutated();
            self.RepData.valueHasMutated();
            ILSetTimer();
            return self;
          },
        });
      };

      var intervalVar;

      function ILSetTimer() {
        clearInterval(intervalVar);
        if (self.ILException() == "error") interval = Math.min(interval + 60000, 300000);
        intervalVar = setInterval(getILFlow, interval);
      }

      self.disconnected = function () {
        clearInterval(intervalVar);
      };

      self.getILTables = function (event, data) {
        if (self.currentILJOb()) {
          $.ajax({
            url: self.DepName() + "/api/v2/il/tables",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ JobName: self.currentILJOb() }),
            timeout: 120000,
            progressMessage: `Fetching tables for ${self.currentILJOb()}`,
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (textStatus === "abort") return;
              if (xhr.status === 401) {
                self.ILException("");
                return;
              }
              self.ILException(textStatus);
              ILSetTimer();
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to fetch tables for "${self.currentILJOb()}". ${msg}`,
                "Tables Fetch Error",
              );
            },
            success: function (data) {
              self.ILTables([]);
              for (var key in data[0]) {
                self.ILTables.push({
                  TABLE_NAME: key,
                  TARGET_ROWS: data[0][key].TargetRows,
                  PROCESS_NAME: data[0][key].Process,
                });
              }
              self.ILStats([]);
              for (var key in data[0]) {
                self.ILStats.push({
                  TABLE_NAME: key,
                  TARGET_ROWS: data[0][key].TargetRows,
                  PROCESS_NAME: data[0][key].Process,
                });
              }
              self.getNodeFlow();
              return self;
            },
          });
        }
      };

      function getILFlow() {
        if (self.currentILJOb()) {
          self.ILException("");
          $.ajax({
            url: self.DepName() + "/api/v2/gg-il-processes",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({
              JobName: self.currentILJOb(),
              tabList: self.ILTables(),
            }),
            timeout: 120000,
            showProgress: false,
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (textStatus === "abort") return;
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              self.ILException(textStatus);
              ILSetTimer();
            },
            success: function (data) {
              
              self.ExtData([]);
              self.RepData([]);
              for (var i = 0; i < data[1].length; i++) {
                if (data[1][i].extstat == "STOPPED") {
                  self.ExtData.push({
                    ExtName: data[1][i].extname,
                    ExtStat: data[1][i].extstat,
                    styleExt: { "background-color": "Chocolate" },
                  });
                } else if (
                  data[1][i].extstat == "RUNNING" ||
                  data[1][i].extstat == "STARTING"
                ) {
                  self.ExtData.push({
                    ExtName: data[1][i].extname,
                    ExtStat: data[1][i].extstat,
                    styleExt: { "background-color": "ForestGreen" },
                  });
                } else if (data[1][i].extstat == "ABENDED") {
                  self.ExtData.push({
                    ExtName: data[1][i].extname,
                    ExtStat: data[1][i].extstat,
                    styleExt: { "background-color": "IndianRed" },
                  });
                }
              }

              for (var i = 0; i < data[4].length; i++) {
                if (data[4][i].repstat.toUpperCase() == "STOPPED") {
                  self.RepData.push({
                    RepName: data[4][i].repname,
                    RepStat: data[4][i].repstat,
                    styleExt: { "background-color": "Chocolate" },
                  });
                } else if (
                  data[4][i].repstat.toUpperCase() == "RUNNING" ||
                  data[4][i].repstat.toUpperCase() == "STARTING"
                ) {
                  self.RepData.push({
                    RepName: data[4][i].repname,
                    RepStat: data[4][i].repstat,
                    styleExt: { "background-color": "ForestGreen" },
                  });
                } else if (data[4][i].repstat.toUpperCase() == "ABENDED") {
                  self.RepData.push({
                    RepName: data[4][i].repname,
                    RepStat: data[4][i].repstat,
                    styleExt: { "background-color": "IndianRed" },
                  });
                }
              }
              self.ExtData.valueHasMutated();
              self.RepData.valueHasMutated();
              self.ILStats([]);
              var ilstatsdata = []
              for (var key in data[2]) {
                ilstatsdata.push({
                  TABLE_NAME: key,
                  TARGET_ROWS: data[2][key].TargetRows,
                  PROCESS_NAME: data[2][key].Process,
                  EXTCOUNT: data[2][key].TotalEXT,
                  EXTDSC: data[2][key].TotalEXTDSC,
                  EXTRATE: data[2][key].ExtRate,
                  REPCOUNT: data[2][key].TotalREP,
                  REPDSC: data[2][key].TotalREPDSC,
                  REPRATE: data[2][key].RepRate,
                  REPELA: timeConversion(data[2][key].RepElapse),
                  REPETA: timeConversion(data[2][key].RepETA),
                  Stat: data[2][key].Status,
                });
              }
              self.ILStats(ilstatsdata)
              self.ILStats.valueHasMutated();
              self.ILException(data[5]);
              if (self.ILException() == "error") {
                ILSetTimer();
              }
              return self;
            },
          });
        }
      }

      function timeConversion(d) {
        var h = Math.floor(d / 3600);
        var m = Math.floor((d % 3600) / 60);
        var s = Math.floor((d % 3600) % 60);

        var hDisplay = h > 0 ? h + (h == 1 ? "h" : "h") : "";
        var mDisplay = m > 0 ? m + (m == 1 ? "m" : "m") : "";
        var sDisplay = s > 0 ? s + (s == 1 ? "s" : "s") : "";
        let elpseTime = hDisplay + mDisplay + sDisplay;
        return elpseTime;
      }

      self.ExtDataDP = ko.observable(
        new ArrayDataProvider(self.ExtData, { keyAttributes: "ExtName" }),
      );
      self.RepDataDP = ko.observable(
        new ArrayDataProvider(self.RepData, { keyAttributes: "RepName" }),
      );

      self.tableSearchTextRaw = ko.observable("");
      self.tableSearchText = ko.observable("");

      let searchDebounceTimer = null;

      self.tableSearchTextRaw.subscribe(function (newVal) {
        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(function () {
          self.tableSearchText(newVal);
        }, 250);
      });

      self.dataproviderView = ko.computed(function () {
        var searchText = self.tableSearchText();
        var options = {};

        if (searchText && searchText.length > 0) {
        options.filterCriterion = oj.FilterFactory.getFilter({
            filterDef: { text: searchText },
        });
        }

        var baseDataProvider = new ArrayDataProvider(self.ILStats, { keyAttributes: 'TABLE_NAME' });
        return new ListDataProviderView(baseDataProvider, options);
      });

      self.ILStatsDP = ko.observable(
        new ArrayDataProvider(self.ILStats, { keyAttributes: "TABLE_NAME" }),
      );
      self.nodeDataProvider = ko.observable(
        new ArrayTreeDataProvider(self.NodeData, {
          keyAttributes: "id",
          childrenAttribute: "nodes",
        }),
      );
      self.linkDataProvider = ko.observable(
        new ArrayDataProvider(self.LinkData, { keyAttributes: "id" }),
      );
      self.ILjobDataProvider = ko.observable(
        new ArrayDataProvider(self.ILJobData, { keyAttributes: "id" }),
      );
      var color =
        new attributeGroupHandler.ColorAttributeGroupHandler().getValue(0);
      self.layoutFunc = layout.containerLayout;

      self.ILStatscolumnArray = [
        {
          headerText: "Process",
          field: "PROCESS_NAME",
        },
        {
          headerText: "Schema.Table Name",
          field: "TABLE_NAME",
        },
        {
          headerText: "Target Rows",
          field: "TARGET_ROWS",
        },
        {
          headerText: "Extracting Count",
          field: "EXTCOUNT",
        },
        {
          headerText: "Replicating Count",
          field: "REPCOUNT",
        },
        {
          headerText: "Replicat Discard Count",
          field: "REPDSC",
        },
        {
          headerText: "Replicat Rate/sec",
          field: "REPRATE",
        },
        {
          headerText: "Status",
          field: "Stat",
        },
      ];

      this.linkRendererFunc = function (context) {
        var rootElement = context.rootElement;

        var width = context.state.hovered || context.state.selected ? 2 : 1;
        if (!rootElement) {
          var linkid =
            context.type === "promotedLink"
              ? context.id.name + context.id.startId + context.id.endId
              : context.id;
          var rootElement = createGroup("linkSvg" + linkid);
          addPath(
            rootElement,
            10,
            context.state.selected,
            "underlay",
            context.points,
          );
          addPath(rootElement, width, context.state.selected, context.type);
        } else {
          var visiblePath = rootElement.children[1];
          visiblePath.setAttribute("stroke-width", width);
          visiblePath.classList.toggle(
            "demo-diagram-selected-link",
            context.state.selected,
          );
        }
        return { insert: rootElement };
      };

      self.getStyleUrl = (styleId) => {
        return "url(" + document.URL + "#" + styleId + ")";
      };
      this.nodeRendererFunc = function (context) {
        var color = context.state.selected ? "red" : "#87ceeb"; //header color
        var stroke = context.state.selected || context.state.hovered ? 4 : 3;
        var rootElement = context.rootElement;
        if (!rootElement) {
          // initial rendering - create an svg element with a node content in it
          var nodeId = context.data["id"];
          if (context.state.expanded) {
            //render expanded node
            var childContent = context.content;
            // add 20 px for the each side padding and
            // additional 20 px on top for the header
            var w = childContent.w + 60,
              h = childContent.h + 100;
            rootElement = createSVG("nodeSvg" + nodeId, w, h);
            var group = addGroup(rootElement, "topGroup" + nodeId);
            ((w -= 2), (h -= 2)); //reduce width and height for inner elements
            addRect(group, "rect" + nodeId, 1, 1, w, h, "white");
            addRect(group, "rectHdr" + nodeId, 1, 1, w, 25, color); //header size
            addChildContent(group, childContent.element);
          } else {
            //render collapsed or leaf node
            rootElement = createSVG("nodeSvg" + nodeId, 1000, 1000); //size of the main container
            var group = addGroup(rootElement, "topGroup" + nodeId);
            addRect(
              group,
              "rectInner" + nodeId,
              15,
              10,
              200,
              25,
              self.getStyleUrl("gradient1"),
            ); //position of the child containers inside main
          }
        } else {
          // modification case - apply custom treatment to the node
          var group = rootElement.childNodes[0];
          var outerRect = group.childNodes[0];
          outerRect.setAttributeNS(null, "stroke", color);
          outerRect.setAttributeNS(null, "stroke-width", stroke);
          if (context.state.expanded) {
            //change header color for the container node
            var hdrRect = group.childNodes[1];
            hdrRect.setAttributeNS(null, "stroke", "color");
            hdrRect.setAttributeNS(null, "stroke", color);
          }
        }
        return { insert: rootElement };
      };
      // SVG helper functions for node rendering
      function createSVG(id, width, height) {
        var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttributeNS(null, "width", width);
        svg.setAttributeNS(null, "height", height);
        svg.setAttributeNS(null, "viewBox", "0 0 " + width + " " + height);
        return svg;
      }
      function addGroup(parent, id) {
        var group = document.createElementNS("http://www.w3.org/2000/svg", "g");
        group.setAttributeNS(null, "id", id);
        parent.appendChild(group);
        return group;
      }
      function addRect(parent, id, x, y, w, h, fill) {
        var svgRect = document.createElementNS(
          "http://www.w3.org/2000/svg",
          "rect",
        );
        svgRect.setAttributeNS(null, "id", id);
        svgRect.setAttributeNS(null, "x", x);
        svgRect.setAttributeNS(null, "y", y);
        svgRect.setAttributeNS(null, "width", w);
        svgRect.setAttributeNS(null, "height", h);
        svgRect.setAttributeNS(null, "fill", fill);
        svgRect.setAttributeNS(null, "stroke", "#87ceeb");
        svgRect.setAttributeNS(null, "stroke-width", 1);
        parent.appendChild(svgRect);
        return svgRect;
      }
      function addChildContent(parent, elem) {
        parent.appendChild(elem);
        elem.setAttributeNS(null, "transform", "translate(10 30)");
      }

      // SVG helper functions for link rendering
      function createGroup(id) {
        var group = document.createElementNS("http://www.w3.org/2000/svg", "g");
        group.setAttribute("id", id);
        return group;
      }
      function addPath(parent, width, selected, type, points) {
        var svgPath = document.createElementNS(
          "http://www.w3.org/2000/svg",
          "path",
        );
        var linkSvgClasses =
          type === "underlay"
            ? "demo-diagram-link-underlay"
            : "demo-diagram-link oj-diagram-link-path demo-diagram-promoted-link";
        if (type === "underlay") {
          svgPath.setAttribute("d", points.join(" "));
        } else {
          if (type === "promotedLink")
            linkSvgClasses += " demo-diagram-promoted-link";
          if (selected) linkSvgClasses += " demo-diagram-selected-link";
        }
        svgPath.setAttribute("stroke-width", width);
        svgPath.setAttribute("class", linkSvgClasses);
        parent.appendChild(svgPath);
      }

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
      self.selectedAliascategory = ko.observable();
      self.selectedUsercategory = ko.observable();
      self.aliascategories = ko.observableArray([]);
      self.unamecategories = ko.observable();
      self.selectedDomCategory = ko.observable();

      let getAliascategories = (category) => {
        let found = self.aliasname1().find((c) => c.value === category);
        return found ? found.children : null;
      };
      let getUnamecategories = (category) => {
        let found = self.username1().find((c) => c.value === category);
        return found ? found.children : null;
      };
      this.domSelectionChanged = (event) => {
        self.selectedAliascategory("");
        let children = getAliascategories(event.detail.value);
        self.aliascategories(children);
      };

      self.aliasSelectionChanged = (event) => {
        self.selectedUsercategory("");
        let children = getUnamecategories(event.detail.value);
        self.unamecategories(children);
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
      self.helpDef = ko.computed(function () {
        return self.checkboxValues.indexOf("helpDef") !== -1
          ? self._HELP_DEF
          : null;
      });
      this.helpSource = ko.computed(function () {
        return self.checkboxValues.indexOf("helpSource") !== -1
          ? self._HELP_SOURCE
          : null;
      });

      self.currentbeginmode = ko.observable("Now");

      self.beginmode = ko.observableArray([
        { value: "Now", label: "Begin Now" },
        { value: "Time", label: "Custom Time" },
        { value: "LOC", label: "Location" },
      ]);

      self.startOptionDP = new ArrayDataProvider(self.beginmode, {
        keyAttributes: "value",
      });

      self.secondConverter = new DateTimeConverter.IntlDateTimeConverter({
        pattern: "yyyy-MM-dd HH:mm:ss",
      });

      self.ctvalue = ko.observable(
        ConverterUtilsI18n.IntlConverterUtils.dateToLocalIso(new Date()),
      );

      self.seqnovalue = ko.observable();
      self.rbavalue = ko.observable();

      self.decimalHalfDownConverter = new NumberConverter.IntlNumberConverter({
        style: "decimal",
        roundingMode: "HALF_DOWN",
        maximumFractionDigits: 0,
        useGrouping: false,
      });

            function getDomains(forTarget) {
        self.username1([]); self.othdom([]); self.aliasname1([]); self.domname1([]);
        self.selectedDomCategory(""); self.selectedAliascategory(""); self.selectedUsercategory("");

        var route = (forTarget && self.isMsTarget()) ? "/api/v2/credstore" : "/api/v2/vault/info/all";
        var opts = {
          url: self.selDepname() + route,
          type: "GET",
          dataType: "json",
          timeout: 10000,
          progressMessage: "Fetching credential domains",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401) { app.handleSessionExpired(); return; }
            app.showGlobalError(`Unable to fetch credential domains. ${app.extractErrorMessage(xhr)}`,
                                "Credential Domain Error");
          },
          success: function (data) {
            for (var i = 0; i < data[1].length; i++) self.othdom.push({ dom: data[1][i].value });
            self.aliasname1(data[4]);
            for (var i = 0; i < data[2].length; i++) self.domname1.push({ label: data[2][i], value: data[2][i] });
            for (var i = 0; i < data[0].length; i++) {
              self.username1.push({
                label: data[0][i].alias, value: data[0][i].alias,
                children: [{ label: data[0][i].uname, value: data[0][i].uname }],
              });
            }
          },
        };
        if (forTarget) self.tgtAjax(opts); else $.ajax(opts);
      }

      self.selectedNodesValue = ko.observable();
      self.selectionValue = ko.observable("single");

      self.ExtRpt = ko.observableArray([]);
      self.selectedMenuItem = ko.observable("");

      self.selDepname = ko.observable();
      self.selProcType = ko.observable();
      self.onePDepname = ko.observable();
      self.selDbType = ko.observable();
      self.dialogTitle = ko.observable();

      self.popUpResize = (value) => {
        document.getElementById(value).style.width = "1150px";
        document.getElementById(value).style.height = "100vh";
      };

      self.popUpResizeSM = (value) => {
        document.getElementById(value).style.width = "500px";
        document.getElementById(value).style.height = "45vh";
      };

      self.menuItemAction = function (event) {
        self.selectedMenuItem(event.target.value);
        self.selDepname(""); self.selProcType(""); self.selDbType("");
        self.NodeData().forEach(function (grp) {
          grp.nodes.forEach(function (n) {
            if (n.id == self.selectedNodesValue()[0]) {
              self.selDepname(n.url);       // agent URL of the process
              self.selProcType(n.type);     // "Ext" / "Rep"
              self.selDbType(n.depName);    // DEPLOYMENT NAME (e.g. "MSSQL")
            }
          });
        });
        if (self.selProcType() == "Ext") {
          self.TgtOnePDepName("");
          self.TgtonepDepType("");
          self.dialogTitle(
            "View Extract " +
              self.selectedNodesValue()[0].split(" ")[0] +
              " Info",
          );
          if (
            self.selectedMenuItem() == "rpt" ||
            self.selectedMenuItem() == "chk" ||
            self.selectedMenuItem() == "stats" ||
            self.selectedMenuItem() == "startdef" ||
            self.selectedMenuItem() == "stop" ||
            self.selectedMenuItem() == "forcestop" ||
            self.selectedMenuItem() == "kill" ||
            self.selectedMenuItem() == "edit"
          ) {
            self.ExtRpt([]);
            $.ajax({
              url: self.selDepname() + "/api/v2/extract/ops/view/log",
              data: JSON.stringify({
                extops: self.selectedMenuItem(),
                extname: self.selectedNodesValue()[0].split(" ")[0],
              }),
              type: "POST",
              contentType: "application/json",
              dataType: "json",
              timeout: 10000,
              context: self,
              progressMessage: `Processing ${self.selectedMenuItem()} for extract`,
              suppressGlobalError: false,
              error: function (xhr, textStatus) {
                if (textStatus === "abort") return;
                if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
                var msg = app.extractErrorMessage(xhr);
                app.showGlobalError(
                  `Unable to complete extract action. ${msg}`,
                  "Extract Action Error",
                );
              },
              success: function (data) {
                if (
                  self.selectedMenuItem() == "startdef" ||
                  self.selectedMenuItem() == "stop" ||
                  self.selectedMenuItem() == "forcestop" ||
                  self.selectedMenuItem() == "kill"
                ) {
                  self.popUpResizeSM("ViewExtractRptDialog");
                  document.querySelector("#ViewExtractRptDialog").open();
                  self.ExtRpt(data[0]);
                  getILFlow();
                } else if (self.selectedMenuItem() == "edit") {
                  document.querySelector("#EditDialog").open();
                  self.ExtRpt(data[1]);
                } else if (self.selectedMenuItem() == "stats") {
                  var extStats = (data[2] && data[2].message !== undefined) ? data[2].message
                               : (data[2] && Object.keys(data[2]).length ? data[2] : data[0]);
                  self.showStats(extStats, self.selectedNodesValue()[0].split(" ")[0], "Ext")
                  // self.popUpResize("ViewExtractRptDialog");
                  // document.querySelector("#ViewExtractRptDialog").open();
                  // self.ExtRpt(data[2].message);
                } else {
                  self.popUpResize("ViewExtractRptDialog");
                  document.querySelector("#ViewExtractRptDialog").open();
                  self.ExtRpt(data[0]);
                }
                return self;
              },
            });
          } else if (self.selectedMenuItem() == "del") {
            getDomains();
            getOnepDep();
            document.querySelector("#ExtLoginDialog").open();
          }
                } else if (self.selProcType() == "Rep") {
          var repName = self.selectedNodesValue()[0].split(" ")[0];
          self.dialogTitle("View Replicat " + repName + " Info");
          var op = self.selectedMenuItem();

          if (["rpt","chk","stats","startdef","nofilterdup","stop","forcestop","kill","edit"].includes(op)) {
            self.ExtRpt([]);
            self.resolveTgtContext(self.selDbType(), function () {
              var url = self.isMsTarget() ? "/api/v2/viewreplicatlog" : "/api/v2/replicat/ops/view/log";
              self.tgtAjax({
                url: self.selDepname() + url,
                data: JSON.stringify({ repops: op, repname: repName }),
                type: "POST",
                contentType: "application/json",
                dataType: "json",
                timeout: 10000,
                progressMessage: `Processing ${op} for replicat`,
                suppressGlobalError: true,
                error: function (xhr, textStatus) {
                  if (textStatus === "abort") return;
                  app.showGlobalError(`Unable to complete replicat action. ${app.extractErrorMessage(xhr)}`,
                                      "Replicat Action Error");
                },
                success: function (data) {
                  if (["startdef","stop","forcestop","kill","nofilterdup"].includes(op)) {
                    self.popUpResizeSM("ViewExtractRptDialog");
                    document.querySelector("#ViewExtractRptDialog").open();
                    self.ExtRpt(self.isMsTarget() ? self.formatOggResult(data) : data[0]);
                    getILFlow();
                  } else if (op == "edit") {
                    document.querySelector("#EditDialog").open();
                    var prm = data[1];
                    self.ExtRpt(Array.isArray(prm) ? prm.join("\n") : prm);
                  } else if (op == "stats") {
                    self.showStats(data[0], repName, "Rep");
                  } else {
                    self.popUpResize("ViewExtractRptDialog");
                    document.querySelector("#ViewExtractRptDialog").open();
                    self.ExtRpt(self.isMsTarget() && op != "rpt" ? self.formatOggResult(data) : data[0]);
                  }
                },
              });
            });
          } else if (op == "del") {
            self.resolveTgtContext(self.selDbType(), function () {
              getDomains(true);
              document.querySelector("#ExtLoginDialog").open();
            });
          } else if (op == "begin") {
            self.resolveTgtContext(self.selDbType(), function () {
              getDomains(true);
              document.querySelector("#ReplicatBegin").open();
            });
          }
        }
      };

      self.DelExt = function (data, event) {
        document.querySelector("#ExtLoginDialog").close();
        self.ExtRpt([]);
        $.ajax({
          url: self.selDepname() + "/api/v2/extract/ops",
          data: JSON.stringify({
            extname: self.selectedNodesValue()[0].split(" ")[0],
            domain: self.selectedDomCategory(),
            alias: self.selectedAliascategory(),
            extops: "ext" + self.selectedMenuItem(),
          }),
          type: "POST",
          contentType: "application/json",
          dataType: "json",
          timeout: 10000,
          context: self,
          progressMessage: "Deleting extract",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to delete extract. ${msg}`,
              "Delete Extract Error",
            );
          },
          success: function (data) {
            document.querySelector("#ExtDelDialog").open();
            self.selectedDomCategory("");
            self.selectedAliascategory("");
            self.ExtRpt(data[0]);
            return self;
          },
        });
      };

      self.DelExtractRptOKClose = function (data, event) {
        document.querySelector("#ExtDelDialog").close();
        $.ajax({
          url: self.DepName() + "/api/v2/il/ext/delete",
          type: "DELETE",
          contentType: "application/json",
          data: JSON.stringify({
            jobName: self.currentILJOb(),
            srcdep: self.selectedNodesValue()[0].split(" ")[1],
            extname: self.selectedNodesValue()[0].split(" ")[0],
          }),
          dataType: "json",
          timeout: 10000,
          context: self,
          progressMessage: "Removing extract from job",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to remove extract from job. ${msg}`,
              "Remove Extract Error",
            );
          },
          success: function (data) {
            self.getNodeFlow();
            return self;
          },
        });
      };

            self.DelRep = function () {
        document.querySelector("#ExtLoginDialog").close();
        self.ExtRpt([]);
        self.resolveTgtContext(self.selDbType(), function () {
          var url = self.isMsTarget() ? "/api/v2/replicatOps" : "/api/v2/replicat/ops";
          self.tgtAjax({
            url: self.selDepname() + url,          // was TGTonepDepUrl() (empty)
            data: JSON.stringify({
              repname: self.selectedNodesValue()[0].split(" ")[0],
              domain: self.selectedDomCategory(),
              alias: self.selectedAliascategory(),
              repops: "rep" + self.selectedMenuItem(),
            }),
            type: "POST",
            contentType: "application/json",
            dataType: "json",
            timeout: 10000,
            progressMessage: "Deleting replicat",
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (textStatus === "abort") return;
              app.showGlobalError(`Unable to delete replicat. ${app.extractErrorMessage(xhr)}`,
                                  "Delete Replicat Error");
            },
            success: function (data) {
              document.querySelector("#RepDelDialog").open();
              self.ExtRpt(self.isMsTarget() ? self.formatOggResult(data) : data[0]);
            },
          });
        });
      };

      self.AlterReplicatBegin = function () {
        document.querySelector("#ReplicatBegin").close();
        self.ExtRpt([]);
        self.resolveTgtContext(self.selDbType(), function () {
          var url = self.isMsTarget() ? "/api/v2/replicatOps" : "/api/v2/replicat/ops";
          self.tgtAjax({
            url: self.selDepname() + url,
            data: JSON.stringify({
              repname: self.selectedNodesValue()[0].split(" ")[0],
              domain: self.selectedDomCategory(),
              alias: self.selectedAliascategory(),
              beginmode: self.currentbeginmode(),
              ctvalue: self.ctvalue(),
              seqnovalue: self.seqnovalue(),
              rbavalue: self.rbavalue(),
              repops: "rep" + self.selectedMenuItem(),
            }),
            type: "POST",
            contentType: "application/json",     // was missing
            dataType: "json",
            timeout: 10000,
            progressMessage: "Altering replicat begin point",
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (textStatus === "abort") return;
              app.showGlobalError(`Unable to alter replicat begin point. ${app.extractErrorMessage(xhr)}`,
                                  "Alter Replicat Error");
            },
            success: function (data) {
              self.ExtRpt(self.isMsTarget() ? self.formatOggResult(data) : data[0]);
              document.querySelector("#ViewExtractRptDialog").open();
            },
          });
        });
      };

      this._checkValidationGroup = () => {
        var tracker = document.getElementById("trackerMon");
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

      self.DelReplicatRptOKClose = function (data, event) {
        document.querySelector("#RepDelDialog").close();
        $.ajax({
          url: self.DepName() + "/api/v2/il/rep/delete",
          type: "DELETE",
          contentType: "application/json",
          data: JSON.stringify({
            jobName: self.currentILJOb(),
            tgtdep: self.selectedNodesValue()[0].split(" ")[1],
            repname: self.selectedNodesValue()[0].split(" ")[0],
          }),
          dataType: "json",
          timeout: 10000,
          context: self,
          progressMessage: "Removing replicat from job",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to remove replicat from job. ${msg}`,
              "Remove Replicat Error",
            );
          },
          success: function (data) {
            self.getNodeFlow();
            return self;
          },
        });
      };

      self.ValExtractRptOKClose = ()=>{
        document.querySelector('#ExtValidityDialog').close();
        if(self.selectedILActionMenuItem()=='purge'){
          window.location.reload()
        }
        getILFlow();
      }
      self.dialogTitleValidity = ko.observable();

            self.savePrm = function () {
        document.querySelector("#EditDialog").close();
        var isRep = self.selProcType() == "Rep";

        var send = function () {
          var ms = isRep && self.isMsTarget();
          var opts = {
            url: self.selDepname() + (ms ? "/api/v2/savePrmFile" : "/api/v2/params/save"),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            data: JSON.stringify({
              procName: self.selectedNodesValue()[0].split(" ")[0],
              currentParams: self.PrmWrite(),
            }),
            timeout: 20000,
            progressMessage: "Saving parameters",
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (textStatus === "abort") return;
              if (!isRep && xhr.status === 401) { app.handleSessionExpired(); return; }
              app.showGlobalError(`Unable to save parameters. ${app.extractErrorMessage(xhr)}`,
                                  "Save Parameters Error");
            },
            success: function (data) {
              self.dialogTitleValidity("Parameter Save");
              document.querySelector("#ExtValidityDialog").open();
              self.ExtRpt(ms ? (data.titles || [data.message || "Saved"]) : data[0]);
            },
          };
          if (isRep) self.tgtAjax(opts); else $.ajax(opts);
        };

        if (isRep) self.resolveTgtContext(self.selDbType(), send);
        else send();
      };

      self.ViewExtractRptOKClose = function (event) {
        document.querySelector("#ViewExtractRptDialog").close();
      };

      self.selectedILActionMenuItem = ko.observable();

      self.ILActionItem = function (event) {
        self.selectedILActionMenuItem(event.target.value);
        self.ExtRpt([]);
        $.ajax({
          url: self.DepName() + "/api/v2/gg-il-action",
          data: JSON.stringify({
            jobName: self.currentILJOb(),
            ilops: self.selectedILActionMenuItem(),
          }),
          type: "POST",
          dataType: "json",
          contentType: "application/json",
          timeout: 10000,
          context: self,
          progressMessage: `Processing ${self.selectedILActionMenuItem()} action for job ${self.currentILJOb()}`,
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to complete job action. ${msg}`,
              "Job Action Error",
            );
          },
          success: function (data) {
            self.ExtRpt(data[0]);
            self.popUpResizeSM("ViewExtractRptDialog");
            if (self.selectedILActionMenuItem() == "stop") {
              self.dialogTitle(
                "Stopping InitalLoad Job " + self.currentILJOb(),
              );
            } else if (self.selectedILActionMenuItem() == "start") {
              self.dialogTitle(
                "Starting InitalLoad Job " + self.currentILJOb(),
              );
            } else if (self.selectedILActionMenuItem() == "purge") {
              self.dialogTitle("Purging InitalLoad Job " + self.currentILJOb());
              self.currentILJOb("");
            }
            document.querySelector("#ViewExtractRptDialog").open();
            return self;
          },
        });
      };

      self.stopJobAction = function () {
        document.querySelector("#StopProcess").close();
      };

      self.stopJobDlg = function () {
        document.querySelector("#StopProcess").open();
      };
      self.CloseOkjob = function (event) {
        document.querySelector("#StopProcess").close();
      };

      //strt

      const data = [
        { name: "Home", id: "home", icons: "oj-ux-ico-home" },
        {
          name: "Statics",
          id: "statics",
          icons: "oj-ux-ico-education",
        },
      ];
      this.isChecked = ko.observable();
      this.selectedItem1 = ko.observable("home");
      this.selectedItem2 = ko.observable("statics");

      this.dataProvider = new ArrayDataProvider(data, { keyAttributes: "id" });

      ////end
      self.args = args;
      // Create a child router with one default path
      self.router = self.args.parentRouter;

      self.connected = function () {
        if (sessionStorage.getItem("userName") == null) {
          self.router.go("signin");
        } else {
          app.onAppSuccess();
          self.currentILJOb(args.params.LoadName);
          if (self.currentILJOb()) {
            self.getILTables();
          }
          getILData();
        }
      };

      /**
       * Optional ViewModel method invoked after the View is disconnected from the DOM.
       */
      self.disconnected = function () {
        clearTimeout(getILFlow);
        clearInterval(intervalVar);
        // Implement if needed
      };

      /**
       * Optional ViewModel method invoked after transition to the new View is complete.
       * That includes any possible animation between the old and the new View.
       */
      self.transitionCompleted = function () {};
    }
  }
  /*
   * Returns a constructor for the ViewModel so that the ViewModel is constructed
   * each time the view is displayed.  Return an instance of the ViewModel if
   * only one instance of the ViewModel is needed.
   */
  return InitManageViewModel;
});
