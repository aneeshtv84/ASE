define([
  "knockout",
  "jquery",
  "appController",
  "ojs/ojarraydataprovider",
  "ojs/ojarraytreedataprovider",
  "ojs/ojknockout",
  "ojs/ojformlayout",
  "ojs/ojbutton",
  "ojs/ojtable",
  "ojs/ojselectsingle",
  "ojs/ojtreeview",
], function (ko, $, app, ArrayDataProvider, ArrayTreeDataProvider) {
  class crtshootViewModel {
    constructor(context) {
      var self = this;
      self.DepName = context.DepName;

      self.RepDet = ko.observableArray([]);
      self.repName = ko.observable();
      self.ButtonVal = ko.observable(true);

      self.DBDet = ko.observableArray([]);
      self.PRSession = ko.observableArray([]);
      self.Pstack = ko.observableArray([]);
      self.CRWaits = ko.observableArray([]);
      self.CRSQL = ko.observableArray([]);
      self.sectionErrors = ko.observableArray([]);
      self.loaded = ko.observable(false);

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
            var list = (data[0] || [])
              .filter(function (r) { return String(r.RepType || "").toUpperCase() === "CLASSIC"; })
              .map(function (r) { return { value: r.RepName, label: r.RepName }; });
            self.RepDet(list);
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
        self.Pstack([]);
        self.CRWaits([]);
        self.CRSQL([]);
        self.sectionErrors([]);
        self.loaded(false);

        $.ajax({
          url: self.DepName() + "/api/v2/cr-tshoot",
          type: "POST",
          contentType: "application/json",
          data: JSON.stringify({ repName: self.repName() }),
          dataType: "json",
          timeout: 120000,
          progressMessage: "Analyzing replicat process",
          error: function (xhr) {
            app.showGlobalError(app.extractErrorMessage(xhr), "Troubleshoot Error");
          },
          success: function (data) {
            // data = [db_det, sessions, pstack, waits, sql, errors]
            self.DBDet(data[0] || []);
            self.PRSession(data[1] || []);

            // pstack → tree (every node needs an id)
            var tree = [];
            var stack = data[2] || {};
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

            self.CRWaits(data[3] || []);

            self.CRSQL((data[4] || []).map(function (r) {
              return { SID: r.SID, SQL: r.SQL_FULLTEXT };
            }));

            var errs = data[5] || {};
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
      self.WaitsDP = new ArrayDataProvider(self.CRWaits, { keyAttributes: "@index" });
      self.RunningSqlDP = new ArrayDataProvider(self.CRSQL, { keyAttributes: "@index" });
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
        { headerText: "Database", field: "DBNAME" },
      ];

      self.WaitscolumnArray = [
        { headerText: "ASE SPID", field: "SID" },
        { headerText: "Wait Event", field: "EVENT" },
        { headerText: "Waits", field: "TOTAL_COUNT" },
        { headerText: "Wait Time (ms)", field: "WAIT_TIME_MS" },
      ];

      self.RunningSqlcolumnArray = [
        { headerText: "ASE SPID", field: "SID", style: "width:90px" },
        { headerText: "SQL Text", field: "SQL", style: "white-space:pre-wrap" },
      ];

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
  return crtshootViewModel;
});