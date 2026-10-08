define([
  "ojs/ojcore",
  "knockout",
  "jquery",
  "appController",
  "ojs/ojoffcanvas",
  "ojDesigner/ggGridLayout",
  "text!../ojDesigner/data.json",
  "ojs/ojasyncvalidator-regexp",
  "ojs/ojconverterutils-i18n",
  "ojs/ojconverter-datetime",
  "ojs/ojconverter-number",
  "ojs/ojpagingdataproviderview",
  "ojs/ojarraydataprovider",
  "ojs/ojlistdataproviderview",
  "ojs/ojattributegrouphandler",
  "ojs/ojdiagram-utils",
  "ojs/ojkeyset",
  "ojs/ojknockout",
  "ojs/ojdiagram",
  "ojs/ojdialog",
  "ojs/ojradioset",
  "ojs/ojswitch",
  "ojs/ojcheckboxset",
  "ojs/ojdatetimepicker",
  "ojs/ojtrain",
  "ojs/ojlabel",
  "ojs/ojbutton",
  "ojs/ojlabelvalue",
  "ojs/ojavatar",
  "ojs/ojprogress-bar",
  "ojs/ojmenu",
  "ojs/ojselectsingle",
  "ojs/ojformlayout",
  "ojs/ojselectcombobox",
  "ojs/ojtable",
  "ojs/ojinputtext",
  "ojs/ojpagingcontrol",
  "ojs/ojvalidationgroup",
  "ojs/ojinputsearch",
], function (
  oj,
  ko,
  $,
  app,
  OffcanvasUtils,
  layout,
  jsonData,
  AsyncRegExpValidator,
  ConverterUtilsI18n,
  DateTimeConverter,
  NumberConverter,
  PagingDataProviderView,
  ArrayDataProvider,
  ListDataProviderView,
  ojattributegrouphandler_1,
  ojdiagram_utils_1,
  ojkeyset_1,
) {
  class DesignerViewModel {
    constructor(args) {
      var self = this;
      self.DepName = args.routerState.detail.dep_url;
      self.SrcOnePDepName = ko.observable();
      self.TgtOnePDepName = ko.observable();
      self.isFormReadonly = ko.observable(false);
      self.pdbSelList = ko.observableArray([]);
      self.pdbRegList = ko.observableArray([]);
      self.dialogTitle = ko.observable();

      self.groupValid = ko.observable();

      self.ExtName = ko.observable();
      self.ExtDesc = ko.observable();
      self.PmpName = ko.observable();
      self.PmpDesc = ko.observable();

      self.OPError = ko.observableArray([]);

      self.CancelBehaviorOpt = ko.observable("icon");

      self.startExtChk = ko.observable(false);
      self.startRepChk = ko.observable(false);
      self.currentTrailType = ko.observable();
      self.SRCcurrentPDB = ko.observable();
      self.TGTcurrentPDB = ko.observable();
      self.ExtName = ko.observable();
      self.ExtDesc = ko.observable();
      self.RepName = ko.observable();
      self.RepDesc = ko.observable();
      self.rmtOnepPort = ko.observable();
      self.rmtTrailName = ko.observable();
      self.rmttrailSubDir = ko.observable();
      self.dbTgtDetList = ko.observableArray([]);
      self.onepDepList = ko.observableArray([]);

      self.schemaList = ko.observableArray([]);
      self.selectedTGTCollections = ko.observable();

      self.gatherMeta = ko.observable(false);

      self.CDBCheck = ko.observable();
      self.isPDBLogin = ko.observable(false);
      self.SRConepDepUrl = ko.observable();
      self.TGTonepDepUrl = ko.observable();

      self.repType = ko.observableArray([]);
      self.currentRepType = ko.observable("parallel");
      self.paramValue = ko.observable("text area value");
      self.currentPassThru = ko.observable("passthru");
      self.rmtHostName = ko.observable();
      self.rmtMgrPort = ko.observable(0);
      self.ButtonVal = ko.observable(true);
      self.PDBName = ko.observable();

      self.progressTitle = ko.observable();

      self.dndData = JSON.parse(jsonData);
      self.colorHandler =
        new ojattributegrouphandler_1.ColorAttributeGroupHandler();
      self.nodes1 = ko.observableArray(self.dndData.nodesA);
      self.nodes2 = ko.observableArray(self.dndData.nodesB);
      self.links2 = ko.observableArray(self.dndData.linksB);
      self.nodeDataProvider1 = new ArrayDataProvider(self.nodes1, {
        keyAttributes: "id",
      });
      self.nodeDataProvider2 = new ArrayDataProvider(self.nodes2, {
        keyAttributes: "id",
      });
      self.linkDataProvider2 = new ArrayDataProvider(self.links2, {
        keyAttributes: "id",
      });

      self.getBaseColor = (anchor) => {
        return anchor
          ? self.colorHandler.getValue("1")
          : self.colorHandler.getValue("0");
      };
      self.getColor = (anchor, state, isInverted, isOuterCircle) => {
        let color = self.getBaseColor(anchor);
        if (state && state.selected && isOuterCircle) color = "red";
        else if (state && state.hovered && !isOuterCircle) color = "green";
        if (isInverted) {
          color = color === "blue" ? self.getBaseColor(anchor) : "white";
        }
        return color;
      };

      self.onDrop = (event, context, nodes, linkCleanUp) => {
        const diagramData =
          event.dataTransfer.getData("text/nodes1") ||
          event.dataTransfer.getData("text/nodes2");
        let newNodeId;
        // create new node
        if (diagramData) {
          const dataContext = JSON.parse(diagramData)[0];
          //remove specific node from from it's current location
          self.nodes1.remove((s) => {
            return s.id === dataContext.id;
          });
          self.nodes2.remove((s) => {
            return s.id === dataContext.id;
          });
          if (linkCleanUp)
            self.links2.remove((s) => {
              return s.start === dataContext.id || s.endNode === dataContext.id;
            });
          //add node to the target
          dataContext.itemData.x = context.nodeContext
            ? context.x + 100
            : context.x;
          dataContext.itemData.y = context.y;
          newNodeId = dataContext.itemData.id;
          nodes.push(dataContext.itemData);
        }
        if (context.nodeContext) {
          const startNodeId = context.nodeContext.id;
          self.links2.push({
            id: "L" + startNodeId + "_" + newNodeId,
            startNode: startNodeId,
            endNode: newNodeId,
          });
        } else if (context.linkContext) {
          const linkId = context.linkContext.id,
            startNode = context.linkContext.data.startNode,
            endNode = context.linkContext.data.endNode;
          self.links2.remove((s) => {
            return s.id === linkId;
          });
          self.links2.push({
            id: "L" + startNode + "_" + newNodeId,
            startNode: startNode,
            endNode: newNodeId,
          });
          self.links2.push({
            id: "L" + newNodeId + "_" + endNode,
            startNode: newNodeId,
            endNode: endNode,
          });
        }
      };
      self.labelLayoutFunc = (layoutContext, node) => {
        const nodeBounds = node["getContentBounds"]();
        const nodePos = node["getPosition"]();
        const labelLayout = {
          x: nodeBounds.x + nodePos.x + 0.5 * nodeBounds.w,
          y: nodeBounds.y + nodePos.y + 0.5 * nodeBounds.h,
          halign: "center",
          valign: "middle",
        };
        return labelLayout;
      };
      self.linkPathFunc = (layoutContext, link) => {
        const node1 = layoutContext.getNodeById(link["getStartId"]());
        const node2 = layoutContext.getNodeById(link["getEndId"]());
        const n1Pos = node1.getPosition(),
          n2Pos = node2.getPosition();
        const n1Bounds = node1.getBounds(),
          n2Bounds = node2.getBounds();
        const startX = n1Pos.x + 0.5 * n1Bounds.w;
        const startY = n1Pos.y + 0.5 * n1Bounds.h;
        const endX = n2Pos.x + 0.5 * n2Bounds.w;
        const endY = n2Pos.y + 0.5 * n2Bounds.h;
        return [startX, startY, endX, endY].toString();
      };
      self.onDrop1 = (event, context) => {
        self.onDrop(event, context, self.nodes1, true);
        //console.log(this.nodeContext())
      };
      self.onDrop2 = (event, context) => {
        self.onDrop(event, context, self.nodes2, false);
      };
      self.onLinkDrop = (event, context) => {
        self.onDrop(event, context, self.nodes2, false);
      };
      self.gridLayout = layout.gridLayout();
      self.dropLayout = ko.pureComputed(() => {
        return ojdiagram_utils_1.getLayout({
          nodes: self.nodes2(),
          links: self.links2(),
          nodeDefaults: { labelLayout: self.labelLayoutFunc },
          linkDefaults: { path: self.linkPathFunc },
          viewport: (layoutContext) => {
            if (layoutContext.getCurrentViewport()) {
              return layoutContext.getCurrentViewport();
            } else return layoutContext.getComponentSize();
          },
        });
      });

      self.selectedMenuItem = ko.observable("(None selected yet)");
      self.beforeOpenFunction = (event) => {
        const target = event.detail.originalEvent.target;
        const diagram = document.getElementById("diagram2");
        const context = diagram.getContextByNode(target);
        ((self.node = null), (self.link = null));
        if (context) {
          if (context.subId == "oj-diagram-node") {
            self.node = self.dndData.nodesB[context.index];
            self.selectedMenuItem(self.node.id);
          } else if (context.subId == "oj-diagram-link") {
            self.link = self.dndData.links[context.index];
          }
        }
      };
      self.menuItemAction = (event) => {
        const text = event.target.textContent;
        if (self.node) {
          self.selectedMenuItem(self.node.id);
          if (self.node.id == "Source Deployment") {
            getOnepDep();
            document.querySelector("#SelectDeployment").open();
          } else if (self.selectedMenuItem() == "Source CredentialStore") {
            document.querySelector("#SelectSrcCS").open();
          } else if (self.selectedMenuItem() == "Target CredentialStore") {
            document.querySelector("#SelectTgtCS").open();
          } else if (self.selectedMenuItem() == "Integrated Extract") {
            queryDBLMDict();
            self.currentExtType("Integrated Tranlog");
            self.selectedStepValue("stp1");
            self.selectedStepFormLabel("Extract Options");
            self.dialogTitle("Add Integrated Extract");
            document.querySelector("#AddExtract").open();
          } else if (self.selectedMenuItem() == "Classic Extract") {
            self.currentExtType("Tranlog");
            self.selectedStepValue("stp1");
            self.selectedStepFormLabel("Extract Options");
            self.dialogTitle("Add Classic Extract");
            document.querySelector("#AddExtract").open();
          } else if (self.selectedMenuItem() == "Extract Pump") {
            self.currentExtType("EXTTRAILSOURCE");
            self.selectedStepValue("stp1");
            self.selectedStepFormLabel("Extract Options");
            self.dialogTitle("Add Extract Pump");
            document.querySelector("#AddExtract").open();
            getExtTrails();
            self.ExtPrmList([]);
          } else if (self.selectedMenuItem() == "Target Deployment") {
            getOnepDep();
            document.querySelector("#SelectDeployment").open();
          } else if (self.selectedMenuItem() == "Classic Replicat") {
            self.currentRepType("");
            self.selectedStepValue("stp1");
            self.selectedStepFormLabel("Replicat Options");
            self.dialogTitle("Add Classic Replicat");
            document.querySelector("#addReplicat").open();
            getExtTrails();
          } else if (self.selectedMenuItem() == "Parallel Replicat") {
            self.currentRepType("PARALLEL");
            self.selectedStepValue("stp1");
            self.dialogTitle("Add Parallel Replicat");
            document.querySelector("#addReplicat").open();
            getExtTrails();
          } else if (self.selectedMenuItem() == "Integrated Replicat") {
            self.currentRepType("INTEGRATED");
            self.selectedStepValue("stp1");
            self.selectedStepFormLabel("Replicat Options");
            self.dialogTitle("Add Integarted Replicat");
            document.querySelector("#addReplicat").open();
            getExtTrails();
          } else if (
            self.selectedMenuItem() == "Parallel Integrated Replicat"
          ) {
            self.currentRepType("PARALLEL INTEGRATED");
            self.selectedStepValue("stp1");
            self.selectedStepFormLabel("Replicat Options");
            self.dialogTitle("Add Parallel Integarted Replicat");
            document.querySelector("#addReplicat").open();
            getExtTrails();
          } else if (self.selectedMenuItem() == "Coordinated Replicat") {
            self.currentRepType("COORDINATED INTEGRATED");
            self.selectedStepValue("stp1");
            self.selectedStepFormLabel("Replicat Options");
            self.dialogTitle("Add Coordinated Replicat");
            document.querySelector("#addReplicat").open();
            getExtTrails();
          }
        } else if (self.link) {
          self.selectedMenuItem(text + " from Link " + self.link.id);
        } else {
          self.selectedMenuItem(text + " from diagram background");
        }
      };

      self.RepName.subscribe(function (newValue) {
        if (newValue && newValue !== newValue.toUpperCase()) {
          self.RepName(newValue.toUpperCase());
        }
      });

      self.ExtName.subscribe(function (newValue) {
        if (newValue && newValue !== newValue.toUpperCase()) {
          self.ExtName(newValue.toUpperCase());
        }
      });

      self.PmpName.subscribe(function (newValue) {
        if (newValue && newValue !== newValue.toUpperCase()) {
          self.PmpName(newValue.toUpperCase());
        }
      });

      self.repNameMaxLen = ko.computed(function () {
        var t = self.currentRepType();
        return t === "PARALLEL" || t === "PARALLEL INTEGRATED" ? 5 : 8;
      });

      self.onepDepList = ko.observableArray([]);
      self.SRConepDepUrl = ko.observable();

      function getOnepDep() {
        self.onepDepList([]);
        $.ajax({
          url: self.DepName() + "/api/v2/onep/dep",
          type: "GET",
          dataType: "json",
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
            if (xhr.status == 0) {
              app.showGlobalError(
                app.deploymentUnreachableMessage(),
                "Connection Error",
              );
              return;
            }
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

      self.srcSourceDb = ko.observable("");
      self.tgtTargetDb = ko.observable("");

      function fetchSourceDb() {
        self.srcSourceDb("");
        if (!self.SRCcurrentPDB()) return;
        $.ajax({
          url: self.SRConepDepUrl() + "/api/v2/db/sourcedb",
          type: "POST",
          data: JSON.stringify({ dbname: self.SRCcurrentPDB() }),
          dataType: "json",
          contentType: "application/json",
          showProgress: false,
          suppressGlobalError: true,
          error: function (xhr) {
            if (xhr.status === 401) { app.handleSessionExpired(); return; }
          },
          success: function (data) {
            self.srcSourceDb(data.sourcedb || "");
          },
        });
      }

      function fetchTargetDb() {
        self.tgtTargetDb("");
        if (!self.TGTcurrentPDB()) return;
        self.tgtAjax({
          url: self.TGTonepDepUrl() + "/api/v2/db/sourcedb",
          type: "POST",
          data: JSON.stringify({ dbname: self.TGTcurrentPDB() }),
          dataType: "json",
          contentType: "application/json",
          showProgress: false,
          suppressGlobalError: true,
          error: function () {},
          success: function (data) {
            self.tgtTargetDb(data.sourcedb || "");
          },
        });
      }

      self.SrcOnepDepType = ko.observable("");

      self.SelectSRCDeployment = (event, data) => {
        if (self.SrcOnePDepName()) {
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
                  "Deployment Error",
                );
              } else {
                app.showGlobalError(
                  app.extractErrorMessage(xhr),
                  "Deployment Error",
                );
              }
            },
            success: function (data) {
              self.SRConepDepUrl(data[0]);
              self.trailSubDirBase(data[1]);
              self.SrcOnepDepType((data[2] || "").toLowerCase());
              return self;
            },
          });
        }
      };

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

      self.ChooseSrcDepOkClose = function () {
        var valid = self._checkValidationGroup("DeploymentGRP");
        if (valid) {
          getSrcDomains();
          document.querySelector("#SelectDeployment").close();
        }
      };

      self.ChooseTgtDepOkClose = function () {
        var valid = self._checkValidationGroup("DeploymentGRP");
        if (valid) {
          getTgtDomains();
          document.querySelector("#SelectDeployment").close();
        }
      };

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

      self.ExtoptParam = ko.observableArray([]);
      self.PmpoptParam = ko.observableArray([]);
      self.RepoptParam = ko.observableArray([]);

      self.currentTrailType = ko.observable("exttrail");

      self.paramValue = ko.observable("text area value");
      self.currentPassThru = ko.observable("passthru");

      self.isDDLChecked = ko.observable();

      self.isGetTruncChecked = ko.observable();
      self.isEncrytChecked = ko.observable();
      self.isNoUseSnapChecked = ko.observable();
      self.isExcludeTagChecked = ko.observable();
      self.isGetUpdBefChecked = ko.observable();
      self.Threads = ko.observable(1);

      self.LMDict = ko.observableArray([]);
      self.CaptureList = ko.observableArray([]);
      self.CaptureName = ko.observable(" ");
      self.CDBCheck = ko.observable();

      self.toggleOuter = () => {
        return OffcanvasUtils.toggle(self.outerDrawer);
      };
      self.outerDrawer = {
        displayMode: "push",
        selector: "#oDrawer",
        content: "#oMain",
        autoDismiss: "none",
      };

      function queryDBLMDict() {
        $.ajax({
          url: self.SRConepDepUrl() + "/api/v2/db/lmdictdet",
          type: "POST",
          dataType: "json",
          contentType: "application/json",
          data: JSON.stringify({ dbname: self.SRCcurrentPDB() }),
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Fetching LogMiner dictionary details",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to fetch LogMiner dictionary details. ${msg}`,
              "LogMiner Dictionary Error",
            );
          },
          success: function (data) {
            self.CaptureList([]);
            for (var i = 0; i < data[0].length; i++) {
              self.CaptureList.push({
                label: data[0][i].CLIENT_NAME,
                value: data[0][i].CLIENT_NAME,
              });
            }
            self.LMDict([]);
            for (var i = 0; i < data[1].length; i++) {
              self.LMDict.push({
                FIRST_CHANGE: data[1][i].first_change,
                FIRST_TIME: data[1][i].first_time,
              });
            }
            return self;
          },
        });
      }

      self.DBLMDictDP = new ArrayDataProvider(self.LMDict, {
        keyAttributes: "FIRST_CHANGE",
        textFilterAttributes: ["FIRST_CHANGE", "FIRST_TIME"],
      });
      self.CaptureListDP = new ArrayDataProvider(self.CaptureList, {
        keyAttributes: "value",
      });

      self.ExtPrmList = ko.observableArray([]);
      self.ExtPrmListREP = ko.observableArray([]);
      self.ExtTrailName = ko.observable();

      self.queryExtPrm = function (event, data) {
        if (self.TGTonepDepUrl()) {
          self.ExtTrailName("");
          $.ajax({
            url: self.SRConepDepUrl() + "/api/v2/extract/param",
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
                `Unable to fetch extract parameters for "${self.CurrentExtName()}". ${msg}`,
                "Extract Parameters Error",
              );
            },
            success: function (data) {
              console.log(data);
              
              for (var i = 0; i < self.ExtList().length; i++) {
                if (self.ExtList()[i].value == self.CurrentExtName()) {
                  self.ExtTrailName(self.ExtList()[i].children.value);
                }
              }
              self.ExtPrmList(data[0]);

              var sourceCatalogLines = data[0].filter((line) =>
                line.startsWith("SOURCECATALOG"),
              );

              data[0] = data[0].filter(
                (line) => !line.startsWith("SOURCECATALOG"),
              );
              data[0] = data[0].filter((line) => !line.startsWith("SEQUENCE"));

              for (var j = 0; j < data[0].length; j++) {
                if (data[0][j].startsWith("TABLEEXCLUDE")) {
                  data[0][j] = data[0][j].replace("TABLEEXCLUDE", "MAPEXCLUDE");
                } else if (data[0][j].startsWith("TABLE")) {
                  const tableName = data[0][j]
                    .match(/TABLE\s+(.+);?/)[1]
                    .replace(/;$/, "");
                  data[0][j] = `MAP ${tableName}, TARGET ${tableName};`;
                } else {
                  data[0][j] = data[0][j];
                }
                self.ExtPrmListREP.push(data[0][j]);
              }

              var repList = sourceCatalogLines.concat(data[0]);

              self.ExtPrmListREP(repList);
              return self;
            },
          });
        }
      };

      self.lmDictSCN = ko.observable(" ");

      self.getItemText = function (itemContext) {
        return itemContext.data.FIRST_CHANGE;
      };

      self.tableColumns = [
        { headerText: "SCN", field: "FIRST_CHANGE", template: "cellTemplate" },
        {
          headerText: "Create Time",
          field: "FIRST_TIME",
          template: "cellTemplate",
        },
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
          url: self.SRConepDepUrl() + "/api/v2/exttrail/list",
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
                children: { value: data[0][i].value },
              });
            }
            return self;
          },
        });
      }

      self.ExtListDP = new ArrayDataProvider(self.ExtList, {
        keyAttributes: "value",
      });

      self.currentExtType = ko.observable();

      self.CEOPT = ko.observable("LR");
      self.regExtChk = ko.observable(true);

      self.isFormReadonly = ko.observable(false);

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
      self.csnVal = ko.observable();

      self.decimalHalfDownConverter = new NumberConverter.IntlNumberConverter({
        style: "decimal",
        roundingMode: "HALF_DOWN",
        maximumFractionDigits: 0,
        useGrouping: false,
      });

      self.ExtTrail = ko.observable();
      self.ExtTrailSize = ko.observable("500");

      self.modeVal = ko.observable("Integrated Tranlog");

      self.currentbeginmode = ko.observable("NOW");

      self.TrailName = ko.observable("ET");
      self.trailSubDirBase = ko.observable();
      self.trailSubDir = ko.pureComputed(function () {
        var base = self.trailSubDirBase() || "";
        var ext = self.ExtName();
        if (base && ext) {
          return base.replace(/\/$/, "") + "/" + ext;
        }
        return base;
      });
      self.trailSubDirSlash = ko.observable("/");
      self.trailSize = ko.observable(500);

      self.beginmode = ko.observableArray([
        { value: "NOW", label: "NOW" },
        { value: "ATCSN", label: "ATCSN" },
        { value: "AFTERCSN", label: "AFTERCSN" },
      ]);

      self.startOptionDP = new ArrayDataProvider(self.beginmode, {
        keyAttributes: "value",
      });

      //Get the Credentail Alias Domains

      function getSrcDomains() {
        if (self.SRConepDepUrl()) {
          self.SRCusername1([]);
          self.SRCothdom([]);
          self.SRCaliasname1([]);
          self.SRCdomname1([]);
          $.ajax({
            url: self.SRConepDepUrl() + "/api/v2/vault/info/all",
            type: "GET",
            dataType: "json",
            timeout: sessionStorage.getItem("timeInetrval"),
            progressMessage: `Fetching source credential domains ${self.SrcOnePDepName()}`,
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
              if (textStatus === "abort") return;
              if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
              var msg = app.extractErrorMessage(xhr);
              app.showGlobalError(
                `Unable to fetch source credential domains for "${self.SrcOnePDepName()}"  — could not reach ${self.SRConepDepUrl()}. ${msg}`,
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
              return self;
            },
          });
        }
      }

      self.dbTgtDetList = ko.observableArray([]);
      self.TgtonepDepType = ko.observable();

      self.SelectTGTDeployment = (event, data) => {
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
            self.TGTonepDepUrl(data[0]);
            self.TgtonepDepType(data[2]);

            // if (self.TgtonepDepType() == "mongodb") {
            //   self.fetchTgtDepToken(self.TgtOnePDepName());
            // }

            var key = "Tgt_" + self.TgtOnePDepName() + "_AccessToken";
            if (data[3]) sessionStorage.setItem(key, data[3]);
            else sessionStorage.removeItem(key);

            getRmtHost();
            return self;
          },
        });
      };

      self.fetchTgtDepToken = function (depName, callback) {
        $.ajax({
            url: self.DepName() + "/api/v2/onep/deptoken",
            type: "POST",
            data: JSON.stringify({ dep: depName }),
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            suppressGlobalError: true,
            error: function (xhr, textStatus) {
                if (textStatus === "abort") { if (callback) callback(false); return; }
                if (xhr.status === 401) { 
                  if (callback) { callback(false); return; }
                  app.handleSessionExpired();
                  return;
                }
                var msg = app.extractErrorMessage(xhr);
                if (callback) {
                  callback(false);
                } else {
                  app.showGlobalError(`Unable to authenticate to target deployment "${depName}". ${msg}`, "Target Auth Error");
                }
            },
            success: function (data) {
                console.log(data);
                
                // Namespace by deployment name so multiple targets don't collide
                sessionStorage.setItem("Tgt_" + depName + "_AccessToken", data.access_token);
                sessionStorage.setItem("Tgt_" + depName + "_onepsuid", data.onepsuid);
                sessionStorage.setItem("Tgt_" + depName + "_DepUrl", data.dep_url);
                sessionStorage.setItem("Tgt_" + depName + "_DbType", data.dbtype);

                if (callback) callback(true);
            },
        });
      };

      self.tgtAjax = function (ajaxOpts) {
        if (!["mongodb", "sqlserver"].includes(self.TgtonepDepType())) {
          $.ajax(ajaxOpts);
          return;
        }
        ajaxOpts.isTargetCall = true;
        var originalError = ajaxOpts.error;
        var depName = self.TgtOnePDepName();
        var alreadyRetried = false;

        ajaxOpts.headers = self.tgtAuthHeader();

        ajaxOpts.error = function (xhr, textStatus, errorThrown) {
          if (textStatus === "abort") {
            if (originalError) originalError(xhr, textStatus, errorThrown);
            return;
          }

          if (xhr.status === 401 && !alreadyRetried) {
            alreadyRetried = true;
            self.fetchTgtDepToken(depName, function (success) {
              if (success) {
                // rebuild headers with the fresh token and retry the same request
                ajaxOpts.headers = self.tgtAuthHeader();
                $.ajax(ajaxOpts);
              } else if (originalError) {
                originalError(xhr, textStatus, errorThrown);
              }
            });
            return;
          }

          if (originalError) originalError(xhr, textStatus, errorThrown);
        };
        $.ajax(ajaxOpts);
      };

      self.tgtAuthHeader = function () {
        if (!["mongodb", "sqlserver"].includes(self.TgtonepDepType())) {
          return undefined;
        }
        var token = sessionStorage.getItem("Tgt_" + self.TgtOnePDepName() + "_AccessToken");
        return token ? { "Authorization": "Bearer " + token } : undefined;
      };

      function getRmtHost(data, event) {
        if (self.TGTonepDepUrl()) {
          self.rmtHostName("");
          self.rmtMgrPort();
          self.rmttrailSubDir("");
          let url = "/api/v2/info/all"
          if (["postgresql", "mongodb", "sqlserver"].includes(self.TgtonepDepType())) {
            url = "/api/v2/gginfoall"
          }       
          var ajaxOpts = {
            url: self.TGTonepDepUrl() + url,
            type: "GET",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
            progressMessage: `Fetching target deployment info ${self.TgtOnePDepName()}`,
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
              console.log(data);
              
              self.rmtHostName(
                self.TGTonepDepUrl().split(":")[1].replace("//", ""),
              );
              self.rmtMgrPort(data[5])
              // for (var i = 0; i < data[0].length; i++) {
              //   self.rmtMgrPort(data[0][i].mgrport);
              // }
              self.rmttrailSubDir(data[2]);
              return self;
            },
          };
          self.tgtAjax(ajaxOpts);
        }
      }
      function getTgtDomains(data, event) {
        if (self.TGTonepDepUrl()) {
          self.TGTusername1([]);
          self.TGTothdom([]);
          self.TGTaliasname1([]);
          self.TGTdomname1([]);
          let url = "/api/v2/vault/info/all"
          if (["postgresql", "mongodb", "sqlserver"].includes(self.TgtonepDepType())) {
            url = "/api/v2/credstore"
          }

          var ajaxOpts = {
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
              console.log(data);
              
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

          self.tgtAjax(ajaxOpts);
        }
      }

      self.replicatDP = new ArrayDataProvider(self.repType, {
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
        self.PDBName();
      };

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

      self.TGTaliasSelectionChanged = (event) => {
        self.selectedTGTUsercategory("");
        let children = TGTgetUnamecategories(event.detail.value);
        self.TGTunamecategories(children);
      };

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

      self.PDBNameList = ko.observableArray([]);
      self.schemaNameList = ko.observableArray([]);
      self.dbDetList = ko.observableArray([]);

      self.CDBData = function (data, event) {
        fetchSourceDb();
        self.CDBCheck("");
        self.PDBNameList([]);
        self.dbDetList([]);
        self.schemaNameList([]);
        self.schemaList([]);
        self.PDBName("");
        self.OPError([]);
        self.tableNameList([]);
        self.selectionInfo("");
        self.selectedItems({
          row: new ojkeyset_1.KeySetImpl(),
          column: new ojkeyset_1.KeySetImpl(),
        });

        $.ajax({
          url: self.SRConepDepUrl() + "/api/v2/db/cdbcheck",
          type: "POST",
          data: JSON.stringify({ dbname: self.SRCcurrentPDB() }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Fetching db details",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to fetch schema details. ${msg}`,
              "Schema Details Error",
            );
          },
          success: function (data) {
            self.CDBCheck(data[0]);
            self.isPDBLogin(data[5]);

            if (data[5]) {
              for (var i = 0; i < data[2].length; i++) {
                self.schemaNameCDBList.push({
                  label: data[2][i].username,
                  value: data[2][i].username,
                });
              }
              self.schemaNameCDBList.valueHasMutated();
            }
            if (!data[1].includes("ORA-")) {
              for (var i = 0; i < data[1].length; i++) {
                self.PDBNameList.push({
                  label: data[1][i].name,
                  value: data[1][i].name,
                });
              }
              self.PDBNameList.valueHasMutated();

              for (var i = 0; i < data[2].length; i++) {
                self.schemaNameList.push({
                  label: data[2][i].username,
                  value: data[2][i].username,
                });
              }
              self.schemaNameList.valueHasMutated();
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

              self.trailSubDirBase(data[4]);
            } else {
              document.querySelector("#DBErrDialog").open();
              self.OPError(data[1]);
            }
            return self;
          },
        });
      };

      self.DBErrorOKClose = function (event) {
        document.querySelector("#DBErrDialog").close();
      };

      self.PDBNameListDP = new ArrayDataProvider(self.PDBNameList, {
        keyAttributes: "value",
      });
      self.schemaNameListDP = new ArrayDataProvider(self.schemaNameList, {
        keyAttributes: "value",
      });

      self.srcLoginParam = ko.pureComputed(function () {
        var login = "USERIDALIAS " + self.SRCcurrentPDB() +
                    " DOMAIN " + self.selectedSRCDomCategory();
        if (self.SrcOnepDepType() !== "oracle" && self.srcSourceDb()) {
          return "SOURCEDB " + self.srcSourceDb() + ", " + login;
        }
        return login;
      });

      self.tgtLoginParam = ko.pureComputed(function () {
        var login = "USERIDALIAS " + self.TGTcurrentPDB() +
                    " DOMAIN " + self.selectedTGTDomCategory();
        if (self.TgtonepDepType() === "sybase" && self.tgtTargetDb()) {
          return "TARGETDB " + self.tgtTargetDb() + ", " + login;
        }
        return login;
      });

      self.schemaNameCDBList = ko.observableArray([]);

      self.SRCDBSchema = function (data, event) {
        self.schemaNameCDBList([]);
        $.ajax({
          url: self.SRConepDepUrl() + "/api/v2/db/supplogschema",
          type: "POST",
          data: JSON.stringify({
            dbname: self.SRCcurrentPDB(),
            cdbCheck: self.CDBCheck(),
            pdbName: self.PDBName(),
          }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Fetching schema details",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to fetch schema details. ${msg}`,
              "Schema Details Error",
            );
          },
          success: function (data) {
            if (data[0].includes("ORA-")) {
              document.querySelector("#DBErrDialog").open();
              self.OPError(data[0]);
            } else {
              for (var i = 0; i < data[0].length; i++) {
                self.schemaNameCDBList.push({
                  label: data[0][i].USERNAME,
                  value: data[0][i].USERNAME,
                });
              }
              self.schemaNameCDBList.valueHasMutated();
            }
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

      self.dbTgtDetList = ko.observableArray([]);

      self.dbVer = ko.observable(0);

      self.DBTgtSchema = function (data, event) {
        fetchTargetDb();
        self.trailSubDirBase("");
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
          progressMessage: "Fetching target db details",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
            `Unable to fetch target schema details. ${msg}`,
            "Schema Details Error",
          );
        },
        success: function (data) {
          console.log(data);
          self.dbTgtDetList([]);

          if (self.TgtonepDepType() == "postgresql") {
            for (var i = 0; i < data[3].length; i++) {
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
            }
          } else if (self.TgtonepDepType() == "mongodb") {
            var m = data[1]; // msg object, not an array — pushed once
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
            self.fetchTgtCollections(); 
          } else if (self.TgtonepDepType() == "sybase") {
            var sErr = typeof data[1] === "string" ? data[1] : "";
            if (sErr && sErr.toLowerCase().includes("error")) {
              self.OPError(sErr);
              document.querySelector("#DBErrDialog").open();
              return self;
            }
            for (var k = 0; k < (data[3] || []).length; k++) {
              var row = data[3][k];
              self.dbTgtDetList.push({
                dbname:    row.DBNAME,
                host:      row.HOST,
                version:   row.VERSION,
                dbedition: row.DB_EDITION,
              });
              self.dbVer(row.VERSION || "");
            }
          } else if (self.TgtonepDepType() == "sqlserver") {
            if (typeof data[0] === "string") {          // error text from backend
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
          }
          else {
            for (var i = 0; i < data[3].length; i++) {
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
            }
          }

          self.dbTgtDetList.valueHasMutated();

          self.trailSubDirBase(data[4]);
          queryChkTbl();
          return self;
        },
      };

      self.tgtAjax(ajaxOpts);
    };
      
      function getGGVersion() {
        self.repType([]);
        var ajaxOpts = {
            url: self.TGTonepDepUrl() + "/api/v2/get-version",
            type: "GET",
            dataType: "json",
            contentType: "application/json",
            timeout: sessionStorage.getItem("timeInetrval"),
            progressMessage: "Fetching GoldenGate version",
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

      self.tableNameList = ko.observableArray([]);
      let LoadName = "";

      self.SrcDBSchemaFetch = function (data, event) {
        $.ajax({
          url: self.SRConepDepUrl() + "/api/v2/db/tablelist",
          type: "POST",
          data: JSON.stringify({
            dbname: self.SRCcurrentPDB(),
            schemaList: self.schemaList(),
            cdbCheck: self.CDBCheck(),
            pdbName: self.PDBName(),
            gatherMeta: self.gatherMeta(),
            LoadName: LoadName,
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
            document.querySelector("#TABLEExclude").open();

            self.tableNameList([]);
            for (var i = 0; i < data[0].length; i++) {
              self.tableNameList.push({
                TABLE_NAME: data[0][i].owner + "." + data[0][i].table_name,
                ROWCNT: data[0][i].num_rows,
                AVGSPC: data[0][i].avg_space,
                ANALYZETIME: data[0][i].last_analyzed,
              });
            }
            self.tableNameList.valueHasMutated();
            return self;
          },
        });
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

      self.ChooseExcludeOkClose = function () {
        document.querySelector("#Progress").close();
        document.querySelector("#TABLEExclude").close();
      };

      self.ChooseCredOkClose = function () {
        if (self.selectedMenuItem() == "Source CredentialStore") {
          var valid = self._checkValidationGroup("SelectSrcCSGRP");
        } else if (self.selectedMenuItem() == "Target CredentialStore") {
          var valid = self._checkValidationGroup("SelectTgtCSGRP");
        }

        if (valid) {
          if (self.selectedMenuItem() == "Source CredentialStore") {
            document.querySelector("#SelectSrcCS").close();
          } else if (self.selectedMenuItem() == "Target CredentialStore") {
            document.querySelector("#SelectTgtCS").close();
          }
        }
      };

      //vallidation start

      self._checkValidationGroup = (value) => {
        var tracker = document.getElementById(value);
        if (!tracker) {
          console.warn("Validation group not found: " + value);
          return false;
        }
        if (tracker.valid === "valid") {
          return true;
        } else {
          tracker.showMessages();
          tracker.focusOn("@firstInvalidShown");
          return false;
        }
      };

      self.validate = (event) => {
        if (
          self.selectedMenuItem() == "Integrated Extract" ||
          self.selectedMenuItem() == "Extract Pump" ||
          self.selectedMenuItem() == "Classic Extract"
        ) {
          var valid = self._checkValidationGroup("addExtractGRP");
          // var valid = self._checkValidationGroup("AddExtractGRP");
        } else if (self.selectedMenuItem() == "Classic Replicat") {
          var valid = self._checkValidationGroup("addReplicatGRP");
        }
        //var valid = self._checkValidationGroup("addReplicatGRP");
        if (valid) {
          return true;
        } else {
          //The ojBeforeSelect can be cancelled by calling event.preventDefault().
          event.preventDefault();
          return;
        }
      };

      self.validateRep = (event) => {
        if (
          self.selectedMenuItem() == "Classic Replicat" ||
          self.selectedMenuItem() == "Parallel Replicat" ||
          self.selectedMenuItem() == "Integrated Replicat" ||
          self.selectedMenuItem() == "Parallel Integrated Replicat" ||
          self.selectedMenuItem() == "Coordinated Replicat"
        ) {
          var valid = self._checkValidationGroup("addReplicatGRP");
        }
        if (valid) {
          return true;
        } else {
          //The ojBeforeSelect can be cancelled by calling event.preventDefault().
          event.preventDefault();
          return;
        }
      };

      //end

      self.tableListcolumnArray = [
        {
          headerText: "Schema.Table Name",
          field: "TABLE_NAME",
        },
        {
          headerText: "Row Count",
          field: "ROWCNT",
        },
        {
          headerText: "Average Size(MB)",
          field: "AVGSPC",
        },
        {
          headerText: "Analyze Time",
          field: "ANALYZETIME",
        },
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

      self.mongoDbDetcolumnArray = [
        { headerText: "DB Name", field: "dbname" },
        { headerText: "Product Version", field: "version" },
        { headerText: "Host", field: "host" },
        { headerText: "Clustered", field: "clustered" },
        { headerText: "Replica Members", field: "replicaMembers" },
        { headerText: "Storage Engine", field: "storageEngine" },
        { headerText: "Data Size (MB)", field: "dataSizeMB" },
        { headerText: "Storage Size (MB)", field: "storageSizeMB" },
        { headerText: "Collections", field: "collectionCount" },
        { headerText: "Indexes", field: "indexCount" },
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

      self.valueChangedHandler = (event) => {
        self.ButtonVal(false);
      };
      self.selectionInfo = ko.observable("");

      self.selectedItems = ko.observable({
        row: new ojkeyset_1.KeySetImpl(),
        column: new ojkeyset_1.KeySetImpl(),
      });

      self.selectedSelectionMode = ko.observable({
        row: "multiple",
        column: "none",
      });
      self.selectionModes = [
        { value: { row: "none", column: "single" }, label: "Single Column" },
        {
          value: { row: "none", column: "multiple" },
          label: "Multiple Column",
        },
        { value: { row: "single", column: "none" }, label: "Single Row" },
        { value: { row: "multiple", column: "none" }, label: "Multiple Row" },
      ];
      self.selectionModeDP = new ArrayDataProvider(self.selectionModes, {
        keyAttributes: "value",
      });

      self.selectedChangedListener = (event) => {
        let selectionText = "";
        if (event.detail.value.row.isAddAll()) {
          const row = self.tableNameList();
          const iterator = event.detail.value.row.deletedValues();

          const deletedKeys = new Set();
          iterator.forEach(function (key) {
            deletedKeys.add(key);
          });

          for (var i = 0; i < row.length; i++) {
            if (!deletedKeys.has(row[i].TABLE_NAME)) {
              selectionText =
                selectionText.length === 0
                  ? row[i].TABLE_NAME
                  : `${selectionText}, ${row[i].TABLE_NAME}`;
            }
          }
          selectionText = selectionText.replace(/,\s*$/, "");
        } else {
          const row = event.detail.value.row;
          const column = event.detail.value.column;
          if (row.values().size > 0) {
            row.values().forEach(function (key) {
              selectionText += selectionText.length === 0 ? key : ", " + key;
            });
            selectionText = "" + selectionText;
          }
          if (column.values().size > 0) {
            column.values().forEach(function (key) {
              selectionText += selectionText.length === 0 ? key : ", " + key;
            });
            selectionText = "Column Selection:\nColumn Keys: " + selectionText;
          }
        }
        self.selectionInfo(selectionText);
      };
      self.selectedSelectionMode.subscribe((newValue) => {
        // Reset selected Items on selection mode change.
        self.selectedItems({
          row: new ojkeyset_1.KeySetImpl(),
          column: new ojkeyset_1.KeySetImpl(),
        });
      });

      self.selectedStepValue = ko.observable("stp1");
      self.selectedStepLabel = ko.observable("Extract Options");
      self.selectedStepFormLabel = ko.observable("Extract Options");

      self.stepArray = ko.observableArray([
        { label: "Extract Options", id: "stp1" },
        { label: "Parameter File", id: "stp2" },
      ]);
      self.stepRepArray = ko.observableArray([
        { label: "Replicat Options", id: "stp1" },
        { label: "Parameter File", id: "stp2" },
      ]);

      self.previousStep = function () {
        if (
          self.selectedMenuItem() == "Integrated Extract" ||
          self.selectedMenuItem() == "Extract Pump" ||
          self.selectedMenuItem() == "Classic Extract"
        ) {
          var train = document.getElementById("train");
        } else {
          var train = document.getElementById("repTrain");
        }
        var prev = train.getPreviousSelectableStep();
        if (prev != null) {
          self.selectedStepValue(prev);
          self.selectedStepLabel(train.getStep(prev).label);
          self.selectedStepFormLabel(train.getStep(prev).label);
        }
      };

      self.nextStep = function (event) {
        if (
          self.selectedMenuItem() == "Integrated Extract" ||
          self.selectedMenuItem() == "Extract Pump" ||
          self.selectedMenuItem() == "Classic Extract"
        ) {
          var valid = self._checkValidationGroup("addExtractGRP");
          var train = document.getElementById("train");
          var train_id = "train";
        } else if (
          self.selectedMenuItem() == "Classic Replicat" ||
          self.selectedMenuItem() == "Parallel Replicat" ||
          self.selectedMenuItem() == "Integrated Replicat" ||
          self.selectedMenuItem() == "Parallel Integrated Replicat" ||
          self.selectedMenuItem() == "Coordinated Replicat"
        ) {
          var valid = self._checkValidationGroup("addReplicatGRP");
          var train = document.getElementById("repTrain");
          var train_id = "repTrain";
        }
        var next = train.getNextSelectableStep();

        if (valid) {
          //The previous step will have a confirmation message type icon
          self.selectedStepLabel.messageType = "confirmation";
          document
            .getElementById(train_id)
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
            .getElementById(train_id)
            .updateStep(self.selectedStepLabel.id, self.selectedStepLabel);
          return;
        }
      };

      self.updateLabelText = function (event) {
        if (self.selectedStepValue() == "stp1") {
          self.selectedStepFormLabel("Extract Options");
          self.isFormReadonly(false);
        } else if (self.selectedStepValue() == "stp2") {
          self.selectedStepFormLabel("Parameter File");
          self.isFormReadonly(false);
        }
      };

      self.updateRepLabelText = function (event) {
        if (self.selectedStepValue() == "stp1") {
          self.selectedStepFormLabel("Replicat Options");
          self.isFormReadonly(false);
        } else if (self.selectedStepValue() == "stp2") {
          self.selectedStepFormLabel("Parameter File");
          self.isFormReadonly(false);
        }
      };

      self.newExtParamList = ko.observable("");
      self.newPmpParamList = ko.observable("");
      self.newRepParamList = ko.observable("");

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

      self.currentSchemaParam = ko.computed({
        read: function () {
          var currentSchemaParam = "";
          if (self.CDBCheck() == "YES" && self.PDBName().length > 0) {
            var currentSchemaParam = "SOURCECATALOG " + self.PDBName() + "\n";
            if (self.selectionInfo().length > 0) {
              let selectedData = self.selectionInfo().split(",");
              for (var i = 0; i < selectedData.length; i++) {
                currentSchemaParam =
                  currentSchemaParam + "TABLEEXCLUDE " + selectedData[i] + "\n";
              }
            }
          } else {
            if (self.selectionInfo().length > 0) {
              let selectedData = self.selectionInfo().split(",");
              for (var i = 0; i < selectedData.length; i++) {
                currentSchemaParam =
                  currentSchemaParam + "TABLEEXCLUDE " + selectedData[i] + "\n";
              }
            }
          }
          return currentSchemaParam;
        },
      });

      self.ExtSchemaParam = ko.computed({
        read: function () {
          var ExtSchemaParam = "";
          if (self.CDBCheck() == "YES" && self.PDBName().length > 0) {
            for (var i = 0; i < self.schemaList().length; i++) {
              ExtSchemaParam =
                ExtSchemaParam +
                "TABLE " +
                self.schemaList()[i] +
                ".* ;" +
                "\n";
            }
          } else {
            for (var i = 0; i < self.schemaList().length; i++) {
              ExtSchemaParam =
                ExtSchemaParam + "TABLE " + self.schemaList()[i] + ".*;" + "\n";
            }
          }
          return ExtSchemaParam;
        },
      });

      self.SrcExtTrail = ko.computed({
        read: function () {
          if (self.ExtName()) {
            var SrcExtTrail =
              self.trailSubDir() + self.trailSubDirSlash() + self.TrailName();
          } else {
            var SrcExtTrail = self.ExtTrailName();
          }

          return SrcExtTrail;
        },
      });

      self.SrcRmtTrail = ko.computed({
        read: function () {
          if (self.PmpName()) {
            var SrcRmtTrail =
              self.rmttrailSubDir() +
              self.trailSubDirSlash() +
              self.rmtTrailName();
          } else if (self.ExtName()) {
            var SrcRmtTrail =
              self.trailSubDir() + self.trailSubDirSlash() + self.TrailName();
          } else {
            var SrcRmtTrail = self.ExtTrailName();
          }
          return SrcRmtTrail;
        },
      });

      self.rmthostParam = ko.computed({
        read: function () {
          var rmthostParam = "";
          if (self.currentTrailType() == "exttrail") {
            var rmthostParam = "exttrail " + self.SrcExtTrail() + "\n";
          } else if (
            self.currentTrailType() == "rmttrail" ||
            self.currentExtType() === "Pump"
          ) {
            var rmthostParam =
              "RMTHOST " +
              self.rmtHostName() +
              ",MGRPORT " +
              self.rmtMgrPort() +
              " , TCPBUFSIZE  4194304,TCPFLUSHBYTES 4194304,ENCRYPT AES256" +
              "\n" +
              "ENCRYPTTRAIL" +
              "\n" +
              "rmttrail " +
              self.trailSubDir() +
              self.trailSubDirSlash() +
              self.TrailName() +
              "\n";
          }

          return rmthostParam;
        },
      });

      self.currentExtParam = ko.computed({
        read: function () {
          return (
            "EXTRACT " + self.ExtName() + "\n" +
            self.srcLoginParam() + "\n" +
            self.rmthostParam() + "\n" +
            "REPORTCOUNT EVERY 5 MINUTES, RATE" + "\n" +
            self.currentExtOptParamList() + "\n" +
            self.currentSchemaParam() +
            self.ExtSchemaParam()
          );
        },
      });

      self.AddExtractMsg = ko.observableArray([]);

      self.addIE = function (data, event) {
        self.AddExtractMsg([]);
        $.ajax({
          url: self.SRConepDepUrl() + "/api/v2/extract/add-integrated",
          type: "POST",
          data: JSON.stringify({
            regExtChk: self.regExtChk(),
            regVal: self.regVal(),
            lmDictSCN: self.lmDictSCN(),
            currentShareOpt: self.currentShareOpt(),
            CaptureName: self.CaptureName(),
            extname: self.ExtName(),
            extdesc: self.ExtDesc(),
            domain: self.selectedSRCDomCategory(),
            alias: self.SRCcurrentPDB(),
            mode: self.currentExtType(),
            beginmode: self.currentbeginmode(),
            trailtype: self.currentTrailType(),
            trailsubdir: self.trailSubDir(),
            trailsubdirslash: self.trailSubDirSlash(),
            trail: self.TrailName(),
            trailsize: self.trailSize(),
            currentExtParamList: self.newExtParamList(),
            startExtChk: self.startExtChk(),
            CDBCheck: self.CDBCheck(),
            PDBName: self.PDBName(),
            pdbSelList: self.pdbRegList(),
            isPDBLogin: self.isPDBLogin(),
          }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: `Creating integrated extract ${self.ExtName()}`,
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to create integrated extract "${self.ExtName()}". ${msg}`,
              "Create Extract Error",
            );
          },
          success: function (data) {
            document.querySelector("#AddExtract").close();
            self.dialogTitle("Integrated Extract " + self.ExtName());
            document.querySelector("#AddExtractDialog").open();
            self.AddExtractMsg(data[0]);
            return self;
          },
        });
      };

      self.addCE = function (data, event) {
        self.AddExtractMsg([]);
        $.ajax({
          url: self.SRConepDepUrl() + "/api/v2/extract/add-classic",
          type: "POST",
          data: JSON.stringify({
            extname: self.ExtName(),
            extdesc: self.ExtDesc(),
            domain: self.selectedSRCDomCategory(),
            alias: self.SRCcurrentPDB(),
            mode: self.currentExtType(),
            threads: self.Threads(),
            beginmode: self.currentbeginmode(),
            trailtype: self.currentTrailType(),
            trailsubdir: self.trailSubDir(),
            trailsubdirslash: self.trailSubDirSlash(),
            trail: self.TrailName(),
            trailsize: self.trailSize(),
            currentExtParamList: self.newExtParamList(),
            startExtChk: self.startExtChk(),
            regExtChk: self.regExtChk(),
          }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: `Creating classic extract ${self.ExtName()}`,
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to create classic extract "${self.ExtName()}". ${msg}`,
              "Create Extract Error",
            );
          },
          success: function (data) {
            self.dialogTitle("Classic Extract " + self.ExtName());
            document.querySelector("#AddExtractDialog").open();
            self.AddExtractMsg(data[0]);
            return self;
          },
        });
      };

      self.extCancel = function () {
        document.querySelector("#AddExtract").close();
        document.querySelector("#Progress").close();
      };

      self.repCancel = function () {
        document.querySelector("#Progress").close();
        document.querySelector("#addReplicat").close();
      };

      self.ExtPrmList1 = ko.computed(function () {
        if (self.ExtPrmList()) {
          //console.log(self.ExtPrmList())
          return self.ExtPrmList().join("");
        } else {
          return "";
        }
      });
      self.ExtPrmListREP1 = ko.computed(function () {
        if (self.ExtPrmList()) {
          return self.ExtPrmListREP().join("");
        } else {
          return "";
        }
      });

      self.currentPmpOptParamList = ko.computed(function () {
        var currentPmpOptParamList = "";
        if (self.ExtoptParam()) {
          for (var i = 0; i < self.ExtoptParam().length; i++) {
            currentPmpOptParamList =
              currentPmpOptParamList + self.ExtoptParam()[i] + "\n";
          }
          return currentPmpOptParamList;
        } else {
          return "";
        }
      });

      self.currentPmpParam = ko.computed({
        read: function () {
          if (self.ExtName()) {
            var currentPmpParam =
              "EXTRACT " +
              self.PmpName() +
              "\n" +
              "RMTHOST " +
              self.rmtHostName() +
              ",PORT " +
              self.rmtMgrPort() +
              " " +
              "\n" +
              self.currentPmpOptParamList() +
              "\n" +
              "rmttrail" +
              "  " +
              self.rmttrailSubDir() +
              "/" +
              self.rmtTrailName() +
              "\n" +
              "REPORTCOUNT EVERY 5 MINUTES, RATE" +
              "\n" +
              self.currentSchemaParam() +
              "\n" +
              self.ExtSchemaParam() +
              "\n";
          } else {
            var currentPmpParam =
              "EXTRACT " +
              self.PmpName() +
              "\n" +
              "RMTHOST " +
              self.rmtHostName() +
              ",PORT " +
              self.rmtMgrPort() +
              " " +
              "\n" +
              self.currentPmpOptParamList() +
              "\n" +
              "rmttrail" +
              "  " +
              self.rmttrailSubDir() +
              "/" +
              self.rmtTrailName() +
              "\n" +
              "REPORTCOUNT EVERY 5 MINUTES, RATE" +
              "\n" +
              self.ExtPrmList1();
          }
          return currentPmpParam;
        },
      });

      self.addPumpPT = function (data, event) {
        self.AddExtractMsg([]);
        $.ajax({
          url: self.SRConepDepUrl() + "/api/v2/pump/add",
          type: "POST",
          data: JSON.stringify({
            extname: self.PmpName(),
            extdesc: self.PmpDesc(),
            mode: self.currentExtType(),
            srcTrail: self.SrcExtTrail(),
            beginmode: self.currentbeginmode(),
            trail: self.SrcRmtTrail(),
            trailsize: self.trailSize(),
            currentPmpParamList: self.newPmpParamList(),
            startPmpChk: self.startExtChk(),
          }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: `Creating network pump ${self.PmpName()}`,
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401){
              app.handleSessionExpired();
              return;
            };
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(
              `Unable to create network pump "${self.PmpName()}". ${msg}`,
              "Create Pump Error",
            );
          },
          success: function (data) {
            document.querySelector("#AddExtract").close();
            self.dialogTitle("Extract Pump " + self.ExtName());
            document.querySelector("#AddExtractDialog").open();
            self.AddExtractMsg(data[0]);
            return self;
          },
        });
      };
      self.currentRepOptParamList = ko.computed(function () {
        var currentRepOptParamList = "";
        if (self.RepoptParam()) {
          for (var i = 0; i < self.RepoptParam().length; i++) {
            //console.log(self.RepoptParam())
            currentRepOptParamList =
              currentRepOptParamList + self.RepoptParam()[i] + "\n";
          }
          ////console.log(currentRepOptParamList)
          return currentRepOptParamList;
        } else {
          return "";
        }
      });

      self.currentRepParam = ko.observable();

      self.newparamList = ko.observable("");

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
      });

      self.MongoRepSchemaParam = ko.computed({
        read: function () {
          var targetCollections = self.selectedTGTCollections();
          var sourceLines = self.ExtPrmListREP1();

          if (!targetCollections || targetCollections.length === 0) {
            // No collection chosen yet — keep original same-name TARGET
            return sourceLines;
          }

          var collection = targetCollections[0]; // using the first/only chosen collection

          // Replace only the TARGET portion of each MAP line with the chosen collection
          var lines = sourceLines.split("\n");
          var rebuilt = lines.map(function (line) {
            var trimmed = line.trim();
            if (!trimmed.startsWith("MAP ")) {
              return line; // leave non-MAP lines (SOURCECATALOG etc.) untouched
            }
            // e.g. "MAP MGUK.CUSTOMERS, TARGET MGUK.CUSTOMERS;"
            var match = trimmed.match(/^MAP\s+([^\s,]+)\s*,\s*TARGET\s+[^\s;]+;?/i);
            if (match) {
              var mapSide = match[1]; // e.g. "MGUK.CUSTOMERS"
              return "MAP " + mapSide + ", TARGET " + collection + ".*;";
            }
            return line;
          });

          return rebuilt.join("\n");
        },
      });

      self.currentRepParamList = ko.computed({
        read: function () {
          var currentRepParam = "";

          if (self.TgtonepDepType() == "mongodb") {
            currentRepParam =
              self.currentRepOptParamList() + "\n" +
              self.ExtPrmListREP1();
          } else if (self.ExtName() && !self.PmpName()) {
            var currentRepParam =
              "REPLICAT " +
              self.RepName() +
              "\n" +
              self.tgtLoginParam() +
              "\n" +
              "REPORTCOUNT EVERY 5 MINUTES, RATE" +
              "\n" +
              self.currentRepOptParamList() +
              "\n" +
              self.RepSchemaParam();
          } else if (self.ExtName() && self.PmpName()) {
            var currentRepParam =
              "REPLICAT " +
              self.RepName() +
              "\n" +
              self.tgtLoginParam() +
              "\n" +
              "REPORTCOUNT EVERY 5 MINUTES, RATE" +
              "\n" +
              self.currentRepOptParamList() +
              "\n" +
              self.RepSchemaParam();
          } else {
            var currentRepParam =
              "REPLICAT " +
              self.RepName() +
              "\n" +
              self.tgtLoginParam() +
              "\n" +
              "REPORTCOUNT EVERY 5 MINUTES, RATE" +
              "\n" +
              self.currentRepOptParamList() +
              "\n" +
              self.ExtPrmListREP1();
          }
          // //console.log(currentRepParam)
          return currentRepParam;
        },
      });

      self.AddReplicatMsg = ko.observableArray([]);

      self.addRep = function (data, event) {
        self.AddReplicatMsg([]);
        let url = "/api/v2/replicat/add"
        if(self.TgtonepDepType()== "mongodb"){
          url = "/api/v2/addMongoReplicat"
        }
        if(self.TgtonepDepType()== "sqlserver"){
          url = "/api/v2/addReplicat"
        }
        var ajaxOpts = {
          url: self.TGTonepDepUrl() + url,
          type: "POST",
          data: JSON.stringify({
            repname: self.RepName(),
            repdesc: self.RepDesc(),
            domain: self.selectedTGTDomCategory(),
            alias: self.TGTcurrentPDB(),
            repmode: self.currentRepType(),
            beginmode: self.currentbeginmode(),
            csnVal: self.csnVal(),
            trail: self.SrcRmtTrail(),
            chkpttbl: self.currentChkptTbl(),
            currentParamList: self.newRepParamList(),
            startRepChk: self.startRepChk(),
          }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: `Creating replicat ${self.RepName()}`,
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
              `Unable to create replicat "${self.RepName()}". ${msg}`,
              "Create Replicat Error",
            );
          },
          success: function (data) {
            console.log(data);
            
            self.ExtList([]);
            document.querySelector("#addReplicat").close();
            self.dialogTitle("Replicat " + self.RepName());
            document.querySelector("#AddReplicatDialog").open();

            var allMsgs;
            if (Array.isArray(data)) {   
              allMsgs = data[0] || [];
            } else {                     
              allMsgs = [data.message].concat(data.details || []);
            }
            self.AddReplicatMsg(allMsgs);
            return self;
          },
        };

        self.tgtAjax(ajaxOpts);
      };
      self.AddReplicatOKClose = function (event) {
        document.querySelector("#AddReplicatDialog").close();
        if (self.AddReplicatMsg().toString().includes("ERROR")) {
          self.router.go({ path: "addreplicat" });
        } else {
          self.router.go({ path: "manage" });
        }
      };

      self.args = args;
      // Create a child router with one default path
      self.router = self.args.parentRouter;

      self.AddExtractOKClose = function () {
        document.querySelector("#AddExtractDialog").close();
        if (self.AddExtractMsg().toString().includes("ERROR")) {
          self.router.go({ path: "Designer" });
        } else {
          self.router.go({ path: "manage" });
        }
      };

      self.cancel = function () {
        self.CancelBehaviorOpt("");
      };

      // Replicat Start

      self.chkTblList = ko.observableArray([]);
      self.currentChkptTbl = ko.observable();

      function queryChkTbl(data, event) {
        self.chkTblList([]);
        self.currentChkptTbl("");
        let url = "/api/v2/chkpt/info"
        console.log(self.TgtonepDepType());
        
        if (["mongodb", "sqlserver"].includes(self.TgtonepDepType())) {
          url = "/api/v2/infoCheckpointTable"
        }
        var ajaxOpts = {
          url: self.TGTonepDepUrl() + url,
          type: "POST",
          data: JSON.stringify({
            domain: self.selectedTGTDomCategory(),
            alias: self.TGTcurrentPDB(),
            operation: "View"
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
              if (["mongodb", "sqlserver", "postgresql"].includes(self.TgtonepDepType())) {
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

      self.chkpttblDP = new ArrayDataProvider(self.chkTblList, {
        keyAttributes: "value",
      });

      self.TGTschemaNameList = ko.observableArray([]);     

      self.fetchTgtCollections = function () {
        self.TGTschemaNameList([]);
        var ajaxOpts = {
          url: self.TGTonepDepUrl() + "/api/v2/suppLogSchema",
          type: "POST",
          data: JSON.stringify({ dbname: self.TGTcurrentPDB() }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          context: self,
          progressMessage: "Fetching target collections",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            if (textStatus === "abort") return;
            if (xhr.status === 401) { app.handleSessionExpired(); return; }
            var msg = app.extractErrorMessage(xhr);
            app.showGlobalError(`Unable to fetch target collections. ${msg}`, "Collection List Error");
          },
          success: function (data) {
            var names = (data[0] || [])
              .map(function (item) { return item.name; })
              .filter(Boolean);
            self.TGTschemaNameList(names.map(function (n) { return { label: n, value: n }; }));
            return self;
          }
        };

        self.tgtAjax(ajaxOpts);
      };

      self.TGTschemaNameListDP = new ArrayDataProvider(self.TGTschemaNameList, { keyAttributes: "value" });

      self.chkptTblName = ko.observable();
      self.AddChkptTblMsg = ko.observable();

      self.addsuppOKClose = function (event) {
        document.querySelector("#chkDlg").close();
      };

      self.openCkptTblDiaglog = function () {
        document.querySelector("#AddCkptTblDialog").open();
      };

      self.addChkptTbl = function (data, event) {
        self.AddChkptTblMsg("");
        document.querySelector("#AddCkptTblDialog").close();
        var ajaxOpts = {
            url: self.TGTonepDepUrl() + "/api/v2/chkpt/add",
            type: "POST",
            data: JSON.stringify({
                domain: self.selectedTGTDomCategory(),
                alias: self.TGTcurrentPDB(),
                chkpttbl: self.chkptTblName(),
                operation: "Add",
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
                document.querySelector("#ChkptTblDialog").open();
                self.AddChkptTblMsg(data[0]);
                return self;
            },
        };

        self.tgtAjax(ajaxOpts);
      };
      self.AddChkptTblMsgOKClose = function (event) {
        document.querySelector("#ChkptTblDialog").close();
        queryChkTbl();
      };

      //enf

      self.connected = function () {
        if (sessionStorage.getItem("userName") == null) {
          self.router.go({ path: "signin" });
        } else {
          app.onAppSuccess();
          self.ExtName("");
          self.PmpName("");
          self.toggleOuter();
          self.startExtChk(false);
          self.startRepChk(false);
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
  return DesignerViewModel;
});
