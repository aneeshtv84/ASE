define([
  "knockout",
  "jquery",
  "appController",
  "ojs/ojarraydataprovider",
  "ojs/ojresponsiveutils",
  "ojs/ojresponsiveknockoututils",
  "ojs/ojknockout",
  "ojs/ojbutton",
  "ojs/ojtable",
  "ojs/ojselectsingle",
  "ojs/ojformlayout",
  "ojs/ojnavigationlist",
], function (ko, $, app, ArrayDataProvider, ResponsiveUtils, ResponsiveKnockoutUtils) {
  class ietshootViewModel {
    constructor(context) {
      var self = this;
      self.DepName = context.DepName;

      // ── Database selection ──
      self.currentDB = ko.observable();
      self.DBDet = ko.observableArray([]);
      self.ButtonVal = ko.observable(true);
      self.DBDetDP = new ArrayDataProvider(self.DBDet, { keyAttributes: "value" });

      function getDB() {
        self.DBDet([]);
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

      // ── Section definitions (backend key -> UI section) ──
      var SECTIONS = [
        { id: "server",      key: "db_det",       title: "Server / Database",                icon: "fas fa-server" },
        { id: "trunc",       key: "trunc_point",  title: "Secondary Truncation Point",       icon: "fas fa-flag-checkered" },
        { id: "logspace",    key: "log_space",    title: "Transaction Log Space",            icon: "fas fa-hard-drive" },
        { id: "loghold",     key: "log_hold",     title: "Log Held By (syslogshold)",        icon: "fas fa-lock" },
        { id: "longrun",     key: "long_running", title: "Long Running Transactions (>20m)", icon: "fas fa-hourglass-half" },
        { id: "blocking",    key: "blocking",     title: "Blocking Sessions",                icon: "fas fa-ban" },
        { id: "reptables",   key: "rep_tables",   title: "Tables Marked for Replication",    icon: "fas fa-table" },
        { id: "ggsessions",  key: "gg_sessions",  title: "Extract / LTM Sessions",           icon: "fas fa-plug" },
        { id: "waits",       key: "top_waits",    title: "Top Waits (MDA)",                  icon: "fas fa-stopwatch" },
      ];

      function prettify(key) {
        if (!key) return "Value";
        return String(key)
          .replace(/_/g, " ")
          .replace(/([a-z])([A-Z])/g, "$1 $2")
          .replace(/\b\w/g, function (c) { return c.toUpperCase(); });
      }

      self.sections = SECTIONS.map(function (s) {
        var rows = ko.observableArray([]);
        return Object.assign({}, s, {
          rows: rows,
          columns: ko.observableArray([]),
          dp: new ArrayDataProvider(rows, { keyAttributes: "@index" }),
          error: ko.observable(""),
        });
      });

      function sectionByKey(key) {
        return self.sections.find(function (s) { return s.key === key; });
      }

      // ── Navigation ──
      var lgQuery = ResponsiveUtils.getFrameworkQuery(ResponsiveUtils.FRAMEWORK_QUERY_KEY.LG_UP);
      self.large = ResponsiveKnockoutUtils.createMediaQueryObservable(lgQuery);

      self.navDP = new ArrayDataProvider(
        [{ id: "all", name: "Overview", icons: "fas fa-house" }].concat(
          SECTIONS.map(function (s) { return { id: s.id, name: s.title, icons: s.icon }; })
        ),
        { keyAttributes: "id" }
      );
      self.selectedSection = ko.observable("all");
      self.sectionVisible = function (id) {
        return self.selectedSection() === "all" || self.selectedSection() === id;
      };

      // ── Summary cards ──
      self.loaded = ko.observable(false);
      self.sourceDb = ko.observable("");
      self.sectionErrors = ko.observableArray([]);

      self.truncStatus = ko.pureComputed(function () {
        var r = sectionByKey("trunc_point").rows()[0];
        return r ? (r.secondary_truncation_point || "UNKNOWN") : "-";
      });
      self.logUsedPct = ko.pureComputed(function () {
        var r = sectionByKey("log_space").rows()[0];
        return r ? parseFloat(r.log_used_pct || 0) : 0;
      });
      self.repTablesSummary = ko.pureComputed(function () {
        var rows = sectionByKey("rep_tables").rows();
        var userRows = rows.filter(function (r) { return !/^ckpt(_lox)?$/i.test(r.table_name); });
        var yes = userRows.filter(function (r) { return r.replicated === "YES"; }).length;
        return yes + " / " + userRows.length;
      });
      self.blockingCount = ko.pureComputed(function () { return sectionByKey("blocking").rows().length; });
      self.longRunCount  = ko.pureComputed(function () { return sectionByKey("long_running").rows().length; });

      self.cardClass = function (level) {
        return {
          ok:   "oj-bg-success-20",
          warn: "oj-bg-warning-20",
          bad:  "oj-bg-danger-20",
        }[level] || "";
      };
      self.truncLevel = ko.pureComputed(function () { return self.truncStatus() === "VALID" ? "ok" : "bad"; });
      self.logLevel   = ko.pureComputed(function () {
        var p = self.logUsedPct();
        return p >= 85 ? "bad" : p >= 70 ? "warn" : "ok";
      });

      // ── Run troubleshoot ──
      self.IETShoot = function () {
        if (!self.currentDB()) return;
        $.ajax({
          url: self.DepName() + "/api/v2/ie-tshoot",
          type: "POST",
          contentType: "application/json",
          data: JSON.stringify({ dbname: self.currentDB() }),
          dataType: "json",
          timeout: 120000,
          progressMessage: "Analyzing Sybase extract source",
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

            self.sections.forEach(function (s) {
              var rows = (data[s.key] || []).map(function (r) {
                var copy = {};
                Object.keys(r).forEach(function (k) { copy[k || "value"] = r[k]; });
                return copy;
              });
              var keys = [];
              rows.forEach(function (r) {
                Object.keys(r).forEach(function (k) { if (keys.indexOf(k) < 0) keys.push(k); });
              });
              s.columns(keys.map(function (k) { return { headerText: prettify(k), field: k }; }));
              s.rows(rows);
              s.error(errs[s.key] ? String(errs[s.key]).replace(/^\("|",\s*\d+\)$/g, "") : "");
            });

            self.sectionErrors(Object.keys(errs).map(function (k) {
              var sec = sectionByKey(k);
              return { section: sec ? sec.title : k, message: String(errs[k]) };
            }));
            self.sourceDb(data.sourcedb || "");
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
  return ietshootViewModel;
});