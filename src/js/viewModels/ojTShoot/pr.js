define([
  "knockout",
  "jquery",
  "appController",
  "ojs/ojarraydataprovider",
  "ojs/ojarraytreedataprovider",
  "ojDiagram/viewModels/CircleLayout",
  "ojs/ojattributegrouphandler",
  "ojs/ojknockout",
  "ojs/ojdiagram",
  "ojs/ojformlayout",
  "ojs/ojbutton",
  "ojs/ojtable",
  "ojs/ojselectsingle",
  "ojs/ojradioset",
  "ojs/ojtreeview",
], function (ko, $, app, ArrayDataProvider, ArrayTreeDataProvider, layout, attributeGroupHandler) {
  class prtshootViewModel {
    constructor(context) {
      var self = this;
      self.DepName = context.DepName;

      self.RepDet = ko.observableArray([]);
      self.repName = ko.observable();
      self.ButtonVal = ko.observable(true);
      self.currentFormat = ko.observable("tab");
      self.loaded = ko.observable(false);

      self.DBDet = ko.observableArray([]);
      self.PRSession = ko.observableArray([]);
      self.SchedInfo = ko.observableArray([]);
      self.RunningTxnInfo = ko.observableArray([]);
      self.NodeData = ko.observableArray([]);
      self.LinkData = ko.observableArray([]);
      self.Pstack = ko.observableArray([]);
      self.sectionErrors = ko.observableArray([]);

      // ── Replicat list ──
      function getRep() {
        self.RepDet([]);
        $.ajax({
          url: self.DepName() + "/api/v2/rep-type",
          type: "GET",
          dataType: "json",
          progressMessage: "Fetching replicat list",
          error: function (xhr) {
            app.showGlobalError(app.extractErrorMessage(xhr), "Replicat List Error");
          },
          success: function (data) {
            self.RepDet((data[0] || [])
              .filter(function (r) { return String(r.RepType || "").toUpperCase() === "PARALLEL"; })
              .map(function (r) { return { value: r.RepName, label: r.RepName }; }));
            self.ButtonVal(true);
          },
        });
      }
      self.RepDetDP = new ArrayDataProvider(self.RepDet, { keyAttributes: "value" });

      self.valueChangedHandler = function () {
        self.ButtonVal(!self.repName());
      };

      // ── Troubleshoot ──
      self.PRTShoot = function () {
        if (!self.repName()) return;
        self.DBDet([]);
        self.PRSession([]);
        self.SchedInfo([]);
        self.RunningTxnInfo([]);
        self.NodeData([]);
        self.LinkData([]);
        self.Pstack([]);
        self.sectionErrors([]);
        self.loaded(false);

        $.ajax({
          url: self.DepName() + "/api/v2/pr-tshoot",
          type: "POST",
          contentType: "application/json",
          data: JSON.stringify({ repName: self.repName() }),
          dataType: "json",
          timeout: 120000,
          progressMessage: "Analyzing parallel replicat",
          error: function (xhr) {
            app.showGlobalError(app.extractErrorMessage(xhr), "Troubleshoot Error");
          },
          success: function (data) {
            // [db_det, sessions, schedulers, running_txn, nodes, links, pstack, errors]
            self.DBDet(data[0] || []);
            self.PRSession(data[1] || []);

            self.SchedInfo((data[2] || []).map(function (s) { return { scheduler: s }; }));

            self.RunningTxnInfo((data[3] || []).map(function (r) {
              var t = Array.isArray(r.Txn) ? r.Txn : [r.Txn];
              return { group: r.Group, txnCount: t.length, txn: t.join(", ") };
            }));

            self.NodeData((data[4] || []).map(function (n) {
              return { id: n.id + (n.category === "Txn" ? "-X" : "-Y"), label: n.id, category: n.category };
            }));

            self.LinkData((data[5] || []).map(function (l) {
              return {
                id: l.id, category: l.category,
                start: l.start + "-X", end: l.end + "-Y",
                startTxn: l.start, endTxn: l.end, Wait: "is waiting on",
              };
            }));

            var tree = [];
            var stack = data[6] || {};
            Object.keys(stack).forEach(function (tid) {
              tree.push({
                id: "t" + tid,
                title: tid === "main" ? "Main" : "Thread " + tid,
                children: (stack[tid] || []).map(function (line, i) {
                  return { id: "t" + tid + "-" + i, title: line };
                }),
              });
            });
            self.Pstack(tree);

            var errs = data[7] || {};
            self.sectionErrors(Object.keys(errs).map(function (k) {
              return { section: k, message: String(errs[k]) };
            }));

            self.loaded(true);
          },
        });
      };

      // ── Data providers ──
      self.DBDetDP = new ArrayDataProvider(self.DBDet, { keyAttributes: "@index" });
      self.PRSessionDP = new ArrayDataProvider(self.PRSession, { keyAttributes: "@index" });
      self.SchedInfoDP = new ArrayDataProvider(self.SchedInfo, { keyAttributes: "@index" });
      self.RunningTxnInfoDP = new ArrayDataProvider(self.RunningTxnInfo, { keyAttributes: "@index" });
      self.LinkDataDP = new ArrayDataProvider(self.LinkData, { keyAttributes: "id" });
      self.nodeDataProvider = new ArrayDataProvider(self.NodeData, { keyAttributes: "id" });
      self.linkDataProvider = new ArrayDataProvider(self.LinkData, { keyAttributes: "id" });
      self.PstackDataDP = new ArrayTreeDataProvider(self.Pstack, {
        keyAttributes: "id",
        childrenAttribute: "children",
      });

      // ── Columns ──
      self.PRDBDetcolumnArray = [
        { headerText: "Server", field: "SERVER_NAME" },
        { headerText: "Host", field: "HOST" },
        { headerText: "Database", field: "DBNAME" },
        { headerText: "Version", field: "VERSION_NUMBER" },
        { headerText: "Current Time", field: "CURRENT_TIME" },
      ];

      self.PRSessioncolumnArray = [
        { headerText: "Process", field: "NAME" },
        { headerText: "ASE SPID", field: "SID" },
        { headerText: "KPID", field: "SERIAL" },
        { headerText: "OS PID", field: "SPID" },
        { headerText: "Status", field: "STATUS" },
        { headerText: "Command", field: "EVENT" },
        { headerText: "Blocked By", field: "BLOCKED_BY" },
        { headerText: "Time Blocked (s)", field: "CALL" },
        { headerText: "Transaction", field: "TRAN_NAME" },
        { headerText: "CPU", field: "CPU" },
        { headerText: "Physical IO", field: "PHYSICAL_IO" },
      ];

      self.SchedcolumnArray = [{ headerText: "Scheduler", field: "scheduler" }];

      self.RunningTxncolumnArray = [
        { headerText: "Group", field: "group" },
        { headerText: "Txn Count", field: "txnCount" },
        { headerText: "Transaction IDs", field: "txn", style: "white-space:normal" },
      ];

      self.WaitTxncolumnArray = [
        { headerText: "Transaction (X)", field: "startTxn" },
        { headerText: "", field: "Wait" },
        { headerText: "Transaction (Y)", field: "endTxn" },
      ];

      // ── Diagram ──
      self.colorHandler = new attributeGroupHandler.ColorAttributeGroupHandler();
      self.layoutFunc = layout.layout;
      self.highlightedCategoriesValue = ko.observable(null);
      self.hoverBehaviorValue = ko.observable("dim");
      self.styleDefaults = {
        nodeDefaults: { icon: { width: 150, shape: "rectangle" } },
        linkDefaults: { svgStyle: { vectorEffect: "non-scaling-stroke", opacity: 0.4 } },
      };

      self.formatDetails = function (id) {
        return "Waiting on " + id;
      };

      var tooltipElem = document.createElement("div");
      tooltipElem.innerHTML =
        '<div style="float:left;padding:10px 8px 10px 3px;">' +
        '<span style="font-weight:bold;color:#606060;"></span><br>' +
        '<span style="font-style:italic;"></span></div>';
      var labelText = tooltipElem.children[0].children[0];
      var valueText = tooltipElem.children[0].children[2];

      self.tooltipFunction = function (ctx) {
        var d = ctx.itemData || ctx.data || {};
        if (d.startTxn) {                      // link
          labelText.textContent = d.startTxn;
          valueText.textContent = "is waiting on " + d.endTxn;
        } else {                               // node
          labelText.textContent = d.label || d.id || "";
          valueText.textContent = d.category === "Txn" ? "Waiting transaction" : "Blocking transaction";
        }
        return { insert: tooltipElem };
      };

      self.connected = function () {
        if (sessionStorage.getItem("userName") == null) {
          oj.Router.rootInstance.go("signin");
        } else {
          app.onAppSuccess();
          getRep();
        }
      };
    }
  }
  return prtshootViewModel;
});