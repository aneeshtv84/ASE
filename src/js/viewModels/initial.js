define([
  "knockout",
  "jquery",
  "appController",
  "ojs/ojasyncvalidator-regexp",
  "ojs/ojconverterutils-i18n",
  "ojs/ojconverter-datetime",
  "ojs/ojconverter-number",
  "ojs/ojpagingdataproviderview",
  "ojs/ojarraydataprovider",
  "ojs/ojlistdataproviderview",
  "ojs/ojkeyset",
  "ojs/ojknockout",
  "ojs/ojtrain",
  "ojs/ojradioset",
  "ojs/ojbutton",
  "ojs/ojlabelvalue",
  "ojs/ojdatetimepicker",
  "ojs/ojlabel",
  "ojs/ojlistview",
  "ojs/ojlistitemlayout",
  "ojs/ojformlayout",
  "ojs/ojinputtext",
  "ojs/ojselectsingle",
  "ojs/ojinputnumber",
  "ojs/ojvalidationgroup",
  "ojs/ojselectcombobox",
  "ojs/ojinputsearch",
  "ojs/ojdialog",
  "ojs/ojswitch",
  "ojs/ojcheckboxset",
  "ojs/ojprogress-bar",
  "ojs/ojtable",
  "ojs/ojhighlighttext",
  "ojs/ojpagingcontrol",
  "ojs/ojgauge",
], function (
  ko,
  $,
  app,
  AsyncRegExpValidator,
  ConverterUtilsI18n,
  DateTimeConverter,
  NumberConverter,
  PagingDataProviderView,
  ArrayDataProvider,
  ListDataProviderView,
  ojkeyset_1,
) {
  class InitialLoadViewModel {
    constructor(args) {
      var self = this;
      self.DepName = args.routerState.detail.dep_url;
      self.startExtChk = ko.observable(true);
      self.startRepChk = ko.observable(true);
      self.currentTrailType = ko.observable();
      self.SRCcurrentPDB = ko.observable();
      self.TGTcurrentPDB = ko.observable();
      self.ExtName = ko.observable();
      self.ExtDesc = ko.observable();
      self.RepName = ko.observable();
      self.RepDesc = ko.observable();
      self.rmtOnepPort = ko.observable();
      self.dbTgtDetList = ko.observableArray([]);
      self.onepDepList = ko.observableArray([]);
      self.gatherMeta = ko.observable(true);
      self.deferStart = ko.observable(false);
      self.ApplyMetaButtonVal = ko.observable(true);
      self.OPError = ko.observableArray([]);

      self.LoadOption = ko.observable("file");
      self.SrcOnePDepName = ko.observable();
      self.TgtOnePDepName = ko.observable();

      self.onepUser = ko.observable();
      self.onepPasswd = ko.observable();

      self.repType = ko.observableArray([]);
      self.currentRepType = ko.observable("parallel");
      self.paramValue = ko.observable("text area value");
      self.currentPassThru = ko.observable("passthru");
      self.rmtHostName = ko.observable();
      self.rmtMgrPort = ko.observable();
      self.ButtonVal = ko.observable();
      self.textVal = ko.observable(true);
      self.pdbList = ko.observable();
      self.currentRawValue = ko.observable("");

      self.filter = ko.observable();

      self.currentLoadOption = ko.observable("auto");

      self.ExtoptParam = ko.observableArray([]);
      self.RepoptParam = ko.observableArray([]);

      self.isDDLChecked = ko.observable();
      self.dialogTitle = ko.observable();

      self.isGetTruncChecked = ko.observable();
      self.isEncrytChecked = ko.observable();
      self.isNoUseSnapChecked = ko.observable();
      self.isExcludeTagChecked = ko.observable();
      self.isGetUpdBefChecked = ko.observable();
      self.Threads = ko.observable(1);
      self.selectionInfo = ko.observable("");
      self.excludedTables = ko.observableArray([]);

      self.schemaList = ko.observableArray([]);

      self.LoadName = ko.observable();

      self.CDBCheck = ko.observable();
      self.SRConepDepUrl = ko.observable();
      self.TGTonepDepUrl = ko.observable();
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

      self.CancelBehaviorOpt = ko.observable("icon");
      self.ButtonChltbl = ko.observable(true);

      self.SelectSRCDeployment = (event, data) => {
        self.SRConepDepUrl("");
        $.ajax({
          url: self.DepName() + "/api/v2/onep/depurl",
          type: "POST",
          data: JSON.stringify({ dep: self.SrcOnePDepName() }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: `Resolving deployment ${self.SrcOnePDepName()}`,
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            if (textStatus === "timeout" || xhr.status === 0) {
              app.showGlobalError(
                app.deploymentUnreachableMessage(self.SrcOnePDepName()),
                "Deployment Unreachable",
              );
            } else {
              app.showGlobalError(
                app.extractErrorMessage(xhr),
                "Deployment Error",
              );
            }
          },
          success: function (data) {
            self.selectedSRCDomCategory("");
            self.SRCcurrentPDB("");
            self.pdbList("");
            self.schemaList([]);
            self.SRConepDepUrl(data[0]);
            getSrcDomains();
            return self;
          },
        });
      };
      self.SelectTGTDeployment = (event, data) => {
        if (self.TgtOnePDepName()) {
          self.TGTonepDepUrl("");
          $.ajax({
            url: self.DepName() + "/api/v2/onep/depurl",
            type: "POST",
            data: JSON.stringify({ dep: self.TgtOnePDepName() }),
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: `Resolving deployment ${self.TgtOnePDepName()}`,
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (textStatus === "abort") return;
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              if (textStatus === "timeout" || xhr.status === 0) {
                app.showGlobalError(
                  app.deploymentUnreachableMessage(self.TgtOnePDepName()),
                  "Deployment Unreachable",
                );
              } else {
                app.showGlobalError(
                  app.extractErrorMessage(xhr),
                  "Deployment Error",
                );
              }
            },
            success: function (data) {
              self.selectedTGTDomCategory("");
              self.TGTcurrentPDB("");
              self.TGTonepDepUrl(data[0]);
              self.TgtonepDepType(data[2]);
              var key = "Tgt_" + self.TgtOnePDepName() + "_AccessToken";
              if (data[3]) {
                sessionStorage.setItem(key, data[3]);
              }else {
                sessionStorage.removeItem(key);
              }
              if (data[2] != "bda") {
                getTgtDomains();
              }
              if (data[2] != "bda") {
                getTgtDomains();
              }
              return self;
            },
          });
        }
      };

      var BigDataTgts = [
        { label: "Amazon Kinesis", value: "Amazon Kinesis" },
        { label: "Amazon Redshift", value: "Amazon Redshift" },
        { label: "Amazon S3", value: "Amazon S3" },
        { label: "Apache Cassandra", value: "Apache Cassandra" },
        { label: "Apache Kafka", value: "Apache Kafka" },
        { label: "Apache Hadoop", value: "Apache Hadoop" },
        { label: "Azure Data Lake Storage", value: "Azure Data Lake Storage" },
        { label: "Azure Event Hub", value: "Azure Event Hub" },
        { label: "Azure Synapse Analytics", value: "Azure Synapse Analytics" },
        {
          label: "Cloudera Data Platform (CDP)",
          value: "Cloudera Data Platform (CDP)",
        },
        { label: "Cloudera Hadoop (CDH)", value: "Cloudera Hadoop (CDH)" },
        { label: "Confluent Platform", value: "Confluent Platform" },
        {
          label: "Datastax Enterprise Cassandra",
          value: "Datastax Enterprise Cassandra",
        },
        { label: "Elasticsearch", value: "Elasticsearch" },
        { label: "Google BigQuery", value: "Google BigQuery" },
        { label: "Google Cloud Storage", value: "Google Cloud Storage" },
        { label: "Greenplum", value: "Greenplum" },
        {
          label: "Hortonworks Hadoop (HDP)",
          value: "Hortonworks Hadoop (HDP)",
        },
        {
          label: "Java Message Service (JMS)",
          value: "Java Message Service (JMS)",
        },
        { label: "MapR Hadoop", value: "MapR Hadoop" },
        { label: "MongoDB", value: "MongoDB" },
        { label: "Netezza", value: "Netezza" },
        {
          label: "OCI Autonomous Data Warehouse",
          value: "OCI Autonomous Data Warehouse",
        },
        { label: "OCI Object Storage", value: "OCI Object Storage" },
        { label: "OCI Streaming Service", value: "OCI Streaming Service" },
        {
          label: "Oracle Cloud Object Storage",
          value: "Oracle Cloud Object Storage",
        },
        { label: "Oracle NoSQL", value: "Oracle NoSQL" },
        { label: "Snowflake", value: "Snowflake" },
      ];

      self.BigDataTgtDP = new ArrayDataProvider(BigDataTgts, {
        keyAttributes: "value",
      });

      self.currentBDA = ko.observable();
      self.ButtonAWSKinesis = ko.observable(true);

      self.bdaChangeHandler = function () {
        self.ButtonAWSKinesis(false);
      };

      self.openAWSKenisis = function () {
        document.querySelector("#AWSKenisis").open();
      };

      self.KenisisAlias = ko.observable();

      var AWSRegions = [
        { label: "US East (Ohio)", value: "us-east-2" },
        { label: "US East (N. Virginia)", value: "us-east-1" },
        { label: "US West (N. California)", value: "us-west-1" },
        { label: "US West (Oregon)", value: "us-west-2" },
        { label: "Africa (Cape Town)", value: "af-south-1" },
        { label: "Asia Pacific (Hong Kong)", value: "ap-east-1" },
        { label: "Asia Pacific (Mumbai)", value: "ap-south-1" },
        { label: "Asia Pacific (Osaka)", value: "ap-northeast-3" },
        { label: "Asia Pacific (Seoul)", value: "ap-northeast-2" },
        { label: "Asia Pacific (Singapore)", value: "ap-southeast-1" },
        { label: "Asia Pacific (Sydney)", value: "ap-southeast-2" },
        { label: "Asia Pacific (Tokyo)", value: "ap-northeast-1" },
        { label: "Canada (Central)", value: "ca-central-1" },
        { label: "Europe (Frankfurt)", value: "eu-central-1" },
        { label: "Europe (Ireland)", value: "eu-west-1" },
        { label: "Europe (London)", value: "eu-west-2" },
        { label: "Europe (Milan)", value: "eu-south-1" },
        { label: "Europe (Paris)", value: "eu-west-3" },
        { label: "Europe (Stockholm)", value: "eu-north-1" },
        { label: "Middle East (Bahrain)", value: "me-south-1" },
        { label: "South America (São Paulo)", value: "sa-east-1" },
        { label: "AWS GovCloud (US-East) ", value: "us-gov-east-1" },
        { label: "AWS GovCloud (US-West) ", value: "us-gov-west-1" },
      ];

      self.AWSRegionsDP = new ArrayDataProvider(AWSRegions, {
        keyAttributes: "value",
      });

      self.currentAWSRegion = ko.observable();
      self.kenisis_stream_name = ko.observable();
      self.partitionMappingTemplate = ko.observable();
      self.kinesisProxyServer = ko.observable();
      self.kinesisProxyServerPort = ko.observable();
      self.aws_access_key_id = ko.observable();
      self.aws_secret_access_key = ko.observable();

      self.ExtPrmList = ko.observableArray([]);
      self.ExtTrailName = ko.observable();

      self.queryExtPrm = function (event, data) {
        self.ExtPrmList([]);
        self.ExtTrailName("");
        $.ajax({
          url: self.DepName() + "/api/v2/extract/param",
          type: "POST",
          dataType: "json",
          contentType: "application/json",
          data: JSON.stringify({ currentextname: self.CurrentExtName() }),
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: `Fetching parameters for ${self.CurrentExtName()}`,
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to fetch extract parameters. ${msg}`,
              "Extract Parameters Error",
            );
          },
          success: function (data) {
            self.ExtPrmList(data[0]);
            self.ExtTrailName(data[1]);
            return self;
          },
        });
      };

      self.lmDictSCN = ko.observable(" ");

      self.getItemText = function (itemContext) {
        return itemContext.data.FIRST_CHANGE;
      };

      self.tableColumns = [
        { headerText: "SCN", field: "FIRST_CHANGE", template: "cellTemplate" },
        { headerText: "Time", field: "FIRST_TIME", template: "cellTemplate" },
      ];

      self.regVal = ko.observable("now");
      self.regOptions = [
        { id: "now", value: "now", label: "Now" },
        { id: "existscn", value: "existscn", label: "Existing Dictionary" },
      ];

      self.lmShareOpt = ko.observableArray([
        { label: "AUTOMATIC", value: "AUTOMATIC" },
        { label: "NONE", value: "NONE" },
        { label: "EXTRACT", value: "EXTRACT" },
      ]);
      self.lmShareOptDP = new ArrayDataProvider(self.lmShareOpt, {
        keyAttributes: "value",
      });

      self.currentShareOpt = ko.observable("NONE");

      self.PDBName = ko.observableArray([]);

      self.CurrentExtName = ko.observable();
      self.ExtList = ko.observableArray([]);

      function getExtTrails() {
        self.CurrentExtName("");
        self.ExtList([]);
        $.ajax({
          url: self.DepName() + "/api/v2/exttrail/list",
          type: "GET",
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Fetching extract trail list",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to fetch extract trail list. ${msg}`,
              "Extract Trail Error",
            );
          },
          success: function (data) {
            for (var i = 0; i < data[0].length; i++) {
              self.ExtList.push({
                label: data[0][i].label,
                value: data[0][i].label,
              });
            }
            return self;
          },
        });
      }

      self.ExtListDP = new ArrayDataProvider(self.ExtList, {
        keyAttributes: "value",
      });

      self.currentExtOptParamList = ko.computed(function () {
        var currentExtOptParamList = "";
        if (self.ExtoptParam()) {
          for (var i = 0; i < self.ExtoptParam().length; i++) {
            currentExtOptParamList =
              currentExtOptParamList + self.ExtoptParam()[i] + "\n";
          }
          return currentExtOptParamList;
        } else {
          return "";
        }
      });

      self.currentRepOptParamList = ko.computed(function () {
        var currentRepOptParamList = "";
        if (self.RepoptParam()) {
          for (var i = 0; i < self.RepoptParam().length; i++) {
            currentRepOptParamList =
              currentRepOptParamList + self.RepoptParam()[i] + "\n";
          }
          return currentRepOptParamList;
        } else {
          return "";
        }
      });

      self.ExtPrmList1 = ko.computed(function () {
        if (self.ExtPrmList()) {
          return self.ExtPrmList().join("");
        } else {
          return "";
        }
      });

      self.currentExtType = ko.observable("SOURCEISTABLE");

      self.extType = ko.observableArray([
        { label: "Initial Load Extract", value: "SOURCEISTABLE" },
        { label: "Initial Load Replicat", value: "ILR" },
      ]);

      self.CEOPT = ko.observable("LR");
      self.regExtChk = ko.observable(true);

      self.extractDP = new ArrayDataProvider(self.extType, {
        keyAttributes: "value",
      });

      self.isFormReadonly = ko.observable(false);

      self.selectedStepValue = ko.observable("stp1");
      self.selectedStepLabel = ko.observable("DataSource");
      self.selectedStepFormLabel = ko.observable("DataSource");

      self.manualStepArray = ko.observableArray([
        { label: "DataSource", id: "stp1" },
        { label: "Process Options", id: "stp2" },
        { label: "Parameter File", id: "stp3" },
      ]);

      self.autoStepArray = ko.observableArray([
        { label: "DataSource", id: "stp1" },
      ]);

      self.categorySelectionChanged = (event) => {
        self.selectedSubcategory("");
        let sub = getSubcategories(event.detail.value);
        self.subcategories(sub);
      };

      self.ctvalue = ko.observable(
        ConverterUtilsI18n.IntlConverterUtils.dateToLocalIso(new Date()),
      );

      self.secondConverter = new DateTimeConverter.IntlDateTimeConverter({
        pattern: "yyyy-MM-dd HH:mm:ss",
      });
      self.csnvalue = ko.observable();

      self.decimalHalfDownConverter = new NumberConverter.IntlNumberConverter({
        style: "decimal",
        roundingMode: "HALF_DOWN",
        maximumFractionDigits: 0,
        useGrouping: false,
      });

      self.ExtTrail = ko.observable();
      self.ExtTrailSize = ko.observable("500");

      self.modeVal = ko.observable("Integrated Tranlog");

      self.currentbeginmode = ko.observable("Begin Now");

      self.TrailName = ko.observable();
      self.trailSubDir = ko.observable();
      self.trailSubDirSlash = ko.observable("/");
      self.trailSize = ko.observable(500);

      self.beginmode = ko.observableArray([
        { value: "Begin Now", label: "Now" },
        { value: "Begin ", label: "Custom Time" },
        { value: "CSN", label: "CSN" },
      ]);

      self.startOptionDP = new ArrayDataProvider(self.beginmode, {
        keyAttributes: "value",
      });

      //SRC
      self.SRCusername1 = ko.observableArray([]);
      self.SRCaliasname1 = ko.observableArray([]);
      self.SRCdomname1 = ko.observableArray([]);
      self.SRCothdom = ko.observableArray([]);
      self.selectedSRCDomCategory = ko.observable();
      self.selectedSRCAliascategory = ko.observable();
      self.selectedSRCUsercategory = ko.observable();
      self.SRCaliascategories = ko.observableArray([]);
      self.SRCunamecategories = ko.observable();
      //TGT
      self.TGTusername1 = ko.observableArray([]);
      self.TGTaliasname1 = ko.observableArray([]);
      self.TGTdomname1 = ko.observableArray([]);
      self.TGTothdom = ko.observableArray([]);
      self.selectedTGTDomCategory = ko.observable();
      self.selectedTGTAliascategory = ko.observable();
      self.selectedTGTUsercategory = ko.observable();
      self.TGTaliascategories = ko.observableArray([]);
      self.TGTunamecategories = ko.observable();

      //Get the Credentail Alias Domains
      self.domainLoading = ko.observable(false);

      function getSrcDomains() {
        if (self.SRConepDepUrl().length > 0) {
          self.SRCusername1([]);
          self.SRCothdom([]);
          self.SRCaliasname1([]);
          self.SRCdomname1([]);
          self.domainLoading(true);
          $.ajax({
            url: self.SRConepDepUrl() + "/api/v2/vault/info/all",
            type: "GET",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            progressMessage: "Fetching source credential domains",
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              self.domainLoading(false);
              if (textStatus === "abort") return;
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to fetch source credential domains for "${self.SrcOnePDepName()}" — could not reach ${self.SRConepDepUrl()}. ${msg}`,
                "Credential Domain Error",
              );
            },
            success: function (data) {
              for (var i = 0; i < data[1].length; i++) {
                self.SRCothdom.push({ dom: data[1][i].value });
              }
              self.SRCaliasname1(data[4]);
              for (var i = 0; i < data[2].length; i++) {
                self.SRCdomname1.push({ label: data[2][i], value: data[2][i] });
              }
              for (var i = 0; i < data[0].length; i++) {
                self.SRCusername1.push({
                  label: data[0][i].alias,
                  value: data[0][i].alias,
                  children: [
                    { label: data[0][i].uname, value: data[0][i].uname },
                  ],
                });
              }
              self.domainLoading(false);
              return self;
            },
          });
        }
      }

      self.SRCdomname1DP = new ArrayDataProvider(self.SRCdomname1, {
        keyAttributes: "value",
      });

      function getTgtDomains(data, event) {
        if (self.TGTonepDepUrl().length > 0) {
          self.TGTusername1([]);
          self.TGTothdom([]);
          self.TGTaliasname1([]);
          self.TGTdomname1([]);
          let url = "/api/v2/vault/info/all"
          if (self.TgtonepDepType() == "mongodb") {
            url = "/api/v2/credstore"
          }
          else if (self.TgtonepDepType() == "sqlserver"){
            url = "/api/v2/credstore"
          }
          var ajaxOpts1 = {
            url: self.TGTonepDepUrl() + url,
            type: "GET",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            progressMessage: "Fetching target credential domains",
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (textStatus === "abort") return;
              if (xhr.status === 401){
                app.handleSessionExpired();
                return;
              };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to fetch target credential domains. ${msg}`,
                "Credential Domain Error",
              );
            },
            success: function (data) {
              self.TGTdomname1([])
              for (var i = 0; i < data[1].length; i++) {
                self.TGTothdom.push({ dom: data[1][i].value });
              }
              self.TGTaliasname1(data[4]);
              for (var i = 0; i < data[2].length; i++) {
                self.TGTdomname1.push({ label: data[2][i], value: data[2][i] });
              }
              for (var i = 0; i < data[0].length; i++) {
                self.TGTusername1.push({
                  label: data[0][i].alias,
                  value: data[0][i].alias,
                  children: [
                    { label: data[0][i].uname, value: data[0][i].uname },
                  ],
                });
              }
              return self;
            },
          };
          self.tgtAjax(ajaxOpts1);

          self.dbTgtDetList([]);
          let infoUrl = "/api/v2/info/all";
          if (self.TgtonepDepType() == "mongodb") {
            infoUrl = "/api/v2/gginfoall";
          }
          else if (self.TgtonepDepType() == "sqlserver"){
            infoUrl = "/api/v2/gginfoall"
          }
          var ajaxOpts2 = {
            url: self.TGTonepDepUrl() + infoUrl,
            type: "GET",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: "Fetching target deployment info",
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (textStatus === "abort") return;
              if (xhr.status === 401){
                app.handleSessionExpired();
                return;
              };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to fetch target deployment info for "${self.TgtOnePDepName()}" — could not reach ${self.TGTonepDepUrl()}. ${msg}`,
                "Deployment Info Error",
              );
            },
            success: function (data) {
              self.rmtHostName(
                self.TGTonepDepUrl().split(":")[1].replace("//", ""),
              );
              for (var i = 0; i < data[0].length; i++) {
                self.rmtMgrPort(data[0][i].mgrport);
              }
              return self;
            },
          };
          self.tgtAjax(ajaxOpts2);
        }
      }

      self.replicatDP = new ArrayDataProvider(self.repType, {
        keyAttributes: "value",
      });
      self.TGTdomname1DP = new ArrayDataProvider(self.TGTdomname1, {
        keyAttributes: "value",
      });

      //SRC
      let SRCgetAliascategories = (category) => {
        let found = self.SRCaliasname1().find((c) => c.value === category);
        return found ? found.children : null;
      };
      let SRCgetUnamecategories = (category) => {
        let found = self.SRCusername1().find((c) => c.value === category);
        return found ? found.children : null;
      };
      self.SRCdomSelectionChanged = (event) => {
        self.selectedSRCAliascategory("");
        let children = SRCgetAliascategories(event.detail.value);
        self.SRCaliascategories(children);
        self.schemaList([]);
        self.pdbList();
      };

      self.SRCaliascategoriesDP = new ArrayDataProvider(
        self.SRCaliascategories,
        { keyAttributes: "value" },
      );

      self.SRCaliasSelectionChanged = (event) => {
        self.selectedSRCUsercategory("");
        let children = SRCgetUnamecategories(event.detail.value);
        self.SRCunamecategories(children);
      };

      //TGT
      let TGTgetAliascategories = (category) => {
        let found = self.TGTaliasname1().find((c) => c.value === category);
        return found ? found.children : null;
      };
      let TGTgetUnamecategories = (category) => {
        let found = self.TGTusername1().find((c) => c.value === category);
        return found ? found.children : null;
      };
      self.TGTdomSelectionChanged = (event) => {
        self.selectedTGTAliascategory("");
        let children = TGTgetAliascategories(event.detail.value);
        self.TGTaliascategories(children);
      };

      self.TGTaliascategoriesDP = new ArrayDataProvider(
        self.TGTaliascategories,
        { keyAttributes: "value" },
      );

      self.TGTaliasSelectionChanged = (event) => {
        self.selectedTGTUsercategory("");
        let children = TGTgetUnamecategories(event.detail.value);
        self.TGTunamecategories(children);
      };

      self.value = ko.observable();

      self.groupValid = ko.observable();

      self.tmpPrm = ko.observable();

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
      self.helpSource = ko.computed(function () {
        return self.checkboxValues.indexOf("helpSource") !== -1
          ? self._HELP_SOURCE
          : null;
      });

      self.regExpValidator = new AsyncRegExpValidator({
        pattern: "[a-zA-Z0-9,.'-]{1,}",
        hint: "1 or more letters",
        messageDetail: "You must enter at least 1 letter",
      });

      self.emailRegExpValidator = new AsyncRegExpValidator({
        pattern: ".+\@.+\..+",
        hint: "email format",
        messageDetail: "Invalid email format",
      });

      self.previousStep = function () {
        var train = document.getElementById("train");
        var prev = train.getPreviousSelectableStep();
        if (prev != null) {
          self.selectedStepValue(prev);
          self.selectedStepLabel(train.getStep(prev).label);
          self.selectedStepFormLabel(train.getStep(prev).label);
        }
      };

      self.nextStep = function (event) {
        var train = document.getElementById("train");
        var next = train.getNextSelectableStep();
        if (next == "stp2") {
          var valid = self._checkValidationGroup("SRC");
        } else {
          var valid = self._checkValidationGroup("dataSrc");
        }

        if (valid) {
          //The previous step will have a confirmation message type icon
          self.selectedStepLabel.messageType = "confirmation";
          document
            .getElementById("train")
            .updateStep(self.selectedStepValue, self.selectedStepValue);
          //Now the clicked step could be selected
          self.selectedStepValue(next);
          self.selectedStepLabel(train.getStep(next).label);
          self.selectedStepFormLabel(train.getStep(next).label);
          return;
        } else {
          //The ojBeforeSelect can be cancelled by calling event.preventDefault().
          event.preventDefault();
          //The previous step will have an error message type icon
          self.selectedStepLabel.messageType = "error";
          document
            .getElementById("train")
            .updateStep(self.selectedStepLabel.id, self.selectedStepLabel);
          // show messages on all the components
          // that have messages hidden.

          return;
        }
      }.bind(this);
      //It is being called by the train to make sure the form is valid before moving on to the next step.

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

      this.validate = (event) => {
        var next = train.getNextSelectableStep();
        if (next == "stp2") {
          var valid = self._checkValidationGroup("SRC");
        } else {
          var valid = self._checkValidationGroup("dataSrc");
        }
        if (valid) {
          return;
        } else {
          //The ojBeforeSelect can be cancelled by calling event.preventDefault().
          event.preventDefault();

          setTimeout(function () {
            tracker.showMessages();
            tracker.focusOn("@firstInvalidShown");
          }, 0);
          return;
        }
      };
      self.chkTblList = ko.observableArray([]);
      self.currentChkptTbl = ko.observable();

      function queryChkTbl(data, event) {
        if (self.TGTonepDepUrl().length > 0) {
          self.chkTblList([]);
          self.currentChkptTbl("");
          let url = "/api/v2/chkpt/info";
          if (["mongodb", "sqlserver"].includes(self.TgtonepDepType())) {
            url = "/api/v2/infoCheckpointTable";
          }
          var ajaxOpts = {
            url: self.TGTonepDepUrl() + url,
            type: "POST",
            data: JSON.stringify({
              domain: self.selectedTGTDomCategory(),
              alias: self.TGTcurrentPDB(),
              operation: "View",
            }),
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            progressMessage: "Fetching checkpoint table info",
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (textStatus === "abort") return;
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
              console.log(data);
              self.chkTblList([]);
              var rows = data[0];
              for (var i = 0; i < rows.length; i++) {
                if (rows[i].hasOwnProperty("info")) {
                  self.chkTblList.push({
                    label: rows[i].info,
                    value: rows[i].info,
                  });
                  continue;
                }
                if (["postgresql", "mongodb", "sqlserver"].includes(self.TgtonepDepType())) {
                  self.chkTblList.push({
                    label: rows[i].tabname,
                    value: rows[i].tabname,
                  });
                } else {
                  self.chkTblList.push({ label: data[0][i], value: data[0][i] });
                }
              }
              return self;
            },
          };

          self.tgtAjax(ajaxOpts);
        }
      }

      self.chkpttblDP = new ArrayDataProvider(self.chkTblList, {
        keyAttributes: "value",
      });

      //start
      self.chkptTblName = ko.observable();
      self.domname1 = ko.observableArray([]);
      self.selectedDomCategory = ko.observable();
      self.aliascategories = ko.observableArray([]);
      self.selectedAliascategory = ko.observable();
      self.aliasname1 = ko.observableArray([]);
      self.AddChkptTblMsg = ko.observable();

      self.gotoGGAdmin = function (data, event) {
        $.ajax({
          url: self.DepName() + "/api/v2/vault/info/all",
          type: "GET",
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          progressMessage: "Fetching credential domains",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
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
            self.aliasname1(data[4]);
            for (var i = 0; i < data[2].length; i++) {
              self.domname1.push({ label: data[2][i], value: data[2][i] });
            }
            return self;
          },
        });
        document.querySelector("#chkDlg").open();
      };

      self.addsuppOKClose = function (event) {
        document.querySelector("#chkDlg").close();
      };

      self.DBErrorOKClose = function (event) {
        document.querySelector("#DBErrDialog").close();
      };

      this.domSelectionChanged = (event) => {
        self.selectedAliascategory("");
        let children = getAliascategories(event.detail.value);
        self.aliascategories(children);
      };

      let getAliascategories = (category) => {
        let found = self.aliasname1().find((c) => c.value === category);
        return found ? found.children : null;
      };

      self.addChkptTbl = function (data, event) {
        let valid = self._checkValidationGroup("chktbl");
        if (valid) {
          self.AddChkptTblMsg("");
          let url = "/api/v2/chkpt/add";
          if (self.TgtonepDepType() == "postgresql") {
            url = "/api/v2/gg/checkpointtable";
          }
          if (self.TgtonepDepType() == "mongodb") {
            url = "/api/v2/chkpt/add"; // adjust if Mongo has its own add-checkpoint route
          }

          var ajaxOpts = {
            url: self.TGTonepDepUrl() + url,
            type: "POST",
            data: JSON.stringify({
              domain: self.selectedTGTDomCategory(),
              alias: self.TGTcurrentPDB(),
              operation: "Add",
              chkpttbl: self.chkptTblName(),
            }),
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: "Adding checkpoint table",
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (textStatus === "abort") return;
              if (xhr.status === 401){
                app.handleSessionExpired();
                return;
              };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to add checkpoint table. ${msg}`,
                "Checkpoint Table Error",
              );
            },
            success: function (data) {
              document.querySelector("#chkDlg").close();
              document.querySelector("#ChkptTblDialog").open();
              self.AddChkptTblMsg(data[0]);
              queryChkTbl();
              return self;
            },
          };

          self.tgtAjax(ajaxOpts);
        }
      };

      self.AddChkptTblMsgOKClose = function (event) {
        (self.selectedDomCategory(""),
          self.selectedAliascategory(""),
          self.chkptTblName(""));
        document.querySelector("#ChkptTblDialog").close();
      };

      self.AWSKenisisTblOKClose = function (event) {
        let valid = self._checkValidationGroup("AWSKenisisForm");
        if (valid) {
          // console.log("validation  successs");
          document.querySelector("#AWSKenisis").close();
          self.ApplyMetaButtonVal(false);
        }
      };

      //end

      self.currentExtParamList = ko.observable();
      self.currentPmpParamList = ko.observable();

      self.newExtParamList = ko.observable("");
      self.newRepParamList = ko.observable("");

      //start

      ////console.log(selectedData[1]);

      self.addAutoILProc = function (data, event) {
        self.AddExtractMsg([]);
        self.dialogTitle("Preparing Processes for InitialLoad");        
        $.ajax({
          url: self.SRConepDepUrl() + "/api/v2/initialload/auto",
          type: "POST",
          data: JSON.stringify({
            srcdep: self.SrcOnePDepName(),
            srcdomain: self.selectedSRCDomCategory(),
            srcalias: self.SRCcurrentPDB(),
            startExtChk: self.startExtChk(),
            tgtdep: self.TgtOnePDepName(),
            tgtdomain: self.selectedTGTDomCategory(),
            tgtalias: self.TGTcurrentPDB(),
            chktbl: self.currentChkptTbl(),
            startRepChk: self.startRepChk(),
            tabSplit: self.qualifySplitList(),
            tabExclude: self.excludedTables(), 
            schemaList: self.schemaList(),
            jobName: self.LoadName(),
            cdbCheck: self.CDBCheck(),
            pdbName: self.pdbList(),
            rmtHostName: self.rmtHostName(),
            rmtMgrPort: self.rmtMgrPort(),
            currentSCN: String(self.dbDetList()[0].current_scn),
            deferStart: self.deferStart(),
          }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: `Preparing initial load for ${self.LoadName()}`,
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            console.log(xhr);
            
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to prepare initial load. ${msg}`,
              "Initial Load Error",
            );
          },
          success: function (data) {
            console.log(data);
            
            document.querySelector("#AddILProcDialog").open();
            self.AddExtractMsg(data[0]);
            return self;
          },
        });
      };

      self.currentSchemaParam = ko.computed(function () {
        return self.excludedTables().map((t) => "TABLEEXCLUDE " + t + "\n").join("");
      });

      self.ExtSchemaParam = ko.computed({
        read: function () {
          var ExtSchemaParam = "";
          for (var i = 0; i < self.schemaList().length; i++) {
            if (self.CDBCheck() == "YES" && self.pdbList().length > 0) {
              ExtSchemaParam =
                ExtSchemaParam +
                "TABLE " +
                self.schemaList()[i] +
                ".* , SQLPREDICATE 'AS OF SCN " +
                self.dbDetList()[0].current_scn +
                "';" +
                "\n";
            } else {
              ExtSchemaParam =
                ExtSchemaParam +
                "TABLE " +
                self.schemaList()[i] +
                ".* , SQLPREDICATE 'AS OF SCN " +
                self.dbDetList()[0].current_scn +
                "';" +
                "\n";
            }
          }
          return ExtSchemaParam;
        },
        write: function (newVal) {
          var ExtSchemaParam = newVal;
          return newVal;
        },
      });

      self.RepSchemaParam = ko.computed({
        read: function () {
          var RepSchemaParam = "";
          for (var i = 0; i < self.schemaList().length; i++) {
            RepSchemaParam =
              RepSchemaParam +
              "MAP " +
              self.schemaList()[i] +
              ".* , TARGET " +
              self.schemaList()[i] +
              ".*;" +
              "\n";
          }
          return RepSchemaParam;
        },
        write: function (newVal) {
          var RepSchemaParam = newVal;
          return newVal;
        },
      });

      self.rmthostParam = ko.computed({
        read: function () {
          var rmthostParam = "";
          if (self.LoadOption() === "file") {
            var rmthostParam =
              "RMTHOST " +
              self.rmtHostName() +
              ",MGRPORT " +
              self.rmtMgrPort() +
              " , TCPBUFSIZE  4194304,ENCRYPT AES256" +
              "\n" +
              "rmtfile " +
              "  " +
              self.trailSubDir() +
              self.trailSubDirSlash() +
              self.TrailName() +
              "\n" +
              "ENCRYPTTRAIL";
          } else {
            var rmthostParam =
              "RMTHOST " +
              self.rmtHostName() +
              ",MGRPORT " +
              self.rmtMgrPort() +
              " , TCPBUFSIZE  4194304,ENCRYPT AES256" +
              "\n" +
              "RMTTASK  replicat, GROUP  " +
              self.RepName();
          }

          return rmthostParam;
        },
        write: function (newVal) {
          var rmthostParam = newVal;
          return newVal;
        },
      });

      //end

      self.currentExtParam = ko.computed({
        read: function () {
          if (self.CDBCheck() == "YES" && self.pdbList().length > 0) {
            if (self.LoadOption() === "sqlldr") {
              self.currentRepType("SPECIALRUN");
              var currentExtParam =
                "EXTRACT " +
                self.ExtName() +
                "\n" +
                "useridalias " +
                self.SRCcurrentPDB() +
                " domain " +
                self.selectedSRCDomCategory() +
                "\n" +
                self.rmthostParam() +
                "\n" +
                "BULKLOAD" +
                "\n" +
                "REPORTCOUNT EVERY 1 MINUTES, RATE" +
                "\n" +
                self.currentExtOptParamList() +
                "\n" +
                "SOURCECATALOG " +
                self.pdbList() +
                "\n" +
                self.currentSchemaParam() +
                self.ExtSchemaParam();
            } else if (self.LoadOption() === "file") {
              var currentExtParam =
                "EXTRACT " +
                self.ExtName() +
                "\n" +
                "useridalias " +
                self.SRCcurrentPDB() +
                " domain " +
                self.selectedSRCDomCategory() +
                "\n" +
                self.rmthostParam() +
                "\n" +
                "REPORTCOUNT EVERY 1 MINUTES, RATE" +
                "\n" +
                self.currentExtOptParamList() +
                "\n" +
                "SOURCECATALOG " +
                self.pdbList() +
                "\n" +
                self.currentSchemaParam() +
                self.ExtSchemaParam();
            }
          } else {
            if (self.LoadOption() === "sqlldr") {
              self.currentRepType("SPECIALRUN");
              var currentExtParam =
                "EXTRACT " +
                self.ExtName() +
                "\n" +
                "useridalias " +
                self.SRCcurrentPDB() +
                " domain " +
                self.selectedSRCDomCategory() +
                "\n" +
                self.rmthostParam() +
                "\n" +
                "BULKLOAD" +
                "\n" +
                "REPORTCOUNT EVERY 1 MINUTES, RATE" +
                "\n" +
                self.currentExtOptParamList() +
                "\n" +
                self.currentSchemaParam() +
                self.ExtSchemaParam();
            } else if (self.LoadOption() === "file") {
              var currentExtParam =
                "EXTRACT " +
                self.ExtName() +
                "\n" +
                "useridalias " +
                self.SRCcurrentPDB() +
                " domain " +
                self.selectedSRCDomCategory() +
                "\n" +
                self.rmthostParam() +
                "\n" +
                "REPORTCOUNT EVERY 1 MINUTES, RATE" +
                "\n" +
                self.currentExtOptParamList() +
                "\n" +
                self.currentSchemaParam() +
                self.ExtSchemaParam();
            }
          }
          return currentExtParam;
        },
        write: function (newVal) {
          var currentExtParam = newVal;
          return newVal;
        },
      });

      self.currentExtParamList = self.currentExtParam;

      self.currentRepParam = ko.computed({
        read: function () {
          if (self.CDBCheck() == "YES" && self.pdbList().length > 0) {
            var currentRepParam =
              "REPLICAT " +
              self.RepName() +
              "\n" +
              "useridalias " +
              self.TGTcurrentPDB() +
              " domain " +
              self.selectedTGTDomCategory() +
              "\n" +
              "REPORTCOUNT EVERY 1 MINUTES, RATE" +
              "\n" +
              self.currentRepOptParamList() +
              "\n" +
              "SOURCECATALOG " +
              self.pdbList() +
              "\n" +
              self.RepSchemaParam();
          } else {
            var currentRepParam =
              "REPLICAT " +
              self.RepName() +
              "\n" +
              "useridalias " +
              self.TGTcurrentPDB() +
              " domain " +
              self.selectedTGTDomCategory() +
              "\n" +
              "REPORTCOUNT EVERY 1 MINUTES, RATE" +
              "\n" +
              self.currentRepOptParamList() +
              "\n" +
              self.RepSchemaParam();
          }
          return currentRepParam;
        },
        write: function (newVal) {
          var currentRepParam = newVal;
          return newVal;
        },
      });

      self.currentRepParamList = self.currentRepParam;

      //The method updates the label text to show what step the user is on
      self.updateLabelText = function (event) {
        if (self.selectedStepValue == "stp2") {
          self.selectedStepFormLabel("Extract Options");
          self.isFormReadonly(false);
        } else if (self.selectedStepValue == "stp1") {
          self.selectedStepFormLabel("DataSource / Extract Type");
          self.isFormReadonly(false);
        } else if (self.selectedStepValue == "stp3") {
          self.selectedStepFormLabel("Parameter File");
          self.isFormReadonly(true);
        }
      }.bind(this);

      self.AddExtractMsg = ko.observableArray([]);
      self.AddReplicatMsg = ko.observableArray([]);

      self.cancel = function () {
        self.router.go({ path: "manage" });
      };

      self.addInitialLoadExt = function (data, event) {
        self.AddExtractMsg([]);
        self.dialogTitle("Adding InitalLoad Extract");
        $.ajax({
          url: self.SRConepDepUrl() + "/api/v2/extract/addinitialload",
          type: "POST",
          data: JSON.stringify({
            srcdep: self.SrcOnePDepName(),
            extname: self.ExtName(),
            extdesc: self.ExtDesc(),
            srcdomain: self.selectedSRCDomCategory(),
            srcalias: self.SRCcurrentPDB(),
            extmode: self.currentExtType(),
            currentExtParamList: self.newExtParamList(),
            startExtChk: self.startExtChk(),
          }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: `Adding extract ${self.ExtName()}`,
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to add extract "${self.ExtName()}". ${msg}`,
              "Add Extract Error",
            );
          },
          success: function (data) {
            document.querySelector("#AddInitailLoadExtDialog").open();
            self.AddExtractMsg(data[0]);
            return self;
          },
        });
      };

      self.addInitialLoadRep = function (data, event) {
        self.AddReplicatMsg([]);
        let url = "/api/v2/il/rep/add-initial";
        if (self.TgtonepDepType() == "mongodb") {
          url = "/api/v2/addMongoReplicat"; // adjust to the actual Mongo initial-load-replicat route
        }

        var ajaxOpts = {
          url: self.TGTonepDepUrl() + url,
          type: "POST",
          data: JSON.stringify({
            tgtdep: self.TgtOnePDepName(),
            repname: self.RepName(),
            repdesc: self.RepDesc(),
            tgtdomain: self.selectedTGTDomCategory(),
            tgtalias: self.TGTcurrentPDB(),
            repmode: self.currentRepType(),
            trail:
              self.trailSubDir() + self.trailSubDirSlash() + self.TrailName(),
            currentRepParamList: self.newRepParamList(),
            chktbl: self.currentChkptTbl(),
            startRepChk: self.startRepChk(),
          }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: `Adding replicat ${self.RepName()}`,
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to add replicat "${self.RepName()}". ${msg}`,
              "Add Replicat Error",
            );
          },
          success: function (data) {
            document.querySelector("#AddInitailLoadRepDialog").open();
            self.AddReplicatMsg(data[0]);
            return self;
          },
        };

        self.tgtAjax(ajaxOpts);
      };

      self.CreateTblMsg = ko.observableArray([]);

      self.ApplyMetadata = function (data, event) {
        self.CreateTblMsg([]);
        var ajaxOpts = {
          url: self.TGTonepDepUrl() + "/api/v2/metadata/apply",
          type: "POST",
          data: JSON.stringify({
            dbname: self.TGTcurrentPDB(),
            jobName: self.LoadName(),
            dep_url: self.SRConepDepUrl(),
          }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Applying metadata",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to apply metadata. ${msg}`,
              "Apply Metadata Error",
            );
          },
          success: function (data) {
            document.getElementById("metatbl").refresh();
            document.querySelector("#CreateTableDialog").open();
            for (var i = 0; i < data[0].length; i++) {
              self.CreateTblMsg.push({
                TabName: data[0][i].TabName,
                msg: data[0][i].msg,
              });
            }
            return self;
          },
        };

        self.tgtAjax(ajaxOpts);
      };

      self.CreateTblMsgDP = new PagingDataProviderView(
        new ArrayDataProvider(self.CreateTblMsg, { idAttribute: "TabName" }),
      );

      self.createTblOkClose = function (data, event) {
        document.querySelector("#CreateTableDialog").close();
      };

      self.onepDepList = ko.observableArray([]);

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
      self.onepDepListDP = new ArrayDataProvider(self.onepDepList, {
        keyAttributes: "value",
      });

      self.args = args;
      // Create a child router with one default path
      self.router = self.args.parentRouter;

      self.addAutoILProcOKClose = function () {
        self.router.go({
          path: "initmon",
          params: { LoadName: self.LoadName() },
        });
      };

      self.AddInitialLoadExtOKClose = function (data, event) {
        document.querySelector("#AddInitailLoadExtDialog").close();
        $.ajax({
          url: self.DepName() + "/api/v2/il/ext/add",
          type: "POST",
          data: JSON.stringify({
            srcdep: self.SrcOnePDepName(),
            extname: self.ExtName(),
            trail:
              self.trailSubDir() + self.trailSubDirSlash() + self.TrailName(),
          }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Finalizing extract",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to finalize extract. ${msg}`,
              "Extract Error",
            );
          },
          success: function (data) {
            return self;
          },
        });
      };

      self.AddInitialLoadRepOKClose = function () {
        document.querySelector("#AddInitailLoadRepDialog").close();
        var ajaxOpts = {
          url: self.TGTonepDepUrl() + "/api/v2/il/rep/add",
          type: "POST",
          data: JSON.stringify({
            tgtdep: self.TgtOnePDepName(),
            repname: self.RepName(),
            trail:
              self.trailSubDir() + self.trailSubDirSlash() + self.TrailName(),
          }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Finalizing replicat",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to finalize replicat. ${msg}`,
              "Replicat Error",
            );
          },
          success: function (data) {
            if (self.AddReplicatMsg().toString().includes("ERROR")) {
              // no-op
            } else {
              self.router.go({ path: "initmon" });
            }
            return self;
          },
        };

        self.tgtAjax(ajaxOpts);
      };

      self.PDBNameList = ko.observableArray([]);
      self.schemaNameList = ko.observableArray([]);
      self.dbDetList = ko.observableArray([]);

      self.CDBData = function (data, event) {
        if (self.SRCcurrentPDB()) {
          self.CDBCheck("");
          self.OPError();
          self.PDBNameList([]);
          self.dbDetList([]);
          self.schemaNameList([]);
          self.schemaList([]);
          self.pdbList("");
          $.ajax({
            url: self.SRConepDepUrl() + "/api/v2/db/cdbcheck",
            type: "POST",
            data: JSON.stringify({ dbname: self.SRCcurrentPDB() }),
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: "Checking database (CDB/PDB)",
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (textStatus === "abort") return;
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to check database. ${msg}`,
                "Database Check Error",
              );
            },
            success: function (data) {
              console.log(data);

              self.CDBCheck(data[0]);
              var errMsg = typeof data[1] === "string" ? data[1] : "";
              var hasError = errMsg.includes("ORA-") || errMsg.toLowerCase().includes("error");

              if (!hasError) {
                self.PDBNameList.removeAll();
                if (Array.isArray(data[1])) {
                  for (var i = 0; i < data[1].length; i++) {
                    self.PDBNameList.push({
                      label: data[1][i].name,
                      value: data[1][i].name,
                    });
                  }
                }
                self.PDBNameList.valueHasMutated();

                // Schema list
                self.schemaNameList.removeAll();
                for (var j = 0; j < data[2].length; j++) {
                  self.schemaNameList.push({
                    label: data[2][j].username,
                    value: data[2][j].username,
                  });
                }
                self.schemaNameList.valueHasMutated();

                // DB details: ASE keys are uppercase
                self.dbDetList.removeAll();
                for (var k = 0; k < data[3].length; k++) {
                  var row = data[3][k];
                  self.dbDetList.push({
                    dbname: row.DBNAME,
                    host: row.HOST,
                    version: row.VERSION,
                    dbedition: row.DB_EDITION,
                  });
                }
                self.dbDetList.valueHasMutated();

                // Extra ASE values, if you need them
                // var trailPath = data[4];   // "/cdc_data/TRAILS"
                // var flag      = data[5];   // false
                // var edition   = data[6];   // "EE"
              } else {
                document.querySelector("#DBErrDialog").open();
                self.OPError(errMsg);
              }
              return self;
            },
          });
        }
      };

      self.PDBNameListDP = new ArrayDataProvider(self.PDBNameList, {
        keyAttributes: "value",
      });
      self.schemaNameListDP = new ArrayDataProvider(self.schemaNameList, {
        keyAttributes: "value",
      });

      self.schemaNameCDBList = ko.observableArray([]);

      self.SRCDBSchema = function (data, event) {
        self.schemaNameCDBList([]);
        self.OPError([]);
        $.ajax({
          url: self.SRConepDepUrl() + "/api/v2/db/supplogschema",
          type: "POST",
          data: JSON.stringify({
            dbname: self.SRCcurrentPDB(),
            cdbCheck: self.CDBCheck(),
            pdbName: self.pdbList(),
          }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Fetching schema list",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to fetch schema list. ${msg}`,
              "Schema List Error",
            );
          },
          success: function (data) {
            if (data[0].includes("ORA-")) {
              document.querySelector("#ErrorLoad").open();
              self.OPError(data[0]);
            }
            for (var i = 0; i < data[0].length; i++) {
              self.schemaNameCDBList.push({
                label: data[0][i].USERNAME,
                value: data[0][i].USERNAME,
              });
            }
            self.schemaNameCDBList.valueHasMutated();
            return self;
          },
        });
      };
      self.schemaNameCDBListDP = new ArrayDataProvider(self.schemaNameCDBList, {
        keyAttributes: "value",
      });
      self.dbDetListDP = new ArrayDataProvider(self.dbDetList, {
        keyAttributes: "dbid",
      });

      self.dbVer = ko.observable(0);

      self.DBTgtSchema = function (data, event) {
        if (self.TGTcurrentPDB()) {
          self.trailSubDir("");
          self.dbTgtDetList([]);
          self.OPError([]);
          self.dbVer("");
          let url = "/api/v2/db/cdbcheck";
          if (["postgresql", "mongodb"].includes(self.TgtonepDepType())) {
            url = "/api/v2/cdbcheck";
          }
          else if (self.TgtonepDepType() == "sqlserver"){
            url = "/api/v2/cdbCheck"
          }

          var ajaxOpts = {
            url: self.TGTonepDepUrl() + url,
            type: "POST",
            data: JSON.stringify({ dbname: self.TGTcurrentPDB() }),
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: "Checking target database",
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (textStatus === "abort") return;
              if (xhr.status === 401){
                app.handleSessionExpired();
                return;
              };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to check target database. ${msg}`,
                "Database Check Error",
              );
            },
            success: function (data) {
              self.ButtonChltbl(false);
              console.log(data);

              // ---------- SQL Server ----------
              if (self.TgtonepDepType() == "sqlserver") {
                // On failure the backend returns the error text in data[0]
                if (typeof data[0] === "string") {
                  self.OPError(data[0]);
                  document.querySelector("#DBErrDialog").open();
                  return self;
                }
                var s = data[1] || {};
                self.dbTgtDetList.push({
                  dbname:        s.DBNAME,
                  alias:         data[3],
                  servicename:   data[2],
                  host:          s.Host,
                  version:       s.ProductVersion,
                  edition:       s.Edition,
                  patchlevel:    s.PatchLevel,
                  collation:     s.Collation,
                  recoverymodel: s.RecoveryModel,
                  clustered:     s.IsClustered ? "YES" : "NO",
                  hadr:          s.IsHADREnabled ? "YES" : "NO",
                });
                self.dbVer(s.ProductVersion || "");
                self.dbTgtDetList.valueHasMutated();
                queryChkTbl();
                return self;
              }

              // ---------- MongoDB ----------
              if (self.TgtonepDepType() == "mongodb") {
                var m = data[1];
                self.dbTgtDetList.push({
                  dbname: m.DBNAME,
                  version: m.ProductVersion,
                  host: m.Host,
                  clustered: m.IsClustered ? "YES" : "NO",
                  replicaMembers: m.ReplicaMembers,
                  storageEngine: m.StorageEngine || "N/A",
                  dataSizeMB: m.DataSizeBytes ? (m.DataSizeBytes / (1024 * 1024)).toFixed(2) : "N/A",
                  storageSizeMB: m.StorageSizeBytes ? (m.StorageSizeBytes / (1024 * 1024)).toFixed(2) : "N/A",
                  collectionCount: m.CollectionCount,
                  indexCount: m.IndexCount,
                });
                self.dbVer(m.ProductVersion);
                self.dbTgtDetList.valueHasMutated();
                queryChkTbl();
                return self;
              }

              // ---------- Oracle / PostgreSQL ----------
              var errText = typeof data[1] === "string" ? data[1] : "";
              if (!errText.includes("ORA-")) {
                for (var i = 0; i < data[3].length; i++) {
                  if (self.TgtonepDepType() == "postgresql") {
                    self.dbTgtDetList.push({
                      dbname: data[3][i].dbname,
                      dbowner: data[3][i].db_owner,
                      product: data[3][i].product_name,
                      host: data[3][i].host,
                      port: data[3][i].port,
                      version: data[3][i].server_version,
                      encoding: data[3][i].encoding,
                      dbsize: data[3][i].db_size,
                      starttime: data[3][i].start_time,
                      osplatform: data[3][i].os_system + " " + data[3][i].os_release,
                      cdb: data[0],
                    });
                    self.dbVer(data[3][i].server_version);
                  } else {
                    self.dbTgtDetList.push({
                      dbid: data[3][i].dbid,
                      dbname: data[3][i].dbname,
                      pdbname: data[3][i].pdbname,
                      platform: data[3][i].platform_name,
                      host: data[3][i].host,
                      version: data[3][i].version,
                      dbedition: data[3][i].db_edition,
                      db_role: data[3][i].database_role,
                      current_scn: data[3][i].current_scn,
                      cdb: data[3][i].cdb,
                    });
                    self.dbVer(data[3][i].version);
                  }
                }
                self.dbTgtDetList.valueHasMutated();
                self.trailSubDir(data[4]);
                queryChkTbl();
                getGGVersion();
              } else {
                document.querySelector("#DBErrDialog").open();
                self.OPError(errText);
              }
              return self;
            },
          };

          self.tgtAjax(ajaxOpts);
        }
      };

      function getGGVersion() {
        self.repType([]);
        var ajaxOpts = {
          url: self.TGTonepDepUrl() + "/api/v2/get-version",
          type: "GET",
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          progressMessage: "Fetching version details",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to fetch GoldenGate version. ${msg}`,
              "Version Fetch Error",
            );
          },
          success: function (data) {
            if (
              (data[1] == "211" || data[1] == "191" || data[1] == "181" || data[1] == "123") &&
              self.dbVer().split(".")[0] > 11
            ) {
              self.repType.push(
                { label: "Parallel Replicat", value: "parallel" },
                { label: "Integrated Replicat", value: "integrated" },
                { label: "Classic Replicat", value: "" },
                { label: "Coordinated Replicat", value: "coordinated" },
                { label: "Parallel Integrated Replicat", value: "parallelIR" },
              );
            } else if (
              (data[1] == "211" || data[1] == "191" || data[1] == "181" || data[1] == "123") &&
              self.dbVer().split(".")[0] == 11
            ) {
              self.repType.push(
                { label: "Parallel Replicat", value: "parallel" },
                { label: "Classic Replicat", value: "" },
                { label: "Coordinated Replicat", value: "coordinated" },
              );
            } else if (data[1] <= "122" && self.dbVer().split(".")[0] == "11") {
              self.repType.push(
                { label: "Classic Replicat", value: "" },
                { label: "Coordinated Replicat", value: "coordinated" },
              );
            }
            return self;
          },
        };

        self.tgtAjax(ajaxOpts);
      }

      self.dbTgtDetListDP = new ArrayDataProvider(self.dbTgtDetList, {
        keyAttributes: "@index",
      });

      self.avg_space = ko.observable(0);

      self.tableNameList = ko.observableArray([]);

      self.qualifySplitList = ko.observableArray([]);

      self.SrcDBSchemaFetch = function (data, event) {
        $.ajax({
          url: self.SRConepDepUrl() + "/api/v2/db/tablelist",
          type: "POST",
          data: JSON.stringify({
            dbname: self.SRCcurrentPDB(),
            schemaList: self.schemaList(),
            cdbCheck: self.CDBCheck(),
            pdbName: self.pdbList(),
            gatherMeta: self.gatherMeta(),
            LoadName: self.LoadName(),
          }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Fetching table list",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to fetch table list. ${msg}`,
              "Table List Error",
            );
          },
          success: function (data) {
            console.log(data);
            
            self.tableNameList([]);
            self.qualifySplitList([]);
            self.excludedTables([]);
            self.selectionInfo("");
            self.selectedItems({
              row: new ojkeyset_1.KeySetImpl(),
              column: new ojkeyset_1.KeySetImpl(),
            });
            self.avg_space(0);
            // document.getElementById("tableNameList").refresh();
            let total = 0;
            for (var i = 0; i < data[0].length; i++) {
              self.tableNameList.push({
                TABLE_NAME: data[0][i].owner + "." + data[0][i].table_name,
                ROWCNT: data[0][i].num_rows,
                AVGSPC: data[0][i].avg_space,
                ANALYZETIME: data[0][i].last_analyzed,
              });
              total = total + parseInt(data[0][i].avg_space);
            }
            self.avg_space(total);
            for (var i = 0; i < data[2].length; i++) {
              self.qualifySplitList.push({ TABLE_NAME: data[2][i].table_name });
            }
            self.tableNameList.valueHasMutated();
            self.qualifySplitList.valueHasMutated();
            if (self.gatherMeta() == true) {
              self.ApplyMetaButtonVal(false);
            } else {
              self.ApplyMetaButtonVal(true);
            }
            return self;
          },
        });
      };

      self.tableNameListDP = new PagingDataProviderView(
        new ArrayDataProvider(self.tableNameList, {
          idAttribute: "TABLE_NAME",
        }),
      );

      // self.dataproviderView = new ListDataProviderView(self.tableNameListDP, {
      //     sortCriteria: [{ attribute: "AVGSPC", direction: "descending" }],
      // });

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
        var options = {
          sortCriteria: [{ attribute: "AVGSPC", direction: "descending" }],
        };

        if (searchText && searchText.length > 0) {
          options.filterCriterion = oj.FilterFactory.getFilter({
            filterDef: {
              text: searchText,
            },
          });
        }

        return new ListDataProviderView(self.tableNameListDP, options);
      });
      self.qualifySplitListDP = new ArrayDataProvider(self.qualifySplitList, {
        idAttribute: "TABLE_NAME",
      });

      self.tableListcolumnArray = [
        {
          headerText: "Schema.Table Name",
          field: "TABLE_NAME",
          footerTemplate: "revenueLabelTemplate",
        },
        { headerText: "Row Count", field: "ROWCNT" },
        {
          headerText: "Average Size(MB)",
          footerTemplate: "revenueTotalTemplate",
          field: "AVGSPC",
        },
        { headerText: "Analyze Time", field: "ANALYZETIME" },
      ];

      self.dbDetcolumnArray = [
        { headerText: "DB Name", field: "dbname" },
        { headerText: "Host", field: "host" },
        { headerText: "Version", field: "version" },
        { headerText: "DB Edition", field: "dbedition" },
      ];

      self.postgresDbDetcolumnArray = [
        { headerText: "DB Name", field: "dbname" },
        { headerText: "DB Owner", field: "dbowner" },
        { headerText: "Product", field: "product" },
        { headerText: "Host", field: "host" },
        { headerText: "Port", field: "port" },
        { headerText: "Version", field: "version" },
        { headerText: "Encoding", field: "encoding" },
        { headerText: "DB Size", field: "dbsize" },
        { headerText: "Start Time", field: "starttime" },
        { headerText: "OS Platform", field: "osplatform" },
        { headerText: "CDB", field: "cdb" },
      ];

      self.sqlserverDbDetcolumnArray = [
        { headerText: "DB Name",        field: "dbname" },
        { headerText: "Alias",          field: "alias" },
        { headerText: "Service Name",   field: "servicename" },
        { headerText: "Host",           field: "host" },
        { headerText: "Version",        field: "version" },
        { headerText: "Edition",        field: "edition" },
        { headerText: "Patch Level",    field: "patchlevel" },
        { headerText: "Collation",      field: "collation" },
        { headerText: "Recovery Model", field: "recoverymodel" },
        { headerText: "Clustered",      field: "clustered" },
        { headerText: "HADR",           field: "hadr" },
      ];

      self.submitInput = function (data, event) {
        setTimeout(function () {
          self.LoadName(self.currentRawValue().toUpperCase());
        }, 1);
      };

      self.valueChangedHandler1 = (event) => {
        self.ButtonVal(false);
        self.ApplyMetaButtonVal(false);
      };
      self.valueChangedHandler = (event) => {
        self.textVal(false);
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
        { value: { row: "none", column: "single" }, label: "Single Column" },
        {
          value: { row: "none", column: "multiple" },
          label: "Multiple Column",
        },
        { value: { row: "single", column: "none" }, label: "Single Row" },
        { value: { row: "multiple", column: "none" }, label: "Multiple Row" },
      ];
      this.selectionModeDP = new ArrayDataProvider(this.selectionModes, {
        keyAttributes: "value",
      });

      this.selectedChangedListener = (event) => {
        const rowKeys = event.detail.value.row;
        let excluded = [];

        if (rowKeys.isAddAll()) {
          // "Select all" = every table EXCEPT the ones the user then deselected
          const deselected = new Set();
          rowKeys.deletedValues().forEach((k) => deselected.add(k));
          excluded = self.tableNameList()
            .map((r) => r.TABLE_NAME)
            .filter((n) => !deselected.has(n));
        } else {
          rowKeys.values().forEach((k) => excluded.push(k));
        }

        self.excludedTables(excluded);
        self.selectionInfo(excluded.join(", "));
      };

      this.selectedSelectionMode.subscribe((newValue) => {
        // Reset selected Items on selection mode change.
        this.selectedItems({
          row: new ojkeyset_1.KeySetImpl(),
          column: new ojkeyset_1.KeySetImpl(),
        });
      });

      self.connected = function () {
        if (sessionStorage.getItem("userName") == null) {
          self.router.go({ path: "signin" });
        } else {
          app.onAppSuccess();
          getOnepDep();
          self.selectedSRCAliascategory("");
          self.selectedSRCUsercategory("");
          self.selectedTGTAliascategory("");
          self.selectedTGTUsercategory("");
          self.ExtoptParam([]);
          self.RepoptParam([]);
          self.onepDepList([]);
          self.selectedStepValue("stp1");
          self.selectedStepLabel("DataSource");
          self.selectedStepFormLabel("DataSource");
          self.currentExtType("SOURCEISTABLE");
          self.ExtName("");
          self.ExtDesc("");
          self.currentbeginmode("Begin Now");
          self.trailSubDir("");
          self.TrailName("");
          self.regVal("now");
          self.regExtChk(true);
          self.CDBCheck("");
          self.ButtonVal(true);
          self.pdbList([]);
          self.SrcOnePDepName("");
          self.TgtOnePDepName("");
          self.kinesisProxyServer("");
          self.kinesisProxyServerPort("");
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
      self.transitionCompleted = function () {};
    }
  }
  return InitialLoadViewModel;
});
