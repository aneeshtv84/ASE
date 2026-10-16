define([
  "ojs/ojcore",
  "knockout",
  "jquery",
  "appController",
  "ojs/ojconverter-number",
  "ojDiagram/viewModels/ggLayout",
  "ojs/ojknockout-keyset",
  "ojs/ojattributegrouphandler",
  "ojs/ojarraydataprovider",
  "ojs/ojarraytreedataprovider",
  "ojs/ojknockout",
  "ojs/ojdiagram",
  "ojs/ojdialog",
  "ojs/ojprogress-bar",
], function (
  oj,
  ko,
  $,
  app,
  NumberConverter,
  layout,
  keySet,
  attributeGroupHandler,
  ArrayDataProvider,
  ArrayTreeDataProvider,
) {
  class DataFlowViewModel {
    constructor(context) {
      var self = this;
      self.DepName = context.routerState.detail.dep_url;
      self.ExtName = ko.observable();

      self.RepName = ko.observable();

      self.args = context;
      self.router = self.args.parentRouter;

      self.ExtData1 = ko.observableArray([]);
      self.RepData1 = ko.observableArray([]);

      self.NodeData = ko.observableArray([]);
      self.LinkData = ko.observableArray([]);

      self.NodeExt = ko.observableArray([]);
      self.NodePmp = ko.observableArray([]);
      self.NodeRep = ko.observableArray([]);

      self.styleExt = ko.observable();
      self.styleRep = ko.observable();
      self.ExtATCSN = ko.observable();
      self.ExtAFTERCSN = ko.observable();

      self.RepATCSN = ko.observable();
      self.RepAFTERCSN = ko.observable();
      self.decimalHalfDownConverter = new NumberConverter.IntlNumberConverter({
        style: "decimal",
        roundingMode: "HALF_DOWN",
        maximumFractionDigits: 0,
        useGrouping: false,
      });

      self.onepDepList = ko.observableArray([]);
      self.loading = ko.observable(false);
      self.loadInfo = ko.observable("");
      self.hasNodes = ko.observable(false);

      // ─────────────────────────────────────────────────────────────
      // Data collected from ALL deployments, drawn once at the end
      // ─────────────────────────────────────────────────────────────
      var col = { ext: {}, pmp: {}, rep: {}, links: {} };
      var trailOf = { ext: {}, pmp: {}, pmpRmt: {}, rep: {} }; // nodeId -> normalised trail

      var TOKEN_TYPES = ["mongodb", "sqlserver"]; // same list as the Designer page

      function prettyDbType(t) {
        var map = {
          oracle: "Oracle", sqlserver: "SQL Server", mssql: "SQL Server", "sql server": "SQL Server",
          postgresql: "PostgreSQL", sybase: "Sybase", mongodb: "MongoDB", mysql: "MySQL",
        };
        return map[String(t || "").toLowerCase()] || t || "";
      }
      // "REWERAA MSSQL" -> "REWERAA"
      function procName(name) { return String(name || "").trim().split(/\s+/)[0]; }
      function nodeId(dep, name) { return dep + ":" + procName(name); }

      function addNode(kind, dep, name, dbtype) {
        var id = nodeId(dep, name);
        if (!col[kind][id]) {
          var t = prettyDbType(dbtype);
          col[kind][id] = { id: id, label: "[" + dep + (t ? " · " + t : "") + "] " + procName(name) };
        }
        return id;
      }
      function addLink(start, end, category, key) {
        if (!start || !end || start === end) return;
        var id = key || start + "->" + end;
        if (!col.links[id]) col.links[id] = { id: id, start: start, end: end, category: category || "" };
      }
      // "/cdc_data/TRAILS/JBEX/ZZ000000001" -> "JBEX/ZZ"
      function normTrail(t) {
        var s = String(t || "").trim().replace(/\\/g, "/").replace(/\d{6,9}$/, "");
        return s.split("/").filter(Boolean).slice(-2).join("/").toUpperCase();
      }
      // extract on one deployment -> replicat on another reading the same trail
      function trailMatch(a, b) {
        if (!a || !b) return false;
        var x = a.split("/"), y = b.split("/");
        if (x[x.length - 1] !== y[y.length - 1]) return false;
        if (x.length < 2 || y.length < 2) return true;
        return x[x.length - 2] === y[y.length - 2];
      }
      function sameDep(a, b) { return a.split(":")[0] === b.split(":")[0]; }
      function addCrossLinks() {
        // Extract -> Pump / Distribution Path (same deployment)
        Object.keys(trailOf.ext).forEach(function (e) {
          Object.keys(trailOf.pmp).forEach(function (p) {
            if (sameDep(e, p) && trailMatch(trailOf.ext[e], trailOf.pmp[p])) addLink(e, p, trailOf.ext[e]);
          });
        });
        // Pump / Distribution Path -> Replicat (ANY deployment)
        Object.keys(trailOf.pmpRmt).forEach(function (p) {
          Object.keys(trailOf.rep).forEach(function (r) {
            if (trailMatch(trailOf.pmpRmt[p], trailOf.rep[r])) addLink(p, r, trailOf.pmpRmt[p]);
          });
        });
        // Extract -> Replicat on another deployment (no pump)
        Object.keys(trailOf.ext).forEach(function (e) {
          Object.keys(trailOf.rep).forEach(function (r) {
            if (!sameDep(e, r) && trailOf.ext[e].indexOf("/") > 0 && trailOf.ext[e] === trailOf.rep[r]) addLink(e, r, trailOf.ext[e]);
          });
        });
      }
      function renderDiagram() {
        var known = {};
        ["ext", "pmp", "rep"].forEach(function (k) {
          Object.keys(col[k]).forEach(function (id) { known[id] = true; });
        });
        self.NodeData([
          { id: "Extracts", label: "Extracts", nodes: Object.values(col.ext) },
          { id: "Distribution", label: "Distribution", nodes: Object.values(col.pmp) },
          { id: "Replicats", label: "Replicats", nodes: Object.values(col.rep) },
        ]);
        // only links whose both ends exist, otherwise the diagram throws
        self.LinkData(Object.values(col.links).filter(function (l) { return known[l.start] && known[l.end]; }));
        self.hasNodes(Object.keys(known).length > 0);
      }

      // each deployment type has its own diagram route
      function diagramRoute(dbtype) {
        var t = String(dbtype || "").toLowerCase().replace(/\s+/g, "");
        if (t === "sqlserver" || t === "mssql" || t === "mongodb" || t === "postgresql") return "/api/v2/gginfodiagram";
        return "/api/v2/diagram/info"; // sybase / classic
      }

      // ─────────────────────────────────────────────────────────────
      // Deployment list -> load each deployment one after the other
      // ─────────────────────────────────────────────────────────────
      function getOnepDep() {
        col = { ext: {}, pmp: {}, rep: {}, links: {} };
        trailOf = { ext: {}, pmp: {}, pmpRmt: {}, rep: {} };
        self.onepDepList([]);
        self.NodeData([]);
        self.LinkData([]);
        self.hasNodes(false);
        self.loading(true);
        self.loadInfo("Loading deployments...");
        $.ajax({
          url: self.DepName() + "/api/v2/onep/dep",
          type: "GET",
          dataType: "json",
          contentType: "application/json",
          context: self,
          progressMessage: "Fetching deployment list",
          suppressGlobalError: true,
          error: function (xhr, textStatus) {
            self.loading(false);
            if (textStatus === "abort" || xhr.statusText === "abort") return;
            if (xhr.status === 401) { app.handleSessionExpired(); return; }
            if (xhr.status == 0) {
              app.showGlobalError(app.deploymentUnreachableMessage(), "Connection Error");
              return;
            }
            app.showGlobalError(`Unable to fetch deployment list. ${app.extractErrorMessage(xhr)}`,
                                "Deployment List Error");
          },
          success: function (data) {
            var deployments = (data && data[0]) || [];
            deployments.forEach(function (d) { self.onepDepList.push({ dep: d.dep, dep_url: d.dep_url }); });
            runSequentially(deployments, 0);
          },
        });
      }

      function runSequentially(list, i) {
        if (i >= list.length) {
          addCrossLinks();
          renderDiagram();
          self.loading(false);
          self.loadInfo("");
          return;
        }
        self.loadInfo("Loading " + list[i].dep + " (" + (i + 1) + " of " + list.length + ")...");
        getReplionFlow(list[i].dep, list[i].dep_url, function () { runSequentially(list, i + 1); });
      }

      // Same as Designer: /onep/depurl -> [url, trailPath, dbtype, token]
      function depInfo(dep, callback) {
        $.ajax({
          url: self.DepName() + "/api/v2/onep/depurl",
          type: "POST",
          data: JSON.stringify({ dep: dep }),
          dataType: "json",
          contentType: "application/json",
          timeout: sessionStorage.getItem("timeInetrval"),
          showProgress: false,
          suppressGlobalError: true,
          error: function () { callback(null); },
          success: function (data) {
            var key = "Tgt_" + dep + "_AccessToken";
            if (data && data[3]) sessionStorage.setItem(key, data[3]);
            callback({ url: data && data[0], dbtype: String((data && data[2]) || "").toLowerCase() });
          },
        });
      }

      // Same as Designer: /onep/deptoken -> fresh token
      function fetchDepToken(dep, callback) {
        $.ajax({
          url: self.DepName() + "/api/v2/onep/deptoken",
          type: "POST",
          data: JSON.stringify({ dep: dep }),
          dataType: "json",
          contentType: "application/json",
          showProgress: false,
          suppressGlobalError: true,
          skipSessionExpired: true,
          error: function () { callback(false); },
          success: function (data) {
            sessionStorage.setItem("Tgt_" + dep + "_AccessToken", data.access_token);
            sessionStorage.setItem("Tgt_" + dep + "_DbType", data.dbtype);
            callback(true);
          },
        });
      }

      // Diagram data of ONE deployment (Sybase: own route, SQL Server: token + gginfodiagram)
      function getReplionFlow(dep, dep_url, onDone) {
        var done = false;
        function finish() { if (!done) { done = true; onDone(); } }

        depInfo(dep, function (info) {
          if (!info || !info.url) {
            app.showGlobalError(`Unable to resolve deployment "${dep}".`, "Deployment Error");
            finish();
            return;
          }
          var dbtype = info.dbtype;
          var useToken = TOKEN_TYPES.indexOf(dbtype) !== -1;
          var retried = false;

          function authHeader() {
            if (!useToken) return undefined;
            var t = sessionStorage.getItem("Tgt_" + dep + "_AccessToken");
            return t ? { Authorization: "Bearer " + t } : undefined;
          }

          var opts = {
            url: (info.url || dep_url) + diagramRoute(dbtype),
            type: "GET",
            dataType: "json",
            timeout: 60000,
            showProgress: false,
            suppressGlobalError: true,
            skipSessionExpired: useToken, // a remote 401 must not log the user out
            headers: authHeader(),
            error: function (xhr, textStatus) {
              if (textStatus === "abort") { finish(); return; }
              if (xhr.status === 401 && useToken && !retried) {
                retried = true; // token expired -> refresh once and retry
                fetchDepToken(dep, function (ok) {
                  if (ok) { opts.headers = authHeader(); $.ajax(opts); }
                  else {
                    app.showGlobalError(`Deployment "${dep}" rejected the login. Check its user/password in Remote Deployment.`,
                                        "Dataflow Error");
                    finish();
                  }
                });
                return;
              }
              if (textStatus === "timeout" || xhr.status === 0) {
                app.showGlobalError(`Could not reach deployment "${dep}". It has been skipped.`, "Deployment Unreachable");
              } else {
                app.showGlobalError(app.extractErrorMessage(xhr), `Dataflow Error — ${dep}`);
              }
              finish();
            },
            success: function (data) {
              if (Array.isArray(data) && data[0]) {
                var sets = data[0];
                Object.keys(sets.nodeext || {}).forEach(function (n) {
                  var id = addNode("ext", dep, n, dbtype);
                  trailOf.ext[id] = normTrail(sets.nodeext[n]);
                });
                var pmpRmt = sets.nodepmprmt || {}; // pump -> remote trail
                Object.keys(sets.nodepmp || {}).forEach(function (n) {
                  var id = addNode("pmp", dep, n, dbtype);
                  trailOf.pmp[id] = normTrail(sets.nodepmp[n]);
                  trailOf.pmpRmt[id] = normTrail(pmpRmt[n]);
                });
                Object.keys(sets.noderep || {}).forEach(function (n) {
                  var id = addNode("rep", dep, n, dbtype);
                  trailOf.rep[id] = normTrail(sets.noderep[n]);
                });
                (data[1] || []).forEach(function (l, i) {
                  addLink(nodeId(dep, l.start), nodeId(dep, l.end), l.category);
                });
              }
              finish();
            },
          };
          $.ajax(opts);
        });
      }

      self.nodeDataProvider = new ArrayTreeDataProvider(self.NodeData, {
        keyAttributes: "id",
        childrenAttribute: "nodes",
      });
      self.linkDataProvider = new ArrayDataProvider(self.LinkData, {
        keyAttributes: "id",
      });
      var color =
        new attributeGroupHandler.ColorAttributeGroupHandler().getValue(0);
      self.expandedNodes = new keySet.ObservableKeySet().add([
        "Extracts",
        "Distribution",
        "Replicats",
      ]);
      self.layoutFunc = layout.containerLayout;

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
            var w = childContent.w + 90,
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
              25,
              15,
              250,
              45,
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

      self.selectedNodesValue = ko.observable();
      self.selectionValue = ko.observable("single");

      // Below are a set of the ViewModel methods invoked by the oj-module component.
      // Please reference the oj-module jsDoc for additional information.

      /**
       * Optional ViewModel method invoked after the View is inserted into the
       * document DOM.  The application can put logic that requires the DOM being
       * attached here.
       * This method might be called multiple times - after the View is created
       * and inserted into the DOM and after the View is reconnected
       * after being disconnected.
       */
      self.connected = function () {
        if (sessionStorage.getItem("userName") == null) {
          self.router.go({ path: "signin" });
        } else {
          app.onAppSuccess();
          app.depCtxCache = {};
          getOnepDep();
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
  return DataFlowViewModel;
});