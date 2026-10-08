define([
  "ojs/ojcore",
  "knockout",
  "jquery",
  "appController",
  "ojs/ojtranslation",
  "ojs/ojconverter-number",
  "ojs/ojconverterutils-i18n",
  "ojs/ojconverter-datetime",
  "ojs/ojarraydataprovider",
  "ojs/ojpagingdataproviderview",
  "ojs/ojmutablearraydataprovider",
  "ojs/ojmasonrylayout",
  "ojs/ojtable",
  "ojs/ojselectsingle",
  "ojs/ojbutton",
  "ojs/ojinputnumber",
  "ojs/ojdatetimepicker",
  "ojs/ojinputtext",
  "ojs/ojdialog",
  "ojs/ojmenu",
  "ojs/ojoption",
  "ojs/ojselectcombobox",
  "ojs/ojavatar",
  "ojs/ojlabel",
  "ojs/ojlabelvalue",
  "ojs/ojprogress-bar",
  "ojs/ojcheckboxset",
  "ojs/ojformlayout",
  "ojs/ojradioset",
  "ojs/ojvalidationgroup",
  "ojs/ojpagingcontrol",
  "oj-c/card-view",
  "oj-c/action-card",
  "oj-c/menu-button",
], function (
  oj,
  ko,
  $,
  app,
  Translations,
  NumberConverter,
  ConverterUtilsI18n,
  DateTimeConverter,
  ArrayDataProvider,
  PagingDataProviderView,
  MutableArrayDataProvider,
) {
  class ManageViewModel {
    constructor(args) {
      var self = this;
      self.DepName = args.routerState.detail.dep_url;
      self.MgrName = ko.observable();
      self.ExtName = null;
      self.PmpName = null;
      self.RepName = null;
      self.maxRowsStretch = ko.observable();
      self.dynamicPortList = ko.observable();
      self.mgrPortCheck = ko.observable(true);
      self.dynamicPortListCheck = ko.observable(false);
      self.dynamicPortListCheckEnable = ko.observable(false);
      self.style = ko.observable();

      if (self.dynamicPortListCheckEnable == false) {
        self.dynamicPortListCheck == false;
      }

      self.ExtATCSN = ko.observable();
      self.RepATCSN = ko.observable();
      self.RepAFTERCSN = ko.observable();
      self.groupValid = ko.observable();

      self.mgrCount = ko.observable(0);
      self.extCount = ko.observable(0);
      self.pmpCount = ko.observable(0);
      self.repCount = ko.observable(0);

      self.MgrData1 = ko.observableArray([]);
      self.ExtData1 = ko.observableArray([]);
      self.PmpData1 = ko.observableArray([]);
      self.RepData1 = ko.observableArray([]);
      self.repStats = ko.observableArray([]);

      self.ExtAFTERCSN = ko.observable();

      self.extPrmWrite = ko.observableArray([]);
      self.extPrmRead = ko.observableArray([]);

      self.pmpPrmWrite = ko.observableArray([]);
      self.pmpPrmRead = ko.observableArray([]);

      self.decimalHalfDownConverter = new NumberConverter.IntlNumberConverter({
        style: "decimal",
        roundingMode: "HALF_DOWN",
        maximumFractionDigits: 0,
        useGrouping: false,
      });

      self.getCardStyle = function (status) {
        var colorMap = {
          running: "ForestGreen",
          starting: "Chocolate",
          stopped: "Chocolate",
          killed: "IndianRed",
          abended: "IndianRed",
        };

        var normalizedStatus = status ? status.toLowerCase() : "";

        return {
          "background-color": colorMap[normalizedStatus] || "#546e7a",
          color: "#ffffff",
          "border-radius": "8px",
          "box-shadow": "0 2px 6px rgba(0,0,0,0.2)",
        };
      };

      self.getMgrMenuItems = function (extData) {
        return [
          {
            key: "mgredit",
            label: "Edit Manager Params",
            startIcon: { class: "fa fa-pencil" },
          },
          { type: "separator" },
          {
            key: "mgrstart",
            label: "START",
            startIcon: { class: "fas fa-play-circle bg_green" },
          },
          { type: "separator" },
          {
            key: "mgrstop",
            label: "Stop",
            startIcon: { class: "fas fa-stop" },
          },
          { type: "separator" },
          {
            key: "mgrkill",
            label: "Kill",
            startIcon: { class: "fa fa-window-close bg_red" },
          },
          { type: "separator" },
          {
            key: "mgrrefresh",
            label: "Refresh",
            startIcon: { class: "fa fa-refresh" },
          },
          { type: "separator" },
          {
            type: "submenu",
            label: "View",
            items: [
              {
                key: "mgrrpt",
                label: "View Report",
                startIcon: { class: "fas fa-file-alt" },
              },
              {
                key: "mgrchildstatus",
                label: "Child Process Status",
                startIcon: { class: "fas fa-tasks" },
              },
              {
                key: "mgrportinfo",
                label: "Port Info Detail",
                startIcon: { class: "fas fa-network-wired" },
              },
              {
                key: "mgrpurgeold",
                label: "PURGEOLDEXTRACTS",
                startIcon: { class: "fas fa-trash-alt" },
              },
            ],
          },
        ];
      };

      self.getExtMenuItems = function (extData) {
        return [
          {
            key: "extedit",
            label: "Edit Extract Params",
            startIcon: { class: "fa fa-pencil" },
          },
          { type: "separator" },

          {
            type: "submenu",
            label: "View",
            items: [
              {
                key: "extrpt",
                label: "View Report",
                startIcon: { class: "fas fa-file-alt" },
              },
              {
                key: "extchk",
                label: "View Checkpoint",
                startIcon: { class: "fas fa-check-circle" },
              },
              {
                key: "extstats",
                label: "View Stats",
                startIcon: { class: "fas fa-chart-bar" },
              },
            ],
          },
          { type: "separator" },

          {
            type: "submenu",
            label: "Start",
            items: [
              {
                key: "extstartdef",
                label: "START",
                startIcon: { class: "fas fa-play-circle bg_green" },
              },
              {
                key: "extatcsn",
                label: "ATCSN",
                startIcon: { class: "fas fa-clock" },
              },
              {
                key: "extaftercsn",
                label: "AFTERCSN",
                startIcon: { class: "fas fa-forward" },
              },
            ],
          },
          { type: "separator" },

          {
            type: "submenu",
            label: "Stop",
            items: [
              {
                key: "extstop",
                label: "Stop",
                startIcon: { class: "fas fa-stop bg_red" },
              },
              {
                key: "extforcestop",
                label: "Force Stop",
                startIcon: { class: "fas fa-power-off" },
              },
              {
                key: "extkill",
                label: "Kill",
                startIcon: { class: "fas fa-times-circle" },
              },
            ],
          },
          { type: "separator" },

          {
            type: "submenu",
            label: "Alter",
            items: [
              {
                key: "extetroll",
                label: "Extract Trail Rollover",
                startIcon: { class: "fas fa-rotate-right bg_red" },
              },
              {
                key: "extbegin",
                label: "Begin Now/Time/SCN",
                startIcon: { class: "fas fa-play" },
              },
            ],
          },

          { type: "separator" },

          {
            type: "submenu",
            label: "Show",
            items: [
              {
                key: "cachemgr",
                label: "Extract Cache Statistics",
                startIcon: { class: "fas fa-database" },
              },
              {
                key: "extshowtrans",
                label: "Open Transactions",
                startIcon: { class: "fas fa-list" },
              },
              {
                key: "extstatus",
                label: "Current Read/Write Status",
                startIcon: { class: "fas fa-info-circle" },
              },
            ],
          },
          { type: "separator" },
          {
            type: "submenu",
            label: "Add",
            items: [
              {
                key: "exttrailadd",
                label: "Add Trail",
                startIcon: { class: "fas fa-stream" },
              },
            ],
          },
          { type: "separator" },

          {
            type: "submenu",
            label: "Delete",
            items: [
              {
                key: "extdel",
                label: "Delete Extract",
                startIcon: { class: "fas fa-trash" },
              },
              {
                key: "exttraildel",
                label: "Delete Extract Trail",
                startIcon: { class: "fas fa-trash" },
              },
            ],
          },
          { type: "separator" },
          {
            key: "extunreg",
            label: "Unregister Extract",
            startIcon: { class: "fas fa-user-xmark" },
          },
        ];
      };

      self.getPmpMenuItems = function (extData) {
        return [
          {
            key: "extedit",
            label: "Edit Pump Params",
            startIcon: { class: "fa fa-pencil" },
          },
          { type: "separator" },

          {
            type: "submenu",
            label: "View",
            items: [
              {
                key: "extrpt",
                label: "View Report",
                startIcon: { class: "fas fa-file-alt" },
              },
              {
                key: "extchk",
                label: "View Checkpoint",
                startIcon: { class: "fas fa-check-circle" },
              },
              {
                key: "extstats",
                label: "View Stats",
                startIcon: { class: "fas fa-chart-bar" },
              },
            ],
          },
          { type: "separator" },

          {
            type: "submenu",
            label: "Start",
            items: [
              {
                key: "extstartdef",
                label: "START",
                startIcon: { class: "fas fa-play-circle bg_green" },
              },
              {
                key: "extatcsn",
                label: "ATCSN",
                startIcon: { class: "fas fa-clock" },
              },
              {
                key: "extaftercsn",
                label: "AFTERCSN",
                startIcon: { class: "fas fa-forward" },
              },
            ],
          },
          { type: "separator" },

          {
            type: "submenu",
            label: "Stop",
            items: [
              {
                key: "extstop",
                label: "Stop",
                startIcon: { class: "fas fa-stop bg_red" },
              },
              {
                key: "extforcestop",
                label: "Force Stop",
                startIcon: { class: "fas fa-power-off" },
              },
              {
                key: "extkill",
                label: "Kill",
                startIcon: { class: "fas fa-times-circle" },
              },
            ],
          },
          { type: "separator" },

          {
            type: "submenu",
            label: "Alter",
            items: [
              {
                key: "extetroll",
                label: "Extract Trail Rollover",
                startIcon: { class: "fas fa-rotate-right" },
              },
              {
                key: "extbegin",
                label: "Begin Now/Time/SCN",
                startIcon: { class: "fas fa-play" },
              },
            ],
          },

          { type: "separator" },
          {
            key: "extstatus",
            label: "Current Read/Write Status",
            startIcon: { class: "fas fa-info-circle" },
          },
          { type: "separator" },
          {
            type: "submenu",
            label: "Add",
            items: [
              {
                key: "exttrailadd",
                label: "Add Remote Trail",
                startIcon: { class: "fas fa-stream" },
              },
            ],
          },
          { type: "separator" },

          {
            type: "submenu",
            label: "Delete",
            items: [
              {
                key: "pmpdel",
                label: "Delete Pump",
                startIcon: { class: "fas fa-trash" },
              },
              {
                key: "extdelrmt",
                label: "Delete Remote Trail",
                startIcon: { class: "fas fa-trash" },
              },
            ],
          },
        ];
      };

      self.getRepMenuItems = function (repData) {
        return [
          {
            key: "repedit",
            label: "Edit Replicat Params",
            startIcon: { class: "fa fa-pencil" },
          },
          { type: "separator" },

          {
            type: "submenu",
            label: "View",
            items: [
              {
                key: "reprpt",
                label: "View Report",
                startIcon: { class: "fas fa-file-alt" },
              },
              {
                key: "repchk",
                label: "View Checkpoint",
                startIcon: { class: "fas fa-check-circle" },
              },
              {
                key: "repstats",
                label: "View Stats",
                startIcon: { class: "fas fa-chart-bar" },
              },
              {
                key: "cdrstats",
                label: "View CDR Conflicts",
                startIcon: { class: "fas fa-chart-bar" },
              },
            ],
          },
          { type: "separator" },

          {
            type: "submenu",
            label: "Start",
            items: [
              {
                key: "repstartdef",
                label: "START",
                startIcon: { class: "fas fa-play-circle bg_green" },
              },
              {
                key: "repatcsn",
                label: "ATCSN",
                startIcon: { class: "fas fa-clock" },
              },
              {
                key: "repaftercsn",
                label: "AFTERCSN",
                startIcon: { class: "fas fa-forward" },
              },
            ],
          },
          { type: "separator" },

          {
            type: "submenu",
            label: "Stop",
            items: [
              {
                key: "repstop",
                label: "Stop",
                startIcon: { class: "fas fa-stop bg_red" },
              },
              {
                key: "repforcestop",
                label: "Force Stop",
                startIcon: { class: "fas fa-power-off" },
              },
              {
                key: "repkill",
                label: "Kill",
                startIcon: { class: "fas fa-times-circle" },
              },
            ],
          },
          { type: "separator" },

          {
            type: "submenu",
            label: "Alter",
            items: [
              {
                key: "repbegin",
                label: "Begin Now/Time/SCN",
                startIcon: { class: "fas fa-play" },
              },
            ],
          },

          { type: "separator" },

          {
            type: "submenu",
            label: "Show",
            items: [
              {
                key: "cachemgr",
                label: "Replicat Cache Statistics",
                startIcon: { class: "fas fa-database" },
              },
              {
                key: "repstatus",
                label: "Current Read/Write Status",
                startIcon: { class: "fas fa-info-circle" },
              },
            ],
          },
          { type: "separator" },

          {
            type: "submenu",
            label: "Delete",
            items: [
              {
                key: "repdel",
                label: "Delete Replicat",
                startIcon: { class: "fas fa-trash" },
              },
            ],
          },
        ];
      };

      self.bulkMenuItems = [
        {
          id: "startall",
          label: "Start All",
          startIcon: { class: "fas fa-play-circle" },
        },
        {
          id: "stopall",
          label: "Stop All",
          startIcon: { class: "fas fa-stop-circle" },
        },
        {
          id: "statusall",
          label: "Status All",
          startIcon: { class: "fas fa-info-circle" },
        },
      ];

      self.bulkMenuAction = function (event) {
        var itemId = event.detail.selectedValue;
      };

      self.MgrDataProvider = new MutableArrayDataProvider(self.MgrData1, {
        keyAttributes: "MgrName",
      });
      self.ExtDataProvider = new MutableArrayDataProvider(self.ExtData1, {
        keyAttributes: "ExtName",
      });

      self.PmpDataProvider = new MutableArrayDataProvider(self.PmpData1, {
        keyAttributes: "PmpName",
      });
      self.RepDataProvider = new MutableArrayDataProvider(self.RepData1, {
        keyAttributes: "RepName",
      });

      var refreshXHR = null;
      var monAll = null;
      function refresh(showLoader) {
        if (refreshXHR) refreshXHR.abort();
        refreshXHR = $.ajax({
          url: self.DepName() + "/api/v2/info/all",
          type: "GET",
          dataType: "json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          showProgress: showLoader ? true : false,
          progressMessage: "Fetching process status",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort" || xhr.statusText === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };            
            if(xhr.status == 0){
              app.showGlobalError(self.deploymentUnreachableMessage(), "Connection Error");
              return
            }
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to fetch process status. ${msg}`,
              "Refresh Error",
            );
          },
          success: function (data) {
            console.log(data);
            
            var newMgrItems = [];
            var newExtItems = [];
            var newPmpItems = [];
            var newRepItems = [];
            for (var i = 0; i < data[0].length; i++) {
              if (data[0][i].extstat) {
                newExtItems.push({
                  ExtName: data[0][i].extname,
                  ExtStat: data[0][i].extstat,
                  styleExt: self.getCardStyle(data[0][i].extstat),
                });
              }
              if (data[0][i].pmpstat) {
                newPmpItems.push({
                  PmpName: data[0][i].pmpname,
                  PmpStat: data[0][i].pmpstat,
                  stylePmp: self.getCardStyle(data[0][i].pmpstat),
                });
              }
              if (data[0][i].repstat) {
                newRepItems.push({
                  RepName: data[0][i].repname,
                  RepStat: data[0][i].repstat,
                  styleRep: self.getCardStyle(data[0][i].repstat),
                });
              }
              if (data[0][i].mgrstat) {
                newMgrItems.push({
                  MgrName: "Manager",
                  MgrStat: data[0][i].mgrstat,
                  styleMgr: self.getCardStyle(data[0][i].mgrstat),
                });
              }
            }
            self.MgrDataProvider.data = newMgrItems;
            self.MgrData1 = newMgrItems;
            self.mgrCount(newMgrItems.length);

            self.ExtDataProvider.data = newExtItems;
            self.ExtData1 = newExtItems;
            self.extCount(newExtItems.length);

            self.PmpDataProvider.data = newPmpItems;
            self.PmpData1 = newPmpItems;
            self.pmpCount(newPmpItems.length);

            self.RepDataProvider.data = newRepItems;
            self.RepData1 = newRepItems;
            self.repCount(newRepItems.length);

            return self;
          },
        });
      }

      self.currentbeginmode = ko.observable("Now");

      self.beginmode = ko.observableArray([
        { value: "Now", label: "Begin Now" },
        { value: "Time", label: "Custom Time" },
        { value: "LOC", label: "Location" },
      ]);

      self.startOptionDP = new ArrayDataProvider(self.beginmode, {
        keyAttributes: "value",
      });

      self.currentExtBeginMode = ko.observable("Now");

      self.currentPmpBeginMode = ko.observable("");

      self.extBeginMode = ko.observableArray([
        { value: "Now", label: "Begin Now" },
        { value: "Time", label: "Custom Time" },
        { value: "SCN", label: "SCN" },
      ]);

      self.extStartOptionDP = new ArrayDataProvider(self.extBeginMode, {
        keyAttributes: "value",
      });

      self.secondConverter = new DateTimeConverter.IntlDateTimeConverter({
        pattern: "yyyy-MM-dd HH:mm:ss",
      });

      self.ctvalue = ko.observable(
        ConverterUtilsI18n.IntlConverterUtils.dateToLocalIso(new Date()),
      );

      self.seqnovalue = ko.observable(0);
      self.rbavalue = ko.observable(0);

      self.decimalHalfDownConverter = new NumberConverter.IntlNumberConverter({
        style: "decimal",
        roundingMode: "HALF_DOWN",
        maximumFractionDigits: 0,
        useGrouping: false,
      });

      self.args = args;
      self.router = self.args.parentRouter;

      self.selectedExtractMenuItem = ko.observable("");
      self.selectedPumpMenuItem = ko.observable("");
      self.selectedReplicatMenuItem = ko.observable("");
      self.stopTextValue = ko.observable("");
      var parameter = "";

      self.menuExtractItemAction = function (event) {
        self.selectedExtractMenuItem(event.target.value);
        //Manager Report File
        if (self.selectedExtractMenuItem() == "addext") {
          self.router.go({ path: "Designer" });
        } else if (self.selectedExtractMenuItem() == "stopallext") {
          self.delTitle("Stop All Primary Extracts ?");
          self.stopTextValue(
            "This Action will stop all Primary Extracts . Do you want to continue ?",
          );
          document.querySelector("#StopAllProcessDialog").open();
          refresh();
          parameter = {
            ops: self.selectedExtractMenuItem(),
            processName: self.ExtData1(),
          };
        } else if (self.selectedExtractMenuItem() == "startallext") {
          parameter = {
            ops: self.selectedExtractMenuItem(),
            processName: self.ExtData1(),
          };
          self.delTitle("Start All Primary Extracts");
          refresh();
          ProcessAction();
        }
      };

      self.stopAllProc = function (data, event) {
        document.querySelector("#StopAllProcessDialog").close();
        ProcessAction();
      };

      self.menuPumpItemAction = function () {
        self.selectedPumpMenuItem(event.target.value);
        //Manager Report File
        if (self.selectedPumpMenuItem() == "addpmp") {
          self.router.go({ path: "Designer" });
        } else if (self.selectedPumpMenuItem() == "stopallpmp") {
          self.delTitle("Stop All Pump Extracts ?");
          self.stopTextValue(
            "This Action will stop all Pump Extracts . Do you want to continue ?",
          );
          document.querySelector("#StopAllProcessDialog").open();
          parameter = {
            ops: self.selectedPumpMenuItem(),
            processName: self.PmpData1(),
          };
        } else if (self.selectedPumpMenuItem() == "startallpmp") {
          parameter = {
            ops: self.selectedPumpMenuItem(),
            processName: self.PmpData1(),
          };
          self.delTitle("Start All Pump Extracts");
          ProcessAction();
        }
      };

      self.menuReplicatItemAction = function () {
        self.selectedReplicatMenuItem(event.target.value);
        //Manager Report File
        if (self.selectedReplicatMenuItem() == "addrep") {
          self.router.go({ path: "Designer" });
        } else if (self.selectedReplicatMenuItem() == "stopallrep") {
          self.delTitle("Stop All Replicats ?");
          self.stopTextValue(
            "This Action will stop all Replicats . Do you want to continue ?",
          );
          document.querySelector("#StopAllProcessDialog").open();
          parameter = {
            ops: self.selectedReplicatMenuItem(),
            processName: self.RepData1(),
          };
        } else if (self.selectedReplicatMenuItem() == "startallrep") {
          parameter = {
            ops: self.selectedReplicatMenuItem(),
            processName: self.RepData1(),
          };

          self.delTitle("Start All Replicats");
          ProcessAction();
        }
      };

      function ProcessAction() {
        self.ExtRpt([]);
        $.ajax({
          url: self.DepName() + "/api/v2/process/action",
          type: "POST",
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          data: JSON.stringify(parameter),
          context: self,
          progressMessage: "Processing action",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to complete process action. ${msg}`,
              "Process Action Error",
            );
          },
          success: function (data) {
            self.popUpResizeSM("ViewExtractRptDialog");
            document.querySelector("#ViewExtractRptDialog").open();
            self.ExtRpt(data[0]);
            return self;
          },
        });
      }

      self.CancelBehaviorOpt = ko.observable("icon");

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

      function getDomains() {
        self.username1([]);
        self.othdom([]);
        self.aliasname1([]);
        self.domname1([]);
        self.selectedAliascategory("");
        self.selectedUsercategory("");
        self.uName("");
        self.uPasswd("");
        self.uRepPass("");
        self.valdom("");
        $.ajax({
          url: self.DepName() + "/api/v2/vault/info/all",
          type: "GET",
          dataType: "json",
          timeout: sessionStorage.getItem("timeInetrval"),
          progressMessage: "Fetching credential domains",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to fetch credential domains. ${msg}`,
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
      self.domname1DP = new ArrayDataProvider(self.domname1, {
        keyAttributes: "value",
      });

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

      self.aliascategoriesDP = new ArrayDataProvider(self.aliascategories, {
        keyAttributes: "value",
      });

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

      self.chkTblList = ko.observableArray([]);
      self.currentChkptTbl = ko.observable();

      self.infoChkptTbl = function (event, data) {
        self.chkTblList([]);
        self.currentChkptTbl("");
        $.ajax({
          url: self.DepName() + "/api/v2/chkpt/info",
          type: "POST",
          data: JSON.stringify({
            domain: self.selectedDomCategory(),
            alias: self.selectedAliascategory(),
          }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          progressMessage: "Fetching checkpoint table info",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to fetch checkpoint table info. ${msg}`,
              "Checkpoint Table Error",
            );
          },
          success: function (data) {
            for (var i = 0; i < data[0].length; i++) {
              self.chkTblList.push({ label: data[0][i], value: data[0][i] });
            }
            return self;
          },
        });
      };
      self.chkpttblDP = new ArrayDataProvider(self.chkTblList, {
        keyAttributes: "value",
      });

      self.dialogStyle = ko.observable();

      //**************************************************************************** */
      // Manager Functions
      //**************************************************************************** */

      function mgrOper() {
        self.MgrRpt([]);
        $.ajax({
          url: self.DepName() + "/api/v2/mgr/ops",
          type: "POST",
          dataType: "json",
          contentType: "application/json",
          data: JSON.stringify({ mgrOps: self.selectedMgrMenuItem() }),
          context: self,
          progressMessage: "Processing manager operation",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to complete manager operation. ${msg}`,
              "Manager Operation Error",
            );
          },
          success: function (data) {
            document.querySelector("#ViewMgrRptDialog").open();
            self.MgrRpt(data[0]);
            return self;
          },
        });
      }
      self.MgrRpt = ko.observableArray([]);
      self.selectedMgrMenuItem = ko.observable("");

      self.menuMgrItemAction = function (mgrData) {
        return function (event) {
          self.selectedMgrMenuItem(event.detail.key);
          //Manager Report File
          if (self.selectedMgrMenuItem() == "mgrrpt") {
            self.MgrRpt([]);
            $.ajax({
              url: self.DepName() + "/api/v2/mgr/report",
              type: "GET",
              dataType: "json",
              timeout: sessionStorage.getItem("timeInetrval"),
              context: self,
              progressMessage: "Fetching manager report",
              suppressGlobalError: true,
              error: function (xhr, textStatus) {
                if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
                var msg = app.extractErrorMessage(xhr);
                app.showGlobalError(
                  `Unable to fetch manager report. ${msg}`,
                  "Manager Report Error",
                );
              },
              success: function (data) {
                self.popUpResize("ViewMgrRptDialog");
                document.querySelector("#ViewMgrRptDialog").open();
                self.MgrRpt(data[0]);
                return self;
              },
            });
          } else if (self.selectedMgrMenuItem() == "mgredit") {
            self.mgrPrmRead([]);
            $.ajax({
              url: self.DepName() + "/api/v2/params/manager",
              type: "GET",
              dataType: "json",
              timeout: sessionStorage.getItem("timeInetrval"),
              context: self,
              progressMessage: "Fetching manager parameters",
              suppressGlobalError: true,
              error: function (xhr, textStatus) {
                if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
                var msg = app.extractErrorMessage(xhr);
                app.showGlobalError(
                  `Unable to fetch manager parameters. ${msg}`,
                  "Manager Parameters Error",
                );
              },
              success: function (data) {
                self.popUpResizeSM("ViewMgrRptDialog");
                document.querySelector("#EditMgrDialog").open();
                self.mgrPrmRead(data[0]);
                return self;
              },
            });
          } else if (
            self.selectedMgrMenuItem() == "mgrstart" ||
            self.selectedMgrMenuItem() == "mgrrefresh"
          ) {
            self.popUpResizeSM("ViewMgrRptDialog");
            refresh();
            mgrOper();
          } else if (
            self.selectedMgrMenuItem() == "mgrchildstatus" ||
            self.selectedMgrMenuItem() == "mgrportinfo" ||
            self.selectedMgrMenuItem() == "mgrpurgeold"
          ) {
            self.popUpResize("ViewMgrRptDialog");
            mgrOper();
          } else if (self.selectedMgrMenuItem() == "mgrstop") {
            self.popUpResizeSM("ViewMgrRptDialog");
            refresh();
            document.querySelector("#StopMgrDialog").open();
          } else if (self.selectedMgrMenuItem() == "mgrkill") {
            self.popUpResizeSM("ViewMgrRptDialog");
            refresh();
            document.querySelector("#KillMgrDialog").open();
          }
        };
      };
      self.ViewMgrRptOKClose = function (event) {
        refresh();
        document.querySelector("#ViewMgrRptDialog").close();
      };

      self.mgrPrmRead = ko.observable();
      self.mgrPrmWrite = ko.observable();

      self.stopMgr = function (event, data) {
        document.querySelector("#StopMgrDialog").close();
        mgrOper();
      };

      self.killMgr = function (event, data) {
        document.querySelector("#KillMgrDialog").close();
        mgrOper();
      };

      self.saveMgrPrm = function (event, data) {
        $.ajax({
          url: self.DepName() + "/api/v2/params/manager",
          type: "POST",
          dataType: "json",
          contentType: "application/json",
          data: JSON.stringify({ currentMgrParams: self.mgrPrmWrite() }),
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Saving manager parameters",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to save manager parameters. ${msg}`,
              "Save Manager Parameters Error",
            );
          },
          success: function (data) {
            document.querySelector("#EditMgrDialog").close();
            document.querySelector("#ViewMgrRptDialog").open();
            self.MgrRpt(data[0]);
            return self;
          },
        });
      };
      //**************************************************************************** */
      // Extract Functions
      //**************************************************************************** */

      self.ExtRpt = ko.observableArray([]);
      self.addExtTrailName = ko.observable();
      self.addExtTrailType = ko.observable("exttrail");
      self.addExtTrailSize = ko.observable("500");
      self.DBLoginTitle = ko.observable();
      self.extStats = ko.observableArray([]);

      self.selectedMenuItem = ko.observable();
      self.ExtOpenTrans = ko.observableArray([]);

      function getOpenTrans() {
        self.ExtOpenTrans([]);
        $.ajax({
          url: self.DepName() + "/api/v2/extract/showtrans",
          data: JSON.stringify({ extname: self.ExtName }),
          type: "POST",
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Fetching open transactions",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to fetch open transactions. ${msg}`,
              "Open Transactions Error",
            );
          },
          success: function (data) {
            self.ExtOpenTrans(data[0]);
            document.querySelector("#ViewExtOpenTransDialog").open();
            return self;
          },
        });
      }
      self.popUpResize = (value) => {
        document.getElementById(value).style.width = "1150px";
        document.getElementById(value).style.height = "80vh";
      };

      self.popUpResizeMD = (value) => {
        document.getElementById(value).style.width = "500px";
        document.getElementById(value).style.height = "60vh";
      };

      self.popUpResizeSM = (value) => {
        document.getElementById(value).style.width = "500px";
        document.getElementById(value).style.height = "45vh";
      };

      self.extRptIsTable = ko.observable(false);

      self.extInfoRows = ko.observableArray([]);
      self.extReadRows = ko.observableArray([]);
      self.extWriteRows = ko.observableArray([]);

      self.extInfoColumnArray = [
        { headerText: "", field: "property", width: 170 },
        { headerText: "", field: "value", width: 330 },
      ];
      self.extReadColumnArray = [
        { headerText: "", field: "property", width: 170 },
        { headerText: "", field: "value", width: 330 },
      ];
      self.extWriteColumnArray = [
        { headerText: "", field: "property", width: 170 },
        { headerText: "", field: "value", width: 330 },
      ];

      self.extInfoDP = new ArrayDataProvider(self.extInfoRows, { keyAttributes: "id" });
      self.extReadDP = new ArrayDataProvider(self.extReadRows, { keyAttributes: "id" });
      self.extWriteDP = new ArrayDataProvider(self.extWriteRows, { keyAttributes: "id" });

      self.extStatusSections = ko.observableArray([]);
      self.selectedExtStatusIndex = ko.observable(0);

      self.selectExtStatusSection = function (index) {
        return function () {
          self.selectedExtStatusIndex(index);
        };
      };

      self.selectedExtStatusData = ko.computed(function () {
        var sections = self.extStatusSections();
        var idx = self.selectedExtStatusIndex();
        return sections[idx] || null;
      });

      function extStatusSectionMeta(title) {
        var t = title.toUpperCase();
        if (t.indexOf("INFORMATION") > -1) return { icon: "information", type: "info" };
        if (t.indexOf("READ") > -1) return { icon: "download", type: "read" };
        if (t.indexOf("WRITE") > -1) return { icon: "upload", type: "write" };
        return { icon: "information", type: "default" };
      }

function buildExtractReportSections(lines) {
  var info = [];
  var read = [];
  var write = [];
  var idx = 0;
  var target = null;
  var started = false;
  var arr = Array.isArray(lines) ? lines : (lines || "").toString().split("\n");

  arr.forEach(function (rawLine) {
    var trimmed = (rawLine || "").trim();
    if (!trimmed) return;

    if (!started) {
      var extractIdx = trimmed.search(/EXTRACT\s+\S+\s*\(PID\s+\d+\)/i);
      if (extractIdx > -1) {
        started = true;
        var match = trimmed.match(/EXTRACT\s+(\S+)\s*\(PID\s+(\d+)\)/i);
        if (match) {
          info.push({ id: idx++, property: "Extract Name", value: match[1] });
          info.push({ id: idx++, property: "PID", value: match[2] });
        } else {
          info.push({ id: idx++, property: trimmed, value: "" });
        }
        target = "info";
      }
      return;
    }

    var colonIdx = trimmed.indexOf(":");
    if (colonIdx === -1) return;

    var property = trimmed.substring(0, colonIdx).trim();
    var value = trimmed.substring(colonIdx + 1).trim();

    if (!value) {
      if (/read position/i.test(property)) target = "read";
      else if (/write position/i.test(property)) target = "write";
      else target = "info";
      return;
    }

    if (property === "Current status") property = "Current Status";
    if (property === "Extract Trail") target = "info";

    var row = { id: idx++, property: property, value: value };
    if (target === "read") read.push(row);
    else if (target === "write") write.push(row);
    else info.push(row);
  });

  var rawSections = [
    { title: "Extract Information", rows: info },
    { title: "Current Read Position", rows: read },
    { title: "Current Write Position", rows: write },
  ].filter(function (s) { return s.rows.length > 0; });

  return rawSections.map(function (s, i) {
    var meta = extStatusSectionMeta(s.title);
    return {
      idx: i,
      title: s.title,
      icon: meta.icon,
      iconType: meta.type,
      rowCount: s.rows.length,
      dp: new ArrayDataProvider(s.rows, { keyAttributes: "id" }),
    };
  });
}

function isExtractStatusReport(lines) {
  var arr = Array.isArray(lines) ? lines : (lines || "").toString().split("\n");
  var text = arr.join(" ");
  return /EXTRACT\s+\S+\s*\(PID/i.test(text) && /read position/i.test(text) && /write position/i.test(text);
}

self.extRptIsCacheMgr = ko.observable(false);
self.cacheMgrSections = ko.observableArray([]); // [{ title, dp }]

self.cacheMgrColumnArray = [
  { headerText: "", field: "property", width: 240 },
  { headerText: "", field: "value", width: 280 },
];

function isCacheSectionHeader(line) {
  if (!line) return false;
  if (line.indexOf("=") > -1) return false;
  if (line.indexOf(":") > -1 && !/^[A-Z0-9 #\-\/\(\)]+:$/.test(line)) return false;
  var lettersOnly = line.replace(/[^A-Za-z]/g, "");
  if (!lettersOnly || lettersOnly.length < 3) return false;
  return lettersOnly === lettersOnly.toUpperCase() && line.length < 80;
}

function parseCacheEqualsLine(line) {
  var rows = [];
  var regex = /([^=]+?)=\s*(\S+)/g;
  var match;
  while ((match = regex.exec(line)) !== null) {
    var property = match[1].trim();
    var value = match[2].trim();
    if (property) {
      rows.push({ property: property, value: value });
    }
  }
  return rows;
}

function parseCachePipeLine(line) {
  var rows = [];
  line.split("|").forEach(function (chunk) {
    var colonIdx = chunk.indexOf(":");
    if (colonIdx > -1) {
      var property = chunk.substring(0, colonIdx).trim();
      var value = chunk.substring(colonIdx + 1).trim();
      if (property && value !== undefined) {
        rows.push({ property: property, value: value });
      }
    }
  });
  return rows;
}

function cacheSectionMeta(title) {
  var t = title.toUpperCase();
  if (t.indexOf("VM USAGE") > -1) return { icon: "chart-bar", type: "vm" };
  if (t.indexOf("CONFIGURATION") > -1) return { icon: "settings", type: "config" };
  if (t.indexOf("RUNTIME") > -1) return { icon: "play-circle", type: "runtime" };
  if (t.indexOf("CUMULATIVE") > -1) return { icon: "history", type: "cumulative" };
  if (t.indexOf("FILE CACHING") > -1) return { icon: "folder", type: "file" };
  if (t.indexOf("MANAGEMENT") > -1) return { icon: "cog", type: "mgmt" };
  if (t.indexOf("QUEUE") > -1) return { icon: "list", type: "queue" };
  if (t.indexOf("POOL") > -1) return { icon: "database", type: "pool" };
  return { icon: "information", type: "default" };
}

function buildCacheMgrSections(lines) {
  var sections = [];
  var current = null;
  var idx = 0;
  var arr = Array.isArray(lines) ? lines : (lines || "").toString().split("\n");

  arr.forEach(function (rawLine) {
    var trimmed = (rawLine || "").trim();
    if (!trimmed) return;
    if (/^-{3,}$/.test(trimmed) || /^={3,}$/.test(trimmed)) return;
    if (/^(Close|Operating system|Sending)/i.test(trimmed)) return;

    if (isCacheSectionHeader(trimmed)) {
      current = { title: trimmed.replace(/:$/, ""), rows: [] };
      sections.push(current);
      return;
    }

    if (!current) {
      current = { title: "General", rows: [] };
      sections.push(current);
    }

    var pairs = [];
    if (trimmed.indexOf("=") > -1) {
      pairs = parseCacheEqualsLine(trimmed);
    } else if (trimmed.indexOf("|") > -1) {
      pairs = parseCachePipeLine(trimmed);
    } else if (trimmed.indexOf(":") > -1) {
      var colonIdx = trimmed.indexOf(":");
      pairs = [{ property: trimmed.substring(0, colonIdx).trim(), value: trimmed.substring(colonIdx + 1).trim() }];
    } else {
      pairs = [{ property: trimmed, value: "" }];
    }

    pairs.forEach(function (p) {
      if (!p.property) return;
      current.rows.push({ id: idx++, property: p.property, value: p.value });
    });
  });

  return sections.map(function (s, i) {
    var meta = cacheSectionMeta(s.title);
    return {
      idx: i,
      title: s.title,
      icon: meta.icon,
      iconType: meta.type,
      rowCount: s.rows.length,
      dp: new ArrayDataProvider(s.rows, { keyAttributes: "id" }),
    };
  });
}

self.selectedCacheSectionIndex = ko.observable(0);

self.selectCacheSection = function (index) {
  return function () {
    self.selectedCacheSectionIndex(index);
  };
};

self.selectedCacheSectionData = ko.computed(function () {
  var sections = self.cacheMgrSections();
  var idx = self.selectedCacheSectionIndex();
  return sections[idx] || null;
});

function isCacheMgrReport(lines) {
  var arr = Array.isArray(lines) ? lines : (lines || "").toString().split("\n");
  var text = arr.join(" ");
  return /CACHE OBJECT MANAGER statistics/i.test(text) || /CACHEMGR request/i.test(text);
}

self.menuItemAction = function (extData) {
  return function (event) {
    self.selectedMenuItem(event.detail.key);
    self.ExtName = extData.ExtName;
    if (
      self.selectedMenuItem() == "extrpt" ||
      self.selectedMenuItem() == "extchk" ||
      self.selectedMenuItem() == "extstats" ||
      self.selectedMenuItem() == "extstartdef" ||
      self.selectedMenuItem() == "extstop" ||
      self.selectedMenuItem() == "extforcestop" ||
      self.selectedMenuItem() == "extkill" ||
      self.selectedMenuItem() == "cachemgr" ||
      self.selectedMenuItem() == "extstatus"
    ) {
      self.ExtRpt([]);
      self.extRptIsTable(false);
      self.extRptIsCacheMgr(false);  
      self.delTitle("");
      $.ajax({
        url: self.DepName() + "/api/v2/extract/ops",
        data: JSON.stringify({
          extname: self.ExtName,
          extops: self.selectedMenuItem(),
        }),
        type: "POST",
        dataType: "json",
        contentType: "application/json",
        timeout: sessionStorage.getItem("timeInetrval"),
        context: self,
        progressMessage: `Processing ${self.selectedMenuItem()} for extract ${self.ExtName}`,
        suppressGlobalError: true,
        error: function (xhr, textStatus) {
          if (xhr.status === 401) {
            app.handleSessionExpired();
            return;
          }
          var msg = app.extractErrorMessage(xhr);
          app.showGlobalError(
            `Unable to complete action for extract "${self.ExtName}". ${msg}`,
            "Extract Action Error",
          );
        },
        success: function (data) {
          self.delTitle("View  Extract " + self.ExtName + " Info");
          if (
            self.selectedMenuItem() == "extstartdef" ||
            self.selectedMenuItem() == "extstop" ||
            self.selectedMenuItem() == "extforcestop" ||
            self.selectedMenuItem() == "extkill"
          ) {
            self.popUpResizeSM("ViewExtractRptDialog");
            document.querySelector("#ViewExtractRptDialog").open();
          } else if (self.selectedMenuItem() == "extstats") {
            self.delTitle("Extract " + self.ExtName + " Statistics");
            document.querySelector("#statsTable").refresh();
            self.extStats([]);
            for (var key in data[2]) {
              self.extStats.push({
                TabName: key,
                Inserts: data[2][key]["Inserts"],
                Updates: data[2][key]["Updates"],
                Deletes: data[2][key]["Deletes"],
                Upserts: data[2][key]["Upserts"],
                Discards: data[2][key]["Discards"],
                Operations: data[2][key]["Operations"],
              });
            }
            self.extStats.valueHasMutated();
            self.popUpResize("ViewExtractStatDialog");
            document.querySelector("#ViewExtractStatDialog").open();
          } else {
            self.popUpResize("ViewExtractRptDialog");
            document.querySelector("#ViewExtractRptDialog").open();
          }

          self.ExtRpt(data[0]);

          // Only switch to table view for the read/write status report shape.
          // extchk, cachemgr, extstartdef/stop/forcestop/kill, etc. stay as plain text.
          if (self.selectedMenuItem() == "cachemgr" && isCacheMgrReport(data[0])) {
            self.cacheMgrSections(buildCacheMgrSections(data[0]));
            self.selectedCacheSectionIndex(0);
            self.extRptIsCacheMgr(true);
            self.extRptIsTable(false);
          } 
          else if (isExtractStatusReport(data[0])) {
            self.extStatusSections(buildExtractReportSections(data[0]));
            self.selectedExtStatusIndex(0);
            self.extRptIsTable(true);
            self.extRptIsCacheMgr(false);
          } else {
            self.extRptIsTable(false);
            self.extRptIsCacheMgr(false);
          }

          refresh();
          return self;
        },
      });
    }

    //Extract Start ATCSN
    else if (self.selectedMenuItem() == "extatcsn") {
      self.ExtATCSN();
      document.querySelector("#ExtractATCSNDialog").open();
    } else if (self.selectedMenuItem() == "extedit") {
      self.extPrmRead([]);
      $.ajax({
        url: self.DepName() + "/api/v2/extract/ops",
        data: JSON.stringify({
          extname: self.ExtName,
          extops: self.selectedMenuItem(),
        }),
        type: "POST",
        dataType: "json",
        contentType: "application/json",
        timeout: sessionStorage.getItem("timeInetrval"),
        context: self,
        progressMessage: `Fetching parameters for extract ${self.ExtName}`,
        suppressGlobalError: true,
        error: function (xhr, textStatus) {
          if (xhr.status === 401) {
            app.handleSessionExpired();
            return;
          }
          var msg = app.extractErrorMessage(xhr);
          app.showGlobalError(
            `Unable to fetch extract parameters for "${self.ExtName}". ${msg}`,
            "Extract Parameters Error",
          );
        },
        success: function (data) {
          self.popUpResizeSM("ViewExtractRptDialog");
          document.querySelector("#EditExtDialog").open();
          self.extPrmRead(data[1]);
          return self;
        },
      });
    }

    //Extract Start After CSN
    else if (self.selectedMenuItem() == "extaftercsn") {
      self.ExtAFTERCSN(0);
      document.querySelector("#ExtractAFTERCSNDialog").open();
    }
    //Extract Upgrade to IE
    else if (self.selectedMenuItem() == "upgie") {
      self.DBLoginTitle("DBLogin for Extract " + self.ExtName);
      document.querySelector("#ExtLoginDialog").open();
    }
    //Extract Downgrade to CE
    else if (self.selectedMenuItem() == "dwnie") {
      self.DBLoginTitle("DBLogin for Extract " + self.ExtName);
      document.querySelector("#ExtLoginDialog").open();
    }
    //Extract Delete
    else if (self.selectedMenuItem() == "extdel") {
      self.DBLoginTitle("DBLogin for Extract " + self.ExtName);
      refresh();
      document.querySelector("#ExtLoginDialog").open();
    } else if (self.selectedMenuItem() == "extunreg") {
      self.DBLoginTitle("DBLogin for Extract " + self.ExtName);
      document.querySelector("#ExtLoginDialog").open();
    } else if (self.selectedMenuItem() == "extshowtrans") {
      self.delTitle(
        "Current Open Transactions for Extract " + self.ExtName,
      );
      getOpenTrans();
    } else if (self.selectedMenuItem() == "exttraildel") {
      self.delTitle("Delete Trail for Extract " + self.ExtName);
      document.querySelector("#GettingTrailName").open();
      self.ExtRpt([]);
      $.ajax({
        url: self.DepName() + "/api/v2/getExtTrailName",
        data: JSON.stringify({ extname: self.ExtName }),
        type: "POST",
        dataType: "json",
        contentType: "application/json",
        timeout: sessionStorage.getItem("timeInetrval"),
        context: self,
        progressMessage: `Fetching trail name for extract ${self.ExtName}`,
        suppressGlobalError: true,
        error: function (xhr, textStatus) {
          document.querySelector("#GettingTrailName").close();
          if (xhr.status === 401) {
            app.handleSessionExpired();
            return;
          }
          var msg = app.extractErrorMessage(xhr);
          app.showGlobalError(
            `Unable to fetch trail name for "${self.ExtName}". ${msg}`,
            "Trail Name Error",
          );
        },
        success: function (data) {
          document.querySelector("#GettingTrailName").close();
          if (data[0].length > 0) {
            document.querySelector("#TrailForDelete").open();
            self.ExtRpt(data[0]);
          } else {
            document.querySelector("#TrailForDelete").open();
            self.ExtRpt("No Trails available to delete");
          }
          return self;
        },
      });
    } else if (self.selectedMenuItem() == "exttrailadd") {
      self.addExtTrailType("exttrail");
      $.ajax({
        url: self.DepName() + "/api/v2/pump/rmttrail",
        data: JSON.stringify({ extName: self.ExtName }),
        type: "POST",
        dataType: "json",
        contentType: "application/json",
        timeout: sessionStorage.getItem("timeInetrval"),
        context: self,
        progressMessage: `Preparing trail for extract ${self.ExtName}`,
        suppressGlobalError: true,
        error: function (xhr, textStatus) {
          if (xhr.status === 401) {
            app.handleSessionExpired();
            return;
          }
          var msg = app.extractErrorMessage(xhr);
          app.showGlobalError(
            `Unable to prepare trail for "${self.ExtName}". ${msg}`,
            "Add Trail Error",
          );
        },
        success: function (data) {
          self.delTitle("ADD Remote Trail for " + self.ExtName);
          document.querySelector("#AddExtTrailDialog").open();
          self.addExtTrailName(data[0]);
          return self;
        },
      });
    } else if (self.selectedMenuItem() == "extbegin") {
      self.delTitle("Alter extract " + self.ExtName);
      document.querySelector("#ExtractBegin").open();
    } else if (self.selectedMenuItem() == "extetroll") {
      $.ajax({
        url: self.DepName() + "/api/v2/extract/ops",
        data: JSON.stringify({
          extname: self.ExtName,
          extops: self.selectedMenuItem(),
        }),
        type: "POST",
        dataType: "json",
        contentType: "application/json",
        timeout: sessionStorage.getItem("timeInetrval"),
        context: self,
        progressMessage: `Rolling over trail for extract ${self.ExtName}`,
        suppressGlobalError: true,
        error: function (xhr, textStatus) {
          if (xhr.status === 401) {
            app.handleSessionExpired();
            return;
          }
          var msg = app.extractErrorMessage(xhr);
          app.showGlobalError(
            `Unable to roll over trail for "${self.ExtName}". ${msg}`,
            "Trail Rollover Error",
          );
        },
        success: function (data) {
          self.delTitle("Alter Extract " + self.ExtName + " ETROLLOVER");
          self.popUpResizeSM("ViewExtractRptDialog");
          document.querySelector("#ViewExtractRptDialog").open();
          self.ExtRpt(data[0]);
          self.extRptIsTable(false); // ETROLLOVER stays plain text, unchanged from original
          return self;
        },
      });
    }
  };
};

self.extStatsDP = new PagingDataProviderView(
  new ArrayDataProvider(self.extStats, { keyAttributes: "TabName" }),
);

      self.DeleteTrailOKClose = function (event) {
        document.querySelector("#TrailForDelete").close();
        document.querySelector("#GettingTrailName").open();
        $.ajax({
          url: self.DepName() + "/api/v2/extract/ops",
          data: JSON.stringify({
            extname: self.ExtName,
            trailname: self.ExtRpt(),
            extops: self.selectedMenuItem(),
          }),
          type: "POST",
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Deleting trail",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            document.querySelector("#GettingTrailName").close();
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to delete trail. ${msg}`,
              "Delete Trail Error",
            );
          },
          success: function (data) {
            document.querySelector("#GettingTrailName").close();
            document.querySelector("#DeleteTrail").open();
            self.ExtRpt(data[0]);
            return self;
          },
        });
      };
      self.saveExtPrm = function (event, data) {
        $.ajax({
          url: self.DepName() + "/api/v2/params/save",
          type: "POST",
          dataType: "json",
          contentType: "application/json",
          data: JSON.stringify({
            procName: self.ExtName,
            currentParams: self.extPrmWrite(),
          }),
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: `Saving parameters for extract ${self.ExtName}`,
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to save extract parameters for "${self.ExtName}". ${msg}`,
              "Save Parameters Error",
            );
          },
          success: function (data) {
            document.querySelector("#EditExtDialog").close();
            self.popUpResizeSM("ViewExtractRptDialog");
            document.querySelector("#ViewExtractRptDialog").open();
            self.ExtRpt(data[0]);
            return self;
          },
        });
      };
      self.savePmpPrm = function (event, data) {
        $.ajax({
          url: self.DepName() + "/api/v2/params/save",
          type: "POST",
          dataType: "json",
          contentType: "application/json",
          data: JSON.stringify({
            procName: self.PmpName,
            currentParams: self.pmpPrmWrite(),
          }),
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: `Saving parameters for pump ${self.PmpName}`,
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to save pump parameters for "${self.PmpName}". ${msg}`,
              "Save Parameters Error",
            );
          },
          success: function (data) {
            document.querySelector("#EditPmpDialog").close();
            self.popUpResizeSM("ViewExtractRptDialog");
            document.querySelector("#ViewExtractRptDialog").open();
            self.ExtRpt(data[0]);
            return self;
          },
        });
      };
      self.repPrmWrite = ko.observableArray([]);

      self.saveRepPrm = function (event, data) {
        $.ajax({
          url: self.DepName() + "/api/v2/params/save",
          type: "POST",
          dataType: "json",
          contentType: "application/json",
          data: JSON.stringify({
            procName: self.RepName,
            currentParams: self.repPrmWrite(),
          }),
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: `Saving parameters for replicat ${self.RepName}`,
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to save replicat parameters for "${self.RepName}". ${msg}`,
              "Save Parameters Error",
            );
          },
          success: function (data) {
            document.querySelector("#EditRepDialog").close();
            self.popUpResizeSM("ViewReplicatRptDialog");
            document.querySelector("#ViewReplicatRptDialog").open();
            self.RepRpt(data[0]);
            return self;
          },
        });
      };

      self.unregisterExtract = function (event) {
        var valid = self._checkValidationGroup("ExtLoginDialogForm");
        if (valid) {
          document.querySelector("#ExtLoginDialog").close();
          $.ajax({
            url: self.DepName() + "/api/v2/extract/ops",
            data: JSON.stringify({
              extname: self.ExtName,
              domain: self.selectedDomCategory(),
              alias: self.selectedAliascategory(),
              extops: self.selectedMenuItem(),
            }),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: `Unregistering extract ${self.ExtName}`,
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to unregister extract "${self.ExtName}". ${msg}`,
                "Unregister Extract Error",
              );
            },
            success: function (data) {
              self.delTitle("Unregister  Extract " + self.ExtName);
              self.popUpResizeSM("ViewExtractRptDialog");
              document.querySelector("#ViewExtractRptDialog").open();
              self.ExtRpt(data[0]);
              return self;
            },
          });
        }
      };
      self.AlterExtractBegin = function (data, event) {
        var valid = self._checkValidationGroup("ExtractBeginForm");
        if (valid) {
          document.querySelector("#ExtractBegin").close();
          self.ExtRpt([]);
          $.ajax({
            url: self.DepName() + "/api/v2/extract/ops",
            data: JSON.stringify({
              extname: self.ExtName,
              domain: self.selectedDomCategory(),
              alias: self.selectedAliascategory(),
              beginmode: self.currentExtBeginMode(),
              ctvalue: self.ctvalue(),
              scnvalue: self.seqnovalue(),
              extops: self.selectedMenuItem(),
            }),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: `Altering begin point for extract ${self.ExtName}`,
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to alter begin point for "${self.ExtName}". ${msg}`,
                "Alter Extract Error",
              );
            },
            success: function (data) {
              self.popUpResizeSM("ViewExtractRptDialog");
              document.querySelector("#ViewExtractRptDialog").open();
              self.ExtRpt(data[0]);
              return self;
            },
          });
        }
      };
      self.AddExtTrail = function (event, data) {
        var valid = self._checkValidationGroup("AddExtTrailDialogFOrm");
        if (valid) {
          document.querySelector("#GettingTrailName").open();
          $.ajax({
            url: self.DepName() + "/api/v2/extract/ops",
            data: JSON.stringify({
              extname: self.ExtName,
              trailname: self.addExtTrailName(),
              trailtype: self.addExtTrailType(),
              trailsize: self.addExtTrailSize(),
              extops: self.selectedMenuItem(),
            }),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: `Adding trail for extract ${self.ExtName}`,
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              document.querySelector("#GettingTrailName").close();
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to add trail for "${self.ExtName}". ${msg}`,
                "Add Trail Error",
              );
            },
            success: function (data) {
              document.querySelector("#GettingTrailName").close();
              document.querySelector("#ViewExtractRptDialog").open();
              self.ExtRpt(data[0]);
              return self;
            },
          });
        }
      };
      self.TrailOKClose = function (event) {
        document.querySelector("#DeleteTrail").close();
      };

      self.showTransDP = new ArrayDataProvider(self.ExtOpenTrans, {
        keyAttributes: "XID",
      });

      self.showTranscolumnArray = [
        {
          headerText: "Transaction ID",
          field: "XID",
        },
        {
          headerText: "# of Records",
          field: "Items",
        },
        {
          headerText: "Extract Name",
          field: "Extract",
        },
        {
          headerText: "Redo Thread",
          field: "Redo Thread",
        },
        {
          headerText: "Start Time",
          field: "Start Time",
        },
        {
          headerText: "SCN",
          field: "SCN",
        },
        {
          headerText: "Redo Sequence",
          field: "Redo Seq",
        },
        {
          headerText: "Redo RBA",
          field: "Redo RBA",
        },
        {
          headerText: "Status",
          field: "Status",
        },
        {
          headerText: "Action",
          headerStyle: "text-align: center;",
          style: "text-align: center; padding-top: 0px; padding-bottom: 0px;",
          template: "actionTemplate",
        },
      ];

      self.extStatscolumnArray = [
        {
          headerText: "Table Name",
          field: "TabName",
          width: "320px",
        },
        {
          headerText: "Total Inserts",
          field: "Inserts",
        },
        {
          headerText: "Total Updates",
          field: "Updates",
        },
        {
          headerText: "Total Upserts",
          field: "Upserts",
        },
        {
          headerText: "Total Deletes",
          field: "Deletes",
        },
        {
          headerText: "Total Discards",
          field: "Discards",
        },
        {
          headerText: "Total Operations",
          field: "Operations",
        },
      ];

      self.actionListener = function (event) {
        event.detail.originalEvent.stopPropagation();
      };
      self.xid = ko.observable();

      self.menuListener = function (event, context) {
        self.xid("");
        var rowIndex = self.ExtRpt.indexOf(context.row);
        self.xid(context.row.XID);
        if (event.target.value === "skiptrans") {
          self.ExtRpt.splice(rowIndex, 1);
          self.ExtRpt([]);
          $.ajax({
            url: self.DepName() + "/api/v2/extract/skiptrans",
            data: JSON.stringify({
              extname: self.ExtName,
              xid: self.xid(),
            }),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: `Skipping transaction ${self.xid()}`,
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to skip transaction "${self.xid()}". ${msg}`,
                "Skip Transaction Error",
              );
            },
            success: function (data) {
              document.querySelector("#ViewExtTransSkipRpt").open();
              self.ExtRpt(data[0]);
              return self;
            },
          });
        }
      };
      self.ViewExtractRptOKClose = function (event) {
        refresh();
        document.querySelector("#ViewExtractRptDialog").close();
        document.querySelector("#ExtLoginDialog").close();
        document.querySelector("#AddExtTrailDialog").close();
        document.querySelector("#DeleteConfirm").close();
      };

      self.ViewExtractStatRefresh = function (event) {
        let procname = self.ExtName
        if(!procname){
          procname = self.PmpName
        }
        $.ajax({
          url: self.DepName() + "/api/v2/extract/ops",
          data: JSON.stringify({
            extname: procname,
            extops: "extstats",
          }),
          type: "POST",
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: `Refreshing statistics for extract ${self.ExtName}`,
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to refresh statistics for "${self.ExtName}". ${msg}`,
              "Statistics Refresh Error",
            );
          },
          success: function (data) {
            self.extStats([]);
            document.querySelector("#statsTable").refresh();
            for (var key in data[2]) {
              self.extStats.push({
                TabName: key,
                Inserts: data[2][key]["Inserts"],
                Updates: data[2][key]["Updates"],
                Upserts: data[2][key]["Upserts"],
                Deletes: data[2][key]["Deletes"],
                Discards: data[2][key]["Discards"],
                Operations: data[2][key]["Operations"],
              });
            }
            self.extStats.valueHasMutated();
            return self;
          },
        });
      };

      self.ViewPumpStatRefresh = function (event) {
        $.ajax({
          url: self.DepName() + "/api/v2/extract/ops",
          data: JSON.stringify({
            extname: self.PmpName,
            extops: "extstats",
          }),
          type: "POST",
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: `Refreshing statistics for pump ${self.PmpName}`,
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to refresh statistics for "${self.PmpName}". ${msg}`,
              "Statistics Refresh Error",
            );
          },
          success: function (data) {
            self.extStats([]);
            for (var key in data[2]) {
              self.extStats.push({
                TabName: key,
                Inserts: data[2][key]["Totalinserts"],
                Updates: data[2][key]["Totalupdates"],
                Deletes: data[2][key]["Totaldeletes"],
                Discards: data[2][key]["Totaldiscards"],
                Operations: data[2][key]["Totaloperations"],
              });
            }
            self.extStats.valueHasMutated();
            return self;
          },
        });
      };

      self.ViewExtOpenTransrefresh = function (event) {
        getOpenTrans();
        self.ExtOpenTrans.valueHasMutated();
      };

      self.ViewExtTransSkipRptOKClose = function (event) {
        getOpenTrans();
        self.ExtOpenTrans.valueHasMutated();
        document.querySelector("#ViewExtTransSkipRpt").close();
      };

      self.ExtStartATCSN = function (data, event) {
        var valid = self._checkValidationGroup("ExtractATCSNDialogForm");
        if (valid) {
          self.ExtRpt([]);
          $.ajax({
            url: self.DepName() + "/api/v2/extract/ops",
            data: JSON.stringify({
              extname: self.ExtName,
              extatcsn: self.ExtATCSN(),
              extops: self.selectedMenuItem(),
            }),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: `Starting extract ${self.ExtName} at CSN`,
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              document.querySelector("#ExtractATCSNDialog").close();
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to start extract "${self.ExtName}" at CSN. ${msg}`,
                "Start Extract Error",
              );
            },
            success: function (data) {
              document.querySelector("#ViewExtractRptDialog").open();
              self.ExtRpt(data[0]);
              document.querySelector("#ExtractATCSNDialog").close();
              return self;
            },
          });
        }
      };

      self.ExtStartAFTERCSN = function (data, event) {
        var valid = self._checkValidationGroup("ExtractAFTERCSNDialogForm");
        if (valid) {
          self.ExtRpt([]);
          $.ajax({
            url: self.DepName() + "/api/v2/extract/ops",
            data: JSON.stringify({
              extname: self.ExtName,
              extaftercsn: self.ExtAFTERCSN(),
              extops: self.selectedMenuItem(),
            }),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: `Starting extract ${self.ExtName} after CSN`,
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              document.querySelector("#ExtractAFTERCSNDialog").close();
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to start extract "${self.ExtName}" after CSN. ${msg}`,
                "Start Extract Error",
              );
            },
            success: function (data) {
              document.querySelector("#ViewExtractRptDialog").open();
              self.ExtRpt(data[0]);
              document.querySelector("#ExtractAFTERCSNDialog").close();
              return self;
            },
          });
        }
      };
      self.ExtUpgTOIE = function (data, event) {
        var valid = self._checkValidationGroup("ExtLoginDialogForm");
        if (valid) {
          self.ExtRpt([]);
          document.querySelector("#UpgExtractDialog").open();
          $.ajax({
            url: self.DepName() + "/api/v2/extract/ops",
            data: JSON.stringify({
              extname: self.ExtName,
              domain: self.selectedDomCategory(),
              alias: self.selectedAliascategory(),
              extops: self.selectedMenuItem(),
            }),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: `Upgrading extract ${self.ExtName} to Integrated`,
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              document.querySelector("#UpgExtractDialog").close();
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to upgrade extract "${self.ExtName}". ${msg}`,
                "Upgrade Extract Error",
              );
            },
            success: function (data) {
              document.querySelector("#UpgExtractDialog").close();
              document.querySelector("#ViewExtractRptDialog").open();
              self.ExtRpt(data[0]);
              return self;
            },
          });
        }
      };
      self.ExtDwnTOCE = function (data, event) {
        var valid = self._checkValidationGroup("ExtLoginDialogForm");
        if (valid) {
          self.ExtRpt([]);
          document.querySelector("#UpgExtractDialog").open();
          $.ajax({
            url: self.DepName() + "/api/v2/extract/ops",
            data: JSON.stringify({
              extname: self.ExtName,
              domain: self.selectedDomCategory(),
              alias: self.selectedAliascategory(),
              extops: self.selectedMenuItem(),
            }),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: `Downgrading extract ${self.ExtName} to Classic`,
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              document.querySelector("#UpgExtractDialog").close();
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to downgrade extract "${self.ExtName}". ${msg}`,
                "Downgrade Extract Error",
              );
            },
            success: function (data) {
              document.querySelector("#UpgExtractDialog").close();
              document.querySelector("#ViewExtractRptDialog").open();
              self.ExtRpt(data[0]);
              return self;
            },
          });
        }
      };

      self.DelExt = function (data, event) {
        var valid = self._checkValidationGroup("ExtLoginDialogForm");
        if (valid) {
          self.ExtRpt([]);
          $.ajax({
            url: self.DepName() + "/api/v2/extract/ops",
            data: JSON.stringify({
              extname: self.ExtName,
              domain: self.selectedDomCategory(),
              alias: self.selectedAliascategory(),
              extops: self.selectedMenuItem(),
            }),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: `Deleting extract ${self.ExtName}`,
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to delete extract "${self.ExtName}". ${msg}`,
                "Delete Extract Error",
              );
            },
            success: function (data) {
              self.selectedDomCategory("");
              self.selectedAliascategory("");
              self.delTitle("Deleted Extract " + self.ExtName);
              document.querySelector("#ViewExtractRptDialog").open();
              self.ExtRpt(data[0]);
              return self;
            },
          });
        }
      };
      //**************************************************************************** */
      // Pump Functions
      //**************************************************************************** */

      self.PmpRpt = ko.observableArray([]);
      self.delTitle = ko.observable();

      self.addRmtTrailName = ko.observable();
      self.addRmtTrailType = ko.observable("rmttrail");
      self.addRmtTrailSize = ko.observable(500);

      self.selectedPmpMenuItem = ko.observable("");

      self.menuPmpItemAction = function (pmpData) {
        return function (event) {
          self.selectedPmpMenuItem(event.detail.key);
          self.PmpName = pmpData.PmpName;
          if (
            self.selectedPmpMenuItem() == "extrpt" ||
            self.selectedPmpMenuItem() == "extchk" ||
            self.selectedPmpMenuItem() == "extstats" ||
            self.selectedPmpMenuItem() == "extstartdef" ||
            self.selectedPmpMenuItem() == "extstop" ||
            self.selectedPmpMenuItem() == "extforcestop" ||
            self.selectedPmpMenuItem() == "extkill" ||
            self.selectedPmpMenuItem() == "cachemgr" ||
            self.selectedPmpMenuItem() == "extstatus"
          ) {
            self.PmpRpt([]);
            self.delTitle("");
            $.ajax({
              url: self.DepName() + "/api/v2/extract/ops",
              data: JSON.stringify({
                extname: self.PmpName,
                extops: self.selectedPmpMenuItem(),
              }),
              type: "POST",
              dataType: "json",
              contentType: "application/json",
              timeout: sessionStorage.getItem("timeInetrval"),
              context: self,
              progressMessage: `Processing ${self.selectedPmpMenuItem()} for pump ${self.PmpName}`,
              suppressGlobalError: true,
              error: function (xhr, textStatus) {
                if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
                var msg = app.extractErrorMessage(xhr);
                app.showGlobalError(
                  `Unable to complete action for pump "${self.PmpName}". ${msg}`,
                  "Pump Action Error",
                );
              },
              success: function (data) {
                if (
                  self.selectedPmpMenuItem() == "extstartdef" ||
                  self.selectedPmpMenuItem() == "extstop" ||
                  self.selectedPmpMenuItem() == "extforcestop" ||
                  self.selectedPmpMenuItem() == "extkill"
                ) {
                  self.popUpResizeSM("ViewPumpRptDialog");
                  self.delTitle("View Pump " + self.PmpName + " Info");
                  document.querySelector("#ViewPumpRptDialog").open();
                } else if (self.selectedPmpMenuItem() == "extstats") {
                  self.ExtName = null;
                  self.delTitle("Extract " + self.PmpName + " Statistics");
                  self.extStats([]);
                  for (var key in data[2]) {
                    self.extStats.push({
                      TabName: key,
                      Inserts: data[2][key]["Inserts"],
                      Updates: data[2][key]["Updates"],
                      Deletes: data[2][key]["Deletes"],
                      Discards: data[2][key]["Discards"],
                      Operations: data[2][key]["Operations"],
                    });
                  }
                  self.popUpResize("ViewExtractStatDialog");
                  document.querySelector("#ViewExtractStatDialog").open();
                } else {
                  self.delTitle("View Pump " + self.PmpName + " Info");
                  self.popUpResize("ViewPumpRptDialog");
                  document.querySelector("#ViewPumpRptDialog").open();
                }
                self.PmpRpt(data[0]);
                return self;
              },
            });
          }
          //Extract Start ATCSN
          else if (self.selectedPmpMenuItem() == "pmpatcsn") {
            self.ExtATCSN();
            document.querySelector("#ExtractATCSNDialog").open();
          }
          //Extract Start After CSN
          else if (self.selectedPmpMenuItem() == "extaftercsn") {
            self.ExtAFTERCSN(0);
            document.querySelector("#ExtractAFTERCSNDialog").open();
          } else if (self.selectedPmpMenuItem() == "exttrailadd") {
            $.ajax({
              url: self.DepName() + "/api/v2/pump/rmttrail",
              data: JSON.stringify({ extName: self.PmpName }),
              type: "POST",
              dataType: "json",
              contentType: "application/json",
              timeout: sessionStorage.getItem("timeInetrval"),
              context: self,
              progressMessage: `Preparing remote trail for pump ${self.PmpName}`,
              suppressGlobalError: true,
              error: function (xhr, textStatus) {
                if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
                var msg = app.extractErrorMessage(xhr);
                app.showGlobalError(
                  `Unable to prepare remote trail for "${self.PmpName}". ${msg}`,
                  "Add Remote Trail Error",
                );
              },
              success: function (data) {
                self.delTitle("");
                self.delTitle("ADD Remote Trail for " + self.PmpName);
                document.querySelector("#AddRmtTrailDialog").open();
                self.addRmtTrailName(data[0]);
                return self;
              },
            });
          } else if (self.selectedPmpMenuItem() == "extdelrmt") {
            self.delTitle("Delete Remote Trail of Pump " + self.PmpName + " ?");
            document.querySelector("#DeleteConfirm").open();
          } else if (self.selectedPmpMenuItem() == "pmpdel") {
            self.delTitle("Delete Pump " + self.PmpName + " ?");
            document.querySelector("#DeleteConfirm").open();
          } else if (self.selectedPmpMenuItem() == "extbegin") {
            self.delTitle("Alter Pump " + self.PmpName);
            document.querySelector("#PumpBegin").open();
            self.currentPmpBeginMode("pmpextseqno");
          } else if (self.selectedPmpMenuItem() == "extetroll") {
            self.ExtRpt([]);
            $.ajax({
              url: self.DepName() + "/api/v2/extract/ops",
              data: JSON.stringify({
                extname: self.PmpName,
                extops: self.selectedPmpMenuItem(),
              }),
              type: "POST",
              dataType: "json",
              contentType: "application/json",
              timeout: sessionStorage.getItem("timeInetrval"),
              context: self,
              progressMessage: `Rolling over trail for pump ${self.PmpName}`,
              suppressGlobalError: true,
              error: function (xhr, textStatus) {
                if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
                var msg = app.extractErrorMessage(xhr);
                app.showGlobalError(
                  `Unable to roll over trail for "${self.PmpName}". ${msg}`,
                  "Trail Rollover Error",
                );
              },
              success: function (data) {
                self.delTitle("Alter Extract " + self.PmpName + " ETROLLOVER");
                self.popUpResizeSM("ViewExtractRptDialog");
                document.querySelector("#ViewExtractRptDialog").open();
                self.ExtRpt(data[0]);
                return self;
              },
            });
          } else if (self.selectedPmpMenuItem() == "extedit") {
            self.pmpPrmRead([]);
            $.ajax({
              url: self.DepName() + "/api/v2/extract/ops",
              data: JSON.stringify({
                extname: self.PmpName,
                extops: self.selectedPmpMenuItem(),
              }),
              type: "POST",
              dataType: "json",
              contentType: "application/json",
              timeout: sessionStorage.getItem("timeInetrval"),
              context: self,
              progressMessage: `Fetching parameters for pump ${self.PmpName}`,
              suppressGlobalError: true,
              error: function (xhr, textStatus) {
                if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
                var msg = app.extractErrorMessage(xhr);
                app.showGlobalError(
                  `Unable to fetch pump parameters for "${self.PmpName}". ${msg}`,
                  "Pump Parameters Error",
                );
              },
              success: function (data) {
                self.popUpResizeSM("ViewExtractRptDialog");
                document.querySelector("#EditPmpDialog").open();
                self.pmpPrmRead(data[1]);
                return self;
              },
            });
          }
        };
      };
      self.DeleteRMTOKClose = function (data, event) {
        document.querySelector("#DeleteConfirm").close();
        self.PmpRpt([]);
        $.ajax({
          url: self.DepName() + "/api/v2/pump/rmttrail/delete",
          data: JSON.stringify({ pmpName: self.PmpName }),
          type: "POST",
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: `Deleting remote trail for pump ${self.PmpName}`,
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to delete remote trail for "${self.PmpName}". ${msg}`,
              "Delete Remote Trail Error",
            );
          },
          success: function (data) {
            document.querySelector("#ViewPumpRptDialog").open();
            self.PmpRpt(data[0]);
            return self;
          },
        });
      };
      self.AlterPumpBegin = function (event, data) {
        var valid = self._checkValidationGroup("PumpBeginForm");
        if (valid) {
          document.querySelector("#PumpBegin").close();
          $.ajax({
            url: self.DepName() + "/api/v2/extract/ops",
            data: JSON.stringify({
              extname: self.PmpName,
              seqnovalue: self.seqnovalue(),
              rbavalue: self.rbavalue(),
              beginmode: self.currentPmpBeginMode(),
              extops: self.selectedPmpMenuItem(),
            }),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: `Altering begin point for pump ${self.PmpName}`,
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to alter begin point for "${self.PmpName}". ${msg}`,
                "Alter Pump Error",
              );
            },
            success: function (data) {
              self.popUpResizeSM("ViewExtractRptDialog");
              document.querySelector("#ViewExtractRptDialog").open();
              self.ExtRpt(data[0]);
              return self;
            },
          });
        }
      };
      self.AddRmtTrail = function (event, data) {
        var valid = self._checkValidationGroup("AddRmtTrailDialogForm");
        if (valid) {
          document.querySelector("#AddRmtTrailDialog").close();
          document.querySelector("#GettingTrailName").open();
          $.ajax({
            url: self.DepName() + "/api/v2/extract/ops",
            data: JSON.stringify({
              extname: self.PmpName,
              trailname: self.addRmtTrailName(),
              trailtype: self.addRmtTrailType(),
              trailsize: self.addRmtTrailSize(),
              extops: self.selectedPmpMenuItem(),
            }),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: `Adding remote trail for pump ${self.PmpName}`,
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              document.querySelector("#GettingTrailName").close();
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to add remote trail for "${self.PmpName}". ${msg}`,
                "Add Remote Trail Error",
              );
            },
            success: function (data) {
              document.querySelector("#GettingTrailName").close();
              self.popUpResizeSM("ViewExtractRptDialog");
              document.querySelector("#ViewExtractRptDialog").open();
              self.ExtRpt(data[0]);
              return self;
            },
          });
        }
      };
      self.DelPmp = function (event, data) {
        document.querySelector("#DeleteConfirm").close();
        self.selectedMenuItem("");
        self.ExtRpt([]);
        $.ajax({
          url: self.DepName() + "/api/v2/extract/ops",
          data: JSON.stringify({
            extname: self.PmpName,
            extops: self.selectedPmpMenuItem(),
          }),
          type: "POST",
          dataType: "json",
          contentType: "application/json",
          context: self,
          progressMessage: `Deleting pump ${self.PmpName}`,
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to delete pump "${self.PmpName}". ${msg}`,
              "Delete Pump Error",
            );
          },
          success: function (data) {
            self.delTitle("Deleted Pump " + self.PmpName);
            document.querySelector("#ViewExtractRptDialog").open();
            self.ExtRpt(data[0]);
            return self;
          },
        });
      };
      self.ViewPumpRptOKClose = function (event) {
        document.querySelector("#ViewPumpRptDialog").close();
        refresh();
      };

      //**************************************************************************** */
      // Replicat Functions
      //**************************************************************************** */

      self.cdrStatsColumnArray = [
        { headerText: "Table Name", field: "TabName", width: "220px" },
        {
          headerText: "Insert Row Exists",
          field: "CDRInsertRowExists",
          width: "130px",
        },
        {
          headerText: "Update Row Exists",
          field: "CDRUpdateRowExists",
          width: "130px",
        },
        {
          headerText: "Update Row Missing",
          field: "CDRUpdateRowMissing",
          width: "140px",
        },
        {
          headerText: "Delete Row Exists",
          field: "CDRDeleteRowExists",
          width: "130px",
        },
        {
          headerText: "Delete Row Missing",
          field: "CDRDeleteRowMissing",
          width: "140px",
        },
        {
          headerText: "Total CDR Conflicts",
          field: "CDRConflicts",
          width: "130px",
        },
        {
          headerText: "Resolutions Succeeded",
          field: "CDRResolutions",
          width: "150px",
        },
      ];

      self.repCDRStats = ko.observableArray([]);
      self.repCDRStatsDP = new PagingDataProviderView(new ArrayDataProvider(self.repCDRStats, {keyAttributes: "TabName",}));

      self.cdrTotalConflicts = ko.observable("0.00");
      self.cdrTotalResolutions = ko.observable("0.00");

      function populateCDRStats(data) {
        var CDR_FIELDS = [
          "CDRInsertRowExists",
          "CDRUpdateRowExists",
          "CDRUpdateRowMissing",
          "CDRDeleteRowExists",
          "CDRDeleteRowMissing",
          "CDRConflicts",
          "CDRResolutions",
        ];

        self.repCDRStats([]);

        var totalConflicts = 0;
        var totalResolutions = 0;

        for (var key in data[2]) {
          var row = { TabName: key };
          CDR_FIELDS.forEach(function (f) {
            row[f] = data[2][key][f] || "0.00";
          });
          self.repCDRStats.push(row);

          totalConflicts += parseFloat(data[2][key]["CDRConflicts"] || 0);
          totalResolutions += parseFloat(data[2][key]["CDRResolutions"] || 0);
        }

        self.repCDRStats.valueHasMutated();
        self.cdrTotalConflicts(totalConflicts.toFixed(2));
        self.cdrTotalResolutions(totalResolutions.toFixed(2));
      }

      self.RepRpt = ko.observableArray([]);
      self.selectedRepMenuItem = ko.observable("");

      self.repPrmRead = ko.observableArray([]);

      self.menuRepItemAction = function (repData) {
        return function (event) {
          self.selectedRepMenuItem(event.detail.key);

          self.RepName = repData.RepName;
          //Replicat Functions
          if (
            self.selectedRepMenuItem() == "reprpt" ||
            self.selectedRepMenuItem() == "repstats" ||
            self.selectedRepMenuItem() == "cdrstats" ||
            self.selectedRepMenuItem() == "repchk" ||
            self.selectedRepMenuItem() == "repstartdef" ||
            self.selectedRepMenuItem() == "repskiptrans" ||
            self.selectedRepMenuItem() == "repnofilterdup" ||
            self.selectedRepMenuItem() == "repstop" ||
            self.selectedRepMenuItem() == "repforcestop" ||
            self.selectedRepMenuItem() == "repkill" ||
            self.selectedRepMenuItem() == "repstatus" ||
            self.selectedRepMenuItem() == "cachemgr"
          ) {
            self.delTitle("");
            self.RepRpt([]);
            $.ajax({
              url: self.DepName() + "/api/v2/replicat/ops",
              data: JSON.stringify({
                repops: self.selectedRepMenuItem(),
                repname: self.RepName,
              }),
              type: "POST",
              dataType: "json",
              contentType: "application/json",
              timeout: sessionStorage.getItem("timeInetrval"),
              context: self,
              progressMessage: `Processing ${self.selectedRepMenuItem()} for replicat ${self.RepName}`,
              suppressGlobalError: true,
              error: function (xhr, textStatus) {
                if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
                var msg = app.extractErrorMessage(xhr);
                app.showGlobalError(
                  `Unable to complete action for replicat "${self.RepName}". ${msg}`,
                  "Replicat Action Error",
                );
              },
              success: function (data) {
                self.delTitle("View  Replicat " + self.RepName + " Info");
                self.RepRpt(data[0]);

                if (
                  self.selectedRepMenuItem() == "repstartdef" ||
                  self.selectedRepMenuItem() == "repstop" ||
                  self.selectedRepMenuItem() == "repforcestop" ||
                  self.selectedRepMenuItem() == "repkill" ||
                  self.selectedRepMenuItem() == "repstatus"
                ) {
                  self.popUpResizeSM("ViewReplicatRptDialog");
                  document.querySelector("#ViewReplicatRptDialog").open();
                } else if (self.selectedRepMenuItem() == "repstats") {
                  self.delTitle("Replicat " + self.RepName + " Statistics");
                  document.querySelector("#statsTable").refresh();
                  self.repStats([]);
                  for (var key in data[2]) {
                    self.repStats.push({
                      TabName: key,
                      Inserts: data[2][key]["Inserts"],
                      Updates: data[2][key]["Updates"],
                      Deletes: data[2][key]["Deletes"],
                      Upserts: data[2][key]["Upserts"],
                      Discards: data[2][key]["Discards"],
                      Operations: data[2][key]["Operations"],
                    });
                  }
                  self.repStats.valueHasMutated();
                  self.popUpResize("ViewReplicatStatDialog");
                  document.querySelector("#ViewReplicatStatDialog").open();
                } else if (self.selectedRepMenuItem() == "cdrstats") {
                  self.delTitle("Replicat " + self.RepName + " CDR Statistics");
                  document.querySelector("#cdrStatsTable").refresh();
                  populateCDRStats(data);
                  self.popUpResize("ViewReplicatCDRStatistics");
                  document.querySelector("#ViewReplicatCDRStatistics").open();
                } else {
                  self.popUpResize("ViewReplicatRptDialog");
                  document.querySelector("#ViewReplicatRptDialog").open();
                }
                return self;
              },
            });
          } else if (self.selectedRepMenuItem() == "repatcsn") {
            self.RepATCSN("");
            document.querySelector("#ReplicatATCSNDialog").open();
          } else if (self.selectedRepMenuItem() == "repaftercsn") {
            self.RepATCSN("");
            document.querySelector("#ReplicatAFTERCSNDialog").open();
          } else if (
            self.selectedRepMenuItem() == "repdel" ||
            self.selectedRepMenuItem() == "upgir" ||
            self.selectedRepMenuItem() == "dwnir"
          ) {
            self.DBLoginTitle("DBLogin for Replicat " + self.RepName);
            document.querySelector("#RepLoginDialog").open();
          } else if (self.selectedRepMenuItem() == "repbegin") {
            document.querySelector("#ReplicatBegin").open();
          } else if (self.selectedRepMenuItem() == "repedit") {
            self.repPrmRead([]);
            $.ajax({
              url: self.DepName() + "/api/v2/replicat/ops",
              data: JSON.stringify({
                repname: self.RepName,
                repops: self.selectedRepMenuItem(),
              }),
              type: "POST",
              dataType: "json",
              contentType: "application/json",
              timeout: sessionStorage.getItem("timeInetrval"),
              context: self,
              progressMessage: `Fetching parameters for replicat ${self.RepName}`,
              suppressGlobalError: true,
              error: function (xhr, textStatus) {
                if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
                var msg = app.extractErrorMessage(xhr);
                app.showGlobalError(
                  `Unable to fetch replicat parameters for "${self.RepName}". ${msg}`,
                  "Replicat Parameters Error",
                );
              },
              success: function (data) {
                self.popUpResizeSM("ViewReplicatRptDialog");
                document.querySelector("#EditRepDialog").open();
                self.repPrmRead(data[1]);
                return self;
              },
            });
          }
        };
      };
      self.DelRep = function (data, event) {
        var valid = self._checkValidationGroup("RepLoginDialogForm");
        if (valid) {
          document.querySelector("#RepLoginDialog").close();
          self.RepRpt([]);
          $.ajax({
            url: self.DepName() + "/api/v2/replicat/ops",
            data: JSON.stringify({
              repname: self.RepName,
              domain: self.selectedDomCategory(),
              alias: self.selectedAliascategory(),
              repops: self.selectedRepMenuItem(),
            }),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: `Deleting replicat ${self.RepName}`,
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to delete replicat "${self.RepName}". ${msg}`,
                "Delete Replicat Error",
              );
            },
            success: function (data) {
              self.RepRpt(data[0]);
              self.delTitle("Deleted Replicat " + self.RepName);
              document.querySelector("#ViewReplicatRptDialog").open();
              return self;
            },
          });
        }
      };
      self.RepStartATCSN = function (data, event) {
        var valid = self._checkValidationGroup("ReplicatATCSNDialogForm");
        if (valid) {
          document.querySelector("#ReplicatATCSNDialog").close();
          self.RepRpt([]);
          $.ajax({
            url: self.DepName() + "/api/v2/replicat/ops",
            data: JSON.stringify({
              repname: self.RepName,
              domain: self.selectedDomCategory(),
              alias: self.selectedAliascategory(),
              repatcsn: self.RepATCSN(),
              repops: self.selectedRepMenuItem(),
            }),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: `Starting replicat ${self.RepName} at CSN`,
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to start replicat "${self.RepName}" at CSN. ${msg}`,
                "Start Replicat Error",
              );
            },
            success: function (data) {
              self.RepRpt(data[0]);
              document.querySelector("#ViewReplicatRptDialog").open();
              return self;
            },
          });
        }
      };
      self.RepStartAFTERCSN = function (data, event) {
        var valid = self._checkValidationGroup("ReplicatAFTERCSNDialogForm");
        if (valid) {
          document.querySelector("#ReplicatAFTERCSNDialog").close();
          self.RepRpt([]);
          $.ajax({
            url: self.DepName() + "/api/v2/replicat/ops",
            data: JSON.stringify({
              repname: self.RepName,
              domain: self.selectedDomCategory(),
              alias: self.selectedAliascategory(),
              repaftercsn: self.RepAFTERCSN(),
              repops: self.selectedRepMenuItem(),
            }),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: `Starting replicat ${self.RepName} after CSN`,
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to start replicat "${self.RepName}" after CSN. ${msg}`,
                "Start Replicat Error",
              );
            },
            success: function (data) {
              self.RepRpt(data[0]);
              document.querySelector("#ViewReplicatRptDialog").open();
              return self;
            },
          });
        }
      };
      self.ViewReplicatStatRefresh = function (event) {
        $.ajax({
          url: self.DepName() + "/api/v2/replicat/ops",
          data: JSON.stringify({
            repname: self.RepName,
            repops: "repstats",
          }),
          type: "POST",
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: `Refreshing statistics for replicat ${self.RepName}`,
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to refresh statistics for "${self.RepName}". ${msg}`,
              "Statistics Refresh Error",
            );
          },
          success: function (data) {
            self.repStats([]);
            document.querySelector("#statsTable").refresh();
            for (var key in data[2]) {
              self.repStats.push({
                TabName: key,
                Inserts: data[2][key]["Inserts"],
                Updates: data[2][key]["Updates"],
                Upserts: data[2][key]["Upserts"],
                Deletes: data[2][key]["Deletes"],
                Discards: data[2][key]["Discards"],
                Operations: data[2][key]["Operations"],
              });
            }
            self.repStats.valueHasMutated();
            return self;
          },
        });
      };
      self.ViewReplicatCDRStatRefresh = function () {
        $.ajax({
          url: self.DepName() + "/api/v2/replicat/ops",
          data: JSON.stringify({
            repname: self.RepName,
            repops: "cdrstats",
          }),
          type: "POST",
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: `Refreshing CDR statistics for replicat ${self.RepName}`,
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to refresh CDR statistics for "${self.RepName}". ${msg}`,
              "CDR Statistics Error",
            );
          },
          success: function (data) {
            self.delTitle("Replicat " + self.RepName + " CDR Statistics");
            document.querySelector("#cdrStatsTable").refresh();
            populateCDRStats(data);
            self.popUpResize("ViewReplicatCDRStatistics");
            document.querySelector("#ViewReplicatCDRStatistics").open();
            return self;
          },
        });
      };

      self.repStatsDP = new PagingDataProviderView(
        new ArrayDataProvider(self.repStats, { keyAttributes: "TabName" }),
      );

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

      self.RepUpgradetoIntegrated = function (data, event) {
        var valid = self._checkValidationGroup("RepLoginDialogForm");
        if (valid) {
          document.querySelector("#RepLoginDialog").close();
          self.RepRpt([]);
          $.ajax({
            url: self.DepName() + "/api/v2/replicat/ops",
            data: JSON.stringify({
              repname: self.RepName,
              domain: self.selectedDomCategory(),
              alias: self.selectedAliascategory(),
              repops: self.selectedRepMenuItem(),
            }),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: `Upgrading replicat ${self.RepName} to Integrated`,
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to upgrade replicat "${self.RepName}". ${msg}`,
                "Upgrade Replicat Error",
              );
            },
            success: function (data) {
              self.RepRpt(data[0]);
              document.querySelector("#ViewReplicatRptDialog").open();
              return self;
            },
          });
        }
      };
      self.RepDowngradetoClassic = function (data, event) {
        var valid = self._checkValidationGroup("RepLoginDialogForm");
        if (valid) {
          document.querySelector("#RepLoginDialog").close();
          self.RepRpt([]);
          $.ajax({
            url: self.DepName() + "/api/v2/replicat/ops",
            data: JSON.stringify({
              repname: self.RepName,
              domain: self.selectedDomCategory(),
              alias: self.selectedAliascategory(),
              chktbl: self.currentChkptTbl(),
              repops: self.selectedRepMenuItem(),
            }),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: `Downgrading replicat ${self.RepName} to Classic`,
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to downgrade replicat "${self.RepName}". ${msg}`,
                "Downgrade Replicat Error",
              );
            },
            success: function (data) {
              self.RepRpt(data[0]);
              document.querySelector("#ViewReplicatRptDialog").open();
              return self;
            },
          });
        }
      };

      self.AlterReplicatBegin = function (data, event) {
        var valid = self._checkValidationGroup("ReplicatBeginForm");
        if (valid) {
          document.querySelector("#ReplicatBegin").close();
          self.RepRpt([]);
          $.ajax({
            url: self.DepName() + "/api/v2/replicat/ops",
            data: JSON.stringify({
              repname: self.RepName,
              domain: self.selectedDomCategory(),
              alias: self.selectedAliascategory(),
              beginmode: self.currentbeginmode(),
              ctvalue: self.ctvalue(),
              seqnovalue: self.seqnovalue(),
              rbavalue: self.rbavalue(),
              repops: self.selectedRepMenuItem(),
            }),
            type: "POST",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: `Altering begin point for replicat ${self.RepName}`,
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to alter begin point for "${self.RepName}". ${msg}`,
                "Alter Replicat Error",
              );
            },
            success: function (data) {
              self.RepRpt(data[0]);
              document.querySelector("#ViewReplicatRptDialog").open();
              return self;
            },
          });
        }
      };
      self.ViewReplicatRptOKClose = function (event) {
        refresh();
        document.querySelector("#ViewReplicatRptDialog").close();
        document.querySelector("#RepLoginDialog").close();
      };

      self.connected = function () {
        if (sessionStorage.getItem("userName") == null) {
          self.router.go("signin");
        } else {
          app.onAppSuccess();
          getDomains();
          refresh(true);
          monAll = setInterval(function () {
            refresh(false);
          }, 20000);
        }
      };

      /**
       * Optional ViewModel method invoked after the View is disconnected from the DOM.
       */
      self.disconnected = function () {
        // Implement if needed
        if (monAll) {
          clearInterval(monAll);
          monAll = null;
        }
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
  return ManageViewModel;
});
