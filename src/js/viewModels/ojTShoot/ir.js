define([
  "knockout",
  "jquery",
  "appController",
  "ojs/ojarraydataprovider",
  "ojs/ojknockout",
  "ojs/ojcollapsible",
  "ojs/ojbutton",
  "ojs/ojtable",
  "ojs/ojinputtext",
  "ojs/ojselectsingle",
  "ojs/ojformlayout",
], function (ko, $, app, ArrayDataProvider) {
  class irtshootViewModel {
    constructor(context) {
      var self = this;
      self.DepName = context.DepName;

      // ── Inputs ──
      self.currentDB = ko.observable();
      self.repName = ko.observable("");
      self.chkptTbl = ko.observable("");
      self.DBDet = ko.observableArray([]);
      self.ButtonVal = ko.observable(true);
      self.DBDetDP = new ArrayDataProvider(self.DBDet, { keyAttributes: "value" });

      function getDB() {
        $.ajax({
          url: self.DepName() + "/api/v2/db-det",
          type: "GET",
          dataType: "json",
          progressMessage: "Fetching database list",
          suppressGlobalError: true,
          error: function (xhr) {
            if (xhr.status === 401) { app.handleSessionExpired(); return; }
            app.showGlobalError(app.extractErrorMessage(xhr), "Database List Error");
          },
          success: function (data) {
            self.DBDet([]);
            (data[0] || []).forEach(function (r) {
              self.DBDet.push({ value: r.dbname, label: r.dbname });
            });
            self.ButtonVal(true);
          },
        });
      }

      self.valueChangedHandler = function () {
        self.ButtonVal(!self.currentDB());
      };

      // ── Sections, grouped like the old page ──
      var GROUPS = [
        {
          id: "replicat", title: "Replicat Sessions", sections: [
            { key: "rep_sessions",    title: "Replicat Sessions",
              hint: "GoldenGate Replicat connections. A non-zero 'Blocked' means the Replicat is waiting on another session." },
            { key: "rep_open_trans",  title: "Open Replicat Transactions",
              hint: "Long-open Replicat transactions indicate large source transactions or lock waits." },
            { key: "rep_locks",       title: "Locks Held by Replicat",
              hint: "Many page/table locks can escalate and block other users." },
            { key: "rep_waits",       title: "Replicat Wait Events (MDA)",
              hint: "Where the Replicat spends its time. Requires 'enable monitoring' and 'wait event timing'." },
            { key: "rep_current_sql", title: "Current SQL (MDA)",
              hint: "Statement currently executed by each Replicat session." },
            { key: "rep_statements",  title: "Statement Statistics (MDA)",
              hint: "High LogicalReads per RowsAffected usually means a missing index on the target table." },
          ],
        },
        {
          id: "checkpoint", title: "Checkpoint Table", sections: [
            { key: "checkpoint", title: "Replicat Checkpoints",
              hint: "Last applied trail SEQNO/RBA and AUDIT_TS (source commit time) per Replicat." },
          ],
        },
        {
          id: "health", title: "Database Health", sections: [
            { key: "db_det",       title: "Server / Database", hint: "" },
            { key: "db_options",   title: "Database Options",
              hint: "'abort tran on log full = NO' makes the Replicat hang instead of failing when the log fills." },
            { key: "log_space",    title: "Transaction Log Space",
              hint: "A full target log stops the Replicat." },
            { key: "log_hold",     title: "Log Held By (syslogshold)",
              hint: "Oldest open transaction that prevents log truncation." },
            { key: "blocking",     title: "Blocking Sessions", hint: "" },
            { key: "long_running", title: "Long Running Transactions (>20m)", hint: "" },
          ],
        },
        {
          id: "schema", title: "Schema Checks", sections: [
            { key: "no_unique_key",    title: "Tables Without Unique Key",
              hint: "UPDATE/DELETE on these tables scan the whole table. Most common cause of slow Replicat on ASE." },
            { key: "triggers",         title: "Tables With Triggers",
              hint: "Triggers fire for every applied row; consider disabling during initial load." },
            { key: "identity_columns", title: "Identity Columns",
              hint: "Need identity_insert handling to keep source values." },
            { key: "foreign_keys",     title: "Foreign Keys",
              hint: "Parent and child tables should be applied by the same Replicat." },
          ],
        },
      ];

      function prettify(key) {
        if (!key) return "Value";
        return String(key)
          .replace(/_/g, " ")
          .replace(/([a-z])([A-Z])/g, "$1 $2")
          .replace(/\b\w/g, function (c) { return c.toUpperCase(); });
      }

      var sectionMap = {};
      self.groups = GROUPS.map(function (g) {
        return {
          id: g.id,
          title: g.title,
          sections: g.sections.map(function (s) {
            var rows = ko.observableArray([]);
            var sec = Object.assign({}, s, {
              rows: rows,
              columns: ko.observableArray([]),
              dp: new ArrayDataProvider(rows, { keyAttributes: "@index" }),
              error: ko.observable(""),
            });
            sectionMap[s.key] = sec;
            return sec;
          }),
        };
      });

      function rows(key) { return sectionMap[key] ? sectionMap[key].rows() : []; }

      // ── Summary cards ──
      self.loaded = ko.observable(false);
      self.targetDb = ko.observable("");
      self.sectionErrors = ko.observableArray([]);

      self.repSessionCount = ko.pureComputed(function () { return rows("rep_sessions").length; });
      self.repOpenTxnCount = ko.pureComputed(function () { return rows("rep_open_trans").length; });
      self.blockingCount   = ko.pureComputed(function () { return rows("blocking").length; });
      self.noUniqueCount   = ko.pureComputed(function () { return rows("no_unique_key").length; });
      self.logUsedPct      = ko.pureComputed(function () {
        var r = rows("log_space")[0];
        return r ? parseFloat(r.log_used_pct || 0) : 0;
      });

      self.cardClass = function (level) {
        return { ok: "oj-bg-success-20", warn: "oj-bg-warning-20", bad: "oj-bg-danger-20" }[level] || "";
      };
      self.logLevel = ko.pureComputed(function () {
        var p = self.logUsedPct();
        return p >= 85 ? "bad" : p >= 70 ? "warn" : "ok";
      });

      // ── Run troubleshoot ──
      self.IRTShoot = function () {
        if (!self.currentDB()) return;
        $.ajax({
          url: self.DepName() + "/api/v2/db/irtshoot",
          type: "POST",
          contentType: "application/json",
          data: JSON.stringify({
            dbname: self.currentDB(),
            repname: (self.repName() || "").trim() || null,
            chkpttbl: (self.chkptTbl() || "").trim() || null,
          }),
          dataType: "json",
          timeout: 120000,
          progressMessage: "Analyzing Sybase replicat target",
          suppressGlobalError: true,
          error: function (xhr) {
            if (xhr.status === 401) { app.handleSessionExpired(); return; }
            app.showGlobalError(app.extractErrorMessage(xhr), "Troubleshoot Error");
          },
          success: function (data) {
            if (data.error) {
              app.showGlobalError(data.error, "Troubleshoot Error");
              return;
            }
            var errs = data.errors || {};

            Object.keys(sectionMap).forEach(function (key) {
              var sec = sectionMap[key];
              var list = (data[key] || []).map(function (r) {
                var copy = {};
                Object.keys(r).forEach(function (k) { copy[k || "value"] = r[k]; });
                return copy;
              });
              var cols = [];
              list.forEach(function (r) {
                Object.keys(r).forEach(function (k) { if (cols.indexOf(k) < 0) cols.push(k); });
              });
              sec.columns(cols.map(function (k) { return { headerText: prettify(k), field: k }; }));
              sec.rows(list);
              sec.error(errs[key] ? String(errs[key]) : "");
            });

            self.sectionErrors(Object.keys(errs).map(function (k) {
              var sec = sectionMap[k];
              return { section: sec ? sec.title : k, message: String(errs[k]) };
            }));
            self.targetDb(data.targetdb || "");
            self.loaded(true);
          },
        });
      };

      self.connected = function () {
        if (sessionStorage.getItem("userName") == null) {
          oj.Router.rootInstance.go("signin");
        } else {
          app.onAppSuccess();
          getDB();
        }
      };
    }
  }
  return irtshootViewModel;
});