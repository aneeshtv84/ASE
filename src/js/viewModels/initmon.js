define(['ojs/ojcore', 'knockout', 'jquery', 'appController', 'ojDiagram/viewModels/ggLayout', 'ojs/ojknockout-keyset',
'ojs/ojattributegrouphandler', 'ojs/ojconverter-number', 'ojs/ojconverterutils-i18n', 'ojs/ojconverter-datetime',
'ojs/ojarraydataprovider', 'ojs/ojarraytreedataprovider', 'ojs/ojinputnumber', 'ojs/ojdatetimepicker', 'ojs/ojinputtext', 'ojs/ojformlayout',
'ojs/ojknockout', 'ojs/ojactioncard', 'ojs/ojdiagram', 'ojs/ojdialog', 'ojs/ojprogress-bar', 'ojs/ojselectcombobox', 'ojs/ojtable',
'ojs/ojselectsingle', 'ojs/ojradioset', "ojs/ojinputsearch"],
function (oj, ko, $, app, layout, keySet, attributeGroupHandler, NumberConverter, ConverterUtilsI18n, DateTimeConverter,ArrayDataProvider, ArrayTreeDataProvider) {

  class InitManageViewModel {
    constructor(args) {
      //console.log(args)
      var self = this;
      self.DepName = args.routerState.detail.dep_url;

      self.NodeData = ko.observableArray([]);
      self.LinkData = ko.observableArray([]);
      self.ExtData = ko.observableArray([]);
      self.RepData = ko.observableArray([]);
      self.ExpandedNodes = ko.observableArray([]);
      self.CancelBehaviorOpt = ko.observable('icon');
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
      let interval = 30000 ;

      function getILData() {
        $.ajax({
          url: self.DepName() + '/ggildataset',
          type: 'GET',
          dataType: 'json',
          timeout: sessionStorage.getItem("timeInetrval"),
          error: function (xhr, textStatus, errorThrown) {
            if (textStatus == 'timeout' || textStatus == 'error') {
              document.querySelector('#TimeoutMon').open();
            }
          },
          success: function (data) {
            self.ILJobData([]);
            for (var i = 0; i < data[0].length; i++) {
              self.ILJobData.push({ 'label': data[0][i].jobname , 'value' :  data[0][i].jobname});
            }
            //console.log(self.ILJobData())
            return self;
          }
        })
      }

  self.getNodeFlow =    function (event,data) {
        $.ajax({
          url: self.DepName() + '/ggilprocesses',
          type: 'POST',
          data: JSON.stringify({
            JobName : self.currentILJOb()
        }),
          dataType: 'json',
          timeout: sessionStorage.getItem("timeInetrval"),
          error: function (xhr, textStatus, errorThrown) {
            if (textStatus == 'timeout' || textStatus == 'error') {
              document.querySelector('#TimeoutMon').open();
            }
          },
          success: function (data) {
            self.NodeExt([]);
            self.NodeRep([]);
            for (var key in data[3]) {
              for (var i = 0; i < data[3][key].length; i++) {
                if (data[3][key][i].type == 'Ext') {
                  self.NodeExt.push({ 'id': data[3][key][i].procname + ' ' + key, 'url': data[3][key][i].dep_url, 'type': data[3][key][i].type });
                }
                if (data[3][key][i].type == 'Rep') {
                  self.NodeRep.push({ 'id': data[3][key][i].procname + ' ' + key, 'url': data[3][key][i].dep_url, 'type': data[3][key][i].type });
                }
              }
            }
            self.NodeData([]);
            self.NodeData.push({ 'id': 'Extracts', 'nodes': self.NodeExt() }, { 'id': 'Replicats', 'nodes': self.NodeRep() })

            self.expandedNodes.add(['Extracts', 'Replicats'])
            self.LinkData([]);
            for (var i = 0; i < data[0].length; i++) {
              self.LinkData.push({ 'start': data[0][i].extname + ' ' + data[0][i].dep_src, 'trail': data[0][i].trail, 'end': data[0][i].repname + ' ' + data[0][i].dep_tgt, 'id': i });
            }

            self.ExtData([]);
            self.RepData([]);
            for (var i = 0; i < data[1].length; i++) {
              if (data[1][i].extstat == 'STOPPED') {
                self.ExtData.push({ 'ExtName': data[1][i].extname, 'ExtStat': data[1][i].extstat, styleExt: { "background-color": "Chocolate" } });
              }
              else if (data[1][i].extstat == 'RUNNING' || data[1][i].extstat == 'STARTING') {
                self.ExtData.push({ 'ExtName': data[1][i].extname, 'ExtStat': data[1][i].extstat, styleExt: { "background-color": "ForestGreen" } });
              }
              else if (data[1][i].extstat == 'ABENDED') {
                self.ExtData.push({ 'ExtName': data[1][i].extname, 'ExtStat': data[1][i].extstat, styleExt: { "background-color": "IndianRed" } });
              }
            }
              for (var i = 0; i < data[4].length; i++) {
              if (data[4][i].repstat == 'STOPPED') {
                self.RepData.push({ 'RepName': data[4][i].repname, 'RepStat': data[4][i].repstat, styleExt: { "background-color": "Chocolate" } });
              }
              else if (data[4][i].repstat == 'RUNNING' || data[4][i].repstat == 'STARTING') {
                self.RepData.push({ 'RepName': data[4][i].repname, 'RepStat': data[4][i].repstat, styleExt: { "background-color": "ForestGreen" } });
              }
              else if (data[4][i].repstat == 'ABENDED') {
                self.RepData.push({ 'RepName': data[4][i].repname, 'RepStat': data[4][i].repstat, styleExt: { "background-color": "IndianRed" } });
              }
            }
            self.ExtData.valueHasMutated();
            self.RepData.valueHasMutated();
            ILSetTimer();
            return self;
          }
        })
      }

var intervalVar;

function ILSetTimer(){
if (self.ILException()=='error'){
  clearInterval(intervalVar);
  interval = interval + 60000
  intervalVar = setInterval(getILFlow,interval);
  //console.log(intervalVar)
}
else{
  intervalVar = setInterval(getILFlow,interval);
}

}

self.getILTables =    function (event,data)  {
  //console.log(self.currentILJOb())
  if (self.currentILJOb()){
      $.ajax({
        url: self.DepName() + '/ggiltables',
        type: 'POST',
        data: JSON.stringify({
          JobName : self.currentILJOb()
      }),
        timeout: 120000,
        error: function (xhr, textStatus, errorThrown) {
          print(textStatus)
          if (textStatus == 'timeout' || textStatus == 'error') {
            self.ILException(textStatus);
            ILSetTimer();
            document.querySelector('#TimeoutMon').open();
          }
        },
        success: function (data) {
          console.log(data[0])
          self.ILTables([]);
          for (var key in data[0]) {
           self.ILTables.push({ 'TABLE_NAME': key, 'TARGET_ROWS': data[0][key].TargetRows , 'PROCESS_NAME' : data[0][key].Process })
          }
          self.ILStats([]);
          for (var key in data[0]) {
            self.ILStats.push({ 'TABLE_NAME': key, 'TARGET_ROWS': data[0][key].TargetRows , 'PROCESS_NAME' : data[0][key].Process  })
           }
          console.log(self.ILStats);
          self.getNodeFlow();
          return self;
        }
      })
    }
  }

function getILFlow() {
    if (self.currentILJOb()){
      self.ILException('');
        $.ajax({
          url: self.DepName() + '/ggilprocesses',
          type: 'POST',
          data: JSON.stringify({
            JobName : self.currentILJOb(),
            tabList : self.ILTables()
        }),
          timeout: 120000,
          error: function (xhr, textStatus, errorThrown) {
            if (textStatus == 'timeout' || textStatus == 'error') {
              self.ILException(textStatus);
              ILSetTimer();
              document.querySelector('#TimeoutMon').open();
            }
          },
          success: function (data) {
            
            self.ExtData([]);
            self.RepData([]);
            for (var i = 0; i < data[1].length; i++) {
              if (data[1][i].extstat == 'STOPPED') {
                self.ExtData.push({ 'ExtName': data[1][i].extname, 'ExtStat': data[1][i].extstat, styleExt: { "background-color": "Chocolate" } });
              }
              else if (data[1][i].extstat == 'RUNNING' || data[1][i].extstat == 'STARTING') {
                self.ExtData.push({ 'ExtName': data[1][i].extname, 'ExtStat': data[1][i].extstat, styleExt: { "background-color": "ForestGreen" } });
              }
              else if (data[1][i].extstat == 'ABENDED') {
                self.ExtData.push({ 'ExtName': data[1][i].extname, 'ExtStat': data[1][i].extstat, styleExt: { "background-color": "IndianRed" } });
              }
            }
              for (var i = 0; i < data[4].length; i++) {
              if (data[4][i].repstat == 'STOPPED') {
                self.RepData.push({ 'RepName': data[4][i].repname, 'RepStat': data[4][i].repstat, styleExt: { "background-color": "Chocolate" } });
              }
              else if (data[4][i].repstat == 'RUNNING' || data[4][i].repstat == 'STARTING') {
                self.RepData.push({ 'RepName': data[4][i].repname, 'RepStat': data[4][i].repstat, styleExt: { "background-color": "ForestGreen" } });
              }
              else if (data[4][i].repstat == 'ABENDED') {
                self.RepData.push({ 'RepName': data[4][i].repname, 'RepStat': data[4][i].repstat, styleExt: { "background-color": "IndianRed" } });
              }
            }
            self.ExtData.valueHasMutated();
            self.RepData.valueHasMutated();
            self.ILStats([]);
            for (var key in data[2]) {
             self.ILStats.push({'TABLE_NAME' : key,'TARGET_ROWS' : data[2][key].TargetRows,'PROCESS_NAME' : data[2][key].Process ,'EXTCOUNT': data[2][key].TotalEXT, 'EXTDSC': data[2][key].TotalEXTDSC ,'EXTRATE' : data[2][key].ExtRate , 'REPCOUNT': data[2][key].TotalREP, 'REPDSC': data[2][key].TotalREPDSC ,'REPRATE' : data[2][key].RepRate , 'REPELA' : timeConversion(data[2][key].RepElapse),'REPETA' : timeConversion(data[2][key].RepETA), 'Stat' : data[2][key].Status })
            }
            console.log(self.ILStats())
            self.ILStats.valueHasMutated();
            self.ILException(data[5]);
            if (self.ILException()=='error'){
               ILSetTimer();
              }
              //console.log(data[2])
            //console.log(interval)
            return self;
          }
        })
      }
      }

      function timeConversion(d){
        var h = Math.floor(d / 3600);
    var m = Math.floor(d % 3600 / 60);
    var s = Math.floor(d % 3600 % 60);

    var hDisplay = h > 0 ? h + (h == 1 ? "h" : "h") : "";
    var mDisplay = m > 0 ? m + (m == 1 ? "m" : "m") : "";
    var sDisplay = s > 0 ? s + (s == 1 ? "s" : "s") : "";
    let elpseTime = hDisplay + mDisplay + sDisplay; 
    return elpseTime;
      }


      self.ExtDataDP = ko.observable(new ArrayDataProvider(self.ExtData, { keyAttributes: 'ExtName' }));
      self.RepDataDP = ko.observable(new ArrayDataProvider(self.RepData, { keyAttributes: 'RepName' }));
      self.ILStatsDP = ko.observable(new ArrayDataProvider(self.ILStats, { keyAttributes: 'TABLE_NAME' }));
      self.nodeDataProvider = ko.observable(new ArrayTreeDataProvider(self.NodeData, { keyAttributes: 'id', childrenAttribute: "nodes" }));
      self.linkDataProvider = ko.observable(new ArrayDataProvider(self.LinkData, { keyAttributes: 'id' }));
      self.ILjobDataProvider = ko.observable(new ArrayDataProvider(self.ILJobData, { keyAttributes: 'id' }));
      var color = (new attributeGroupHandler.ColorAttributeGroupHandler()).getValue(0);
      self.layoutFunc = layout.containerLayout;

      self.ILStatscolumnArray = [
        {
          headerText: 'Process',
          field: 'PROCESS_NAME'
        },
        {
          headerText: 'Schema.Table Name',
          field: 'TABLE_NAME'
        },
        {
          headerText: 'Target Rows',
          field: 'TARGET_ROWS'
        },
        {
          headerText: 'Extracting Count',
          field: 'EXTCOUNT'
        },
        {
          headerText: 'Extract Discard Count',
          field: 'EXTDSC'
        },
        {
          headerText: 'Extract Rate/sec',
          field: 'EXTRATE'
        },
        {
          headerText: 'Replicating Count',
          field: 'REPCOUNT'
        },
        {
          headerText: 'Replicat Discard Count',
          field: 'REPDSC'
        },
        {
          headerText: 'Replicat Rate/sec',
          field: 'REPRATE'
        },
        {
          headerText: 'Total Elapsed Time',
          field: 'REPELA'
        },
        {
          headerText: 'ETA',
          field: 'REPETA'
        },
        {
          headerText: 'Status',
          field: 'Stat'
        },]

      this.linkRendererFunc = function (context) {
        var rootElement = context.rootElement;

        var width = context.state.hovered || context.state.selected ?
          2 : 1;
        if (!rootElement) {
          var linkid = context.type === 'promotedLink' ?
            context.id.name + context.id.startId + context.id.endId : context.id;
          var rootElement = createGroup('linkSvg' + linkid);
          addPath(rootElement, 10, context.state.selected, 'underlay', context.points);
          addPath(rootElement, width, context.state.selected, context.type);
        } else {
          var visiblePath = rootElement.children[1];
          visiblePath.setAttribute("stroke-width", width);
          visiblePath.classList.toggle("demo-diagram-selected-link", context.state.selected);
        }
        return { "insert": rootElement };
      };

      self.getStyleUrl = (styleId) => {
        return "url(" + document.URL + "#" + styleId + ")";
      };
      this.nodeRendererFunc = function (context) {
        var color = context.state.selected ? 'red' : '#87ceeb';   //header color 
        var stroke = context.state.selected || context.state.hovered ? 4 : 3;
        var rootElement = context.rootElement;
        if (!rootElement) {
          // initial rendering - create an svg element with a node content in it
          var nodeId = context.data['id'];
          if (context.state.expanded) {
            //render expanded node
            var childContent = context.content;
            // add 20 px for the each side padding and 
            // additional 20 px on top for the header
            var w = childContent.w + 60,
              h = childContent.h + 100;
            rootElement = createSVG('nodeSvg' + nodeId, w, h);
            var group = addGroup(rootElement, 'topGroup' + nodeId);
            w -= 2, h -= 2; //reduce width and height for inner elements
            addRect(group, 'rect' + nodeId, 1, 1, w, h, "white");
            addRect(group, 'rectHdr' + nodeId, 1, 1, w, 25, color); //header size 
            addChildContent(group, childContent.element);
          }
          else {
            //render collapsed or leaf node
            rootElement = createSVG('nodeSvg' + nodeId, 1000, 1000);  //size of the main container
            var group = addGroup(rootElement, 'topGroup' + nodeId);
            addRect(group, 'rectInner' + nodeId, 15, 10, 200, 25, self.getStyleUrl("gradient1")); //position of the child containers inside main
          }
        }
        else {// modification case - apply custom treatment to the node
          var group = rootElement.childNodes[0];
          var outerRect = group.childNodes[0];
          outerRect.setAttributeNS(null, "stroke", color);
          outerRect.setAttributeNS(null, "stroke-width", stroke);
          if (context.state.expanded) {
            //change header color for the container node
            var hdrRect = group.childNodes[1];
            hdrRect.setAttributeNS(null, "stroke", 'color');
            hdrRect.setAttributeNS(null, "stroke", color);
          }
        }
        return { "insert": rootElement };
      };
      // SVG helper functions for node rendering
      function createSVG(id, width, height) {
        var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttributeNS(null, 'width', width);
        svg.setAttributeNS(null, 'height', height);
        svg.setAttributeNS(null, 'viewBox', "0 0 " + width + " " + height);
        return svg;
      };
      function addGroup(parent, id) {
        var group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.setAttributeNS(null, 'id', id);
        parent.appendChild(group);
        return group;
      };
      function addRect(parent, id, x, y, w, h, fill) {
        var svgRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
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
      };
      function addChildContent(parent, elem) {
        parent.appendChild(elem);
        elem.setAttributeNS(null, "transform", "translate(10 30)");
      };

      // SVG helper functions for link rendering
      function createGroup(id) {
        var group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.setAttribute('id', id);
        return group;
      };
      function addPath(parent, width, selected, type, points) {
        var svgPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        var linkSvgClasses = type === 'underlay' ?
          'demo-diagram-link-underlay' : "demo-diagram-link oj-diagram-link-path demo-diagram-promoted-link";
        if (type === 'underlay') {
          svgPath.setAttribute("d", points.join(' '));
        }
        else {
          if (type === 'promotedLink')
            linkSvgClasses += ' demo-diagram-promoted-link';
          if (selected)
            linkSvgClasses += ' demo-diagram-selected-link';
        }
        svgPath.setAttribute("stroke-width", width);
        svgPath.setAttribute("class", linkSvgClasses);
        parent.appendChild(svgPath);
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
      self.selectedAliascategory = ko.observable();
      self.selectedUsercategory = ko.observable();
      self.aliascategories = ko.observableArray([]);
      self.unamecategories = ko.observable();
      self.selectedDomCategory = ko.observable();




      let getAliascategories = (category) => {
        let found = self.aliasname1().find(c => c.value === category);
        return found ? found.children : null;
      };
      let getUnamecategories = (category) => {
        let found = self.username1().find(c => c.value === category);
        return found ? found.children : null;
      };
      this.domSelectionChanged = (event) => {
        self.selectedAliascategory('');
        let children = getAliascategories(event.detail.value);
        self.aliascategories(children);
      };


      self.aliasSelectionChanged = (event) => {
        self.selectedUsercategory('');
        let children = getUnamecategories(event.detail.value);
        self.unamecategories(children);
      };


      self.isFormReadonly = ko.observable(false);
      self.isRequired = ko.observable(true);
      self.checkboxValues = ko.observableArray(['required', 'helpSource', 'helpDef']);

      self.isRequired = ko.computed(function () {
        return self.checkboxValues.indexOf('required') !== -1;
      });
      self.helpDef = ko.computed(function () {
        return (self.checkboxValues.indexOf('helpDef') !== -1) ? self._HELP_DEF : null;
      });
      this.helpSource = ko.computed(function () {
        return (self.checkboxValues.indexOf('helpSource') !== -1) ? self._HELP_SOURCE : null;
      });



      self.currentbeginmode = ko.observable('Now');

      self.beginmode = ko.observableArray([
        { value: 'Now', label: 'Begin Now' },
        { value: 'Time', label: 'Custom Time' },
        { value: 'LOC', label: 'Location' }
      ]);

      self.startOptionDP = new ArrayDataProvider(self.beginmode, { keyAttributes: 'value' });

      self.secondConverter = new DateTimeConverter.IntlDateTimeConverter(
        {
          pattern: "yyyy-MM-dd HH:mm:ss"
        });

      self.ctvalue = ko.observable(ConverterUtilsI18n.IntlConverterUtils.dateToLocalIso(new Date()));

      self.seqnovalue = ko.observable();
      self.rbavalue = ko.observable();

      self.decimalHalfDownConverter =
        new NumberConverter.IntlNumberConverter({
          style: 'decimal',
          roundingMode: 'HALF_DOWN',
          maximumFractionDigits: 0,
          useGrouping: false
        });


      function getDomains() {
        self.username1([]);
        self.othdom([]);
        self.aliasname1([]);
        self.domname1([]);
        self.selectedDomCategory('');
        self.selectedAliascategory('');
        self.selectedUsercategory('');
        $.ajax({
          url: self.selDepname() + "/ggcredstore",
          type: 'GET',
          timeout: 10000,
          error: function (xhr, textStatus, errorThrown) {
            if (textStatus == 'timeout' || textStatus == 'error') {
              document.querySelector('#TimeoutMon').open();
            }
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
              self.username1.push({ label: data[0][i].alias, value: data[0][i].alias, 'children': [{ label: data[0][i].uname, value: data[0][i].uname }] });
            }
            //console.log(self)

            return self;
          }
        })
      }



      self.selectedNodesValue = ko.observable();
      self.selectionValue = ko.observable("single");

      self.ExtRpt = ko.observableArray([]);
      self.selectedMenuItem = ko.observable('');

      self.selDepname = ko.observable();
      self.selProcType = ko.observable();
      self.onePDepname = ko.observable();
      self.dialogTitle = ko.observable();

      self.popUpResize = (value) => {
        document.getElementById(value).style.width = "1150px";
        document.getElementById(value).style.height = "100vh";
      }

      self.popUpResizeSM = (value) => {
        document.getElementById(value).style.width = "500px";
        document.getElementById(value).style.height = "45vh";
      }


      self.menuItemAction = function (event) {
        self.selectedMenuItem(event.target.value);
        self.selDepname('');
        self.selProcType('');
        self.onePDepname('');
        for (var i = 0; i < self.NodeData().length; i++) {
          for (var j = 0; j < self.NodeData()[i].nodes.length; j++) {
            if (self.NodeData()[i].nodes[j].id == self.selectedNodesValue()[0]) {
              //console.log(self.NodeData()[i].nodes[j].url)
              self.selDepname(self.NodeData()[i].nodes[j].url);
              self.onePDepname(self.NodeData()[i].id);
              self.selProcType(self.NodeData()[i].nodes[j].type);
            }
          }
        }

        console.log(self.selectedNodesValue()[0].split(' ')[0])
        console.log(self.selProcType())
        console.log(self.selectedMenuItem())
        if (self.selProcType() == 'Ext') {
          self.dialogTitle('View Extract ' + self.selectedNodesValue()[0].split(' ')[0] + ' Info');
          if (self.selectedMenuItem() == 'rpt' || self.selectedMenuItem() == 'chk' || self.selectedMenuItem() == 'stats' || self.selectedMenuItem() == 'startdef' || self.selectedMenuItem() == 'stop' || self.selectedMenuItem() == 'forcestop' || self.selectedMenuItem() == 'kill' || self.selectedMenuItem() == 'edit') {
            self.ExtRpt([]);
            $.ajax({
              url: self.selDepname() + "/viewextractlog",
              data: JSON.stringify({
                extops: self.selectedMenuItem(),
                extname: self.selectedNodesValue()[0].split(' ')[0]
              }),
              type: 'POST',
              dataType: 'json',
              timeout: 10000,
              context: self,
              error: function (xhr, textStatus, errorThrown) {
                if (textStatus == 'timeout' || textStatus == 'error') {
                  document.querySelector('#TimeoutMon').open();
                }
              },
              success: function (data) {
                console.log(data)
                if (self.selectedMenuItem() == 'startdef' || self.selectedMenuItem() == 'stop' || self.selectedMenuItem() == 'forcestop' || self.selectedMenuItem() == 'kill') {
                  self.popUpResizeSM("ViewExtractRptDialog");
                  document.querySelector('#ViewExtractRptDialog').open();
                  self.ExtRpt(data[0]);
                  getILFlow();
                } 
                else if (self.selectedMenuItem() == 'edit' ){
                  document.querySelector('#EditDialog').open();
                  self.ExtRpt(data[1]);
                }                
                else {
                  self.popUpResize("ViewExtractRptDialog");
                  document.querySelector('#ViewExtractRptDialog').open();
                  self.ExtRpt(data[0]);
                }


                //console.log(self);
                return self;

              }

            })
          }
          else if (self.selectedMenuItem() == 'del') {
            getDomains();
            document.querySelector('#ExtLoginDialog').open();
          }

        }

        else if (self.selProcType() == 'Rep') {
          self.dialogTitle('View Replicat ' + self.selectedNodesValue()[0].split(' ')[0] + ' Info');
          if (self.selectedMenuItem() == 'rpt' || self.selectedMenuItem() == 'chk' || self.selectedMenuItem() == 'stats' || self.selectedMenuItem() == 'startdef' || self.selectedMenuItem() == 'nofilterdup' || self.selectedMenuItem() == 'stop' || self.selectedMenuItem() == 'forcestop' || self.selectedMenuItem() == 'kill' || self.selectedMenuItem() == 'edit') {
            self.ExtRpt([]);
            $.ajax({
              url: self.selDepname() + "/viewreplicatlog",
              data: JSON.stringify({
                repops: self.selectedMenuItem(),
                repname: self.selectedNodesValue()[0].split(' ')[0]
              }),
              type: 'POST',
              dataType: 'json',
              timeout: 10000,
              context: self,
              error: function (xhr, textStatus, errorThrown) {
                if (textStatus == 'timeout' || textStatus == 'error') {
                  document.querySelector('#TimeoutMon').open();
                }
              },
              success: function (data) {
                if (self.selectedMenuItem() == 'startdef' || self.selectedMenuItem() == 'stop' || self.selectedMenuItem() == 'forcestop' || self.selectedMenuItem() == 'kill' || self.selectedMenuItem() == 'nofilterdup') {
                  self.popUpResizeSM("ViewExtractRptDialog");
                  document.querySelector('#ViewExtractRptDialog').open();
                  self.ExtRpt(data[0]);
                  getILFlow();
                  
                } 
                else if (self.selectedMenuItem() == 'edit' ){
                  document.querySelector('#EditDialog').open();
                  self.ExtRpt(data[1]);
                }
                else {
                  self.popUpResize("ViewExtractRptDialog");
                  document.querySelector('#ViewExtractRptDialog').open();
                  self.ExtRpt(data[0]);
                }
                

                //console.log(self);
                return self;

              }

            })
          }
          else if (self.selectedMenuItem() == 'del') {
            getDomains();
            document.querySelector('#ExtLoginDialog').open();
          }
          else if (self.selectedMenuItem() == 'begin') {
            getDomains();
            document.querySelector('#ReplicatBegin').open();
          }

        }
      }

      self.DelExt = function (data, event) {
          document.querySelector('#ExtLoginDialog').close();
          self.ExtRpt([]);
          $.ajax({
            url: self.selDepname() + "/ggextops",
            data: JSON.stringify({
              extname: self.selectedNodesValue()[0].split(' ')[0],
              domain: self.selectedDomCategory(),
              alias: self.selectedAliascategory(),
              extops: 'ext' + self.selectedMenuItem()
            }),
            type: 'POST',
            dataType: 'json',
            timeout: 10000,
            context: self,
            error: function (xhr, textStatus, errorThrown) {
              if (textStatus == 'timeout' || textStatus == 'error') {
                document.querySelector('#TimeoutMon').open();
              }
            },
            success: function (data) {
              document.querySelector('#ExtDelDialog').open();
              self.selectedDomCategory("");
              self.selectedAliascategory("");
              self.ExtRpt(data[0]);
              return self;
            }

          })
        }

      self.DelExtractRptOKClose = function (data, event) {
        document.querySelector('#ExtDelDialog').close();
        $.ajax({
          url: self.DepName() + "/delilext",
          type: 'POST',
          data: JSON.stringify({
            srcdep: self.selectedNodesValue()[0].split(' ')[1],
            extname: self.selectedNodesValue()[0].split(' ')[0],
          }),
          dataType: 'json',
          timeout: 10000,
          context: self,
          error: function (xhr, textStatus, errorThrown) {
            if (textStatus == 'timeout' || textStatus == 'error') {
              document.querySelector('#TimeoutMon').open();
            }
          },
          success: function (data) {
            getNodeFlow();
            return self;
          }

        })
      };


      self.DelRep = function (data, event) {
        document.querySelector('#ExtLoginDialog').close();
        self.ExtRpt([]);
        $.ajax({
          url: self.selDepname() + "/ggrepops",
          data: JSON.stringify({
            repname: self.selectedNodesValue()[0].split(' ')[0],
            domain: self.selectedDomCategory(),
            alias: self.selectedAliascategory(),
            repops: 'rep' + self.selectedMenuItem()
          }),
          type: 'POST',
          dataType: 'json',
          timeout: 10000,
          context: self,
          error: function (xhr, textStatus, errorThrown) {
            if (textStatus == 'timeout' || textStatus == 'error') {
              document.querySelector('#TimeoutMon').open();
            }
          },
          success: function (data) {
            document.querySelector('#RepDelDialog').open();
            self.ExtRpt(data[0]);
            return self;
          }

        })
      }

      this._checkValidationGroup = () => {
        var tracker = document.getElementById("trackerMon");
        //console.log(tracker)
        if (tracker.valid === "valid") {
          return true;
        }
        else {
          // show messages on all the components
          // that have messages hidden.
          tracker.showMessages();
          tracker.focusOn("@firstInvalidShown");
          return false;
        }
      };
      self.DelReplicatRptOKClose = function (data, event) {
        document.querySelector('#RepDelDialog').close();
        $.ajax({
          url: self.DepName() + "/delilrep",
          type: 'POST',
          data: JSON.stringify({
            tgtdep: self.selectedNodesValue()[0].split(' ')[1],
            repname: self.selectedNodesValue()[0].split(' ')[0],
          }),
          dataType: 'json',
          timeout: 10000,
          context: self,
          error: function (xhr, textStatus, errorThrown) {
            if (textStatus == 'timeout' || textStatus == 'error') {
              document.querySelector('#TimeoutMon').open();
            }
          },
          success: function (data) {
            getNodeFlow();
            return self;
          }

        })
      };


      self.AlterReplicatBegin = function (data, event) {
        document.querySelector('#ReplicatBegin').close();
        self.ExtRpt([]);
        document.querySelector('#RepProgress').open();
        $.ajax({
          url: self.selDepname() + "/ggrepops",
          data: JSON.stringify({
            repname: self.selectedNodesValue()[0].split(' ')[0],
            domain: self.selectedDomCategory(),
            alias: self.selectedAliascategory(),
            beginmode: self.currentbeginmode(),
            ctvalue: self.ctvalue(),
            seqnovalue: self.seqnovalue(),
            rbavalue: self.rbavalue(),
            repops: 'rep' + self.selectedMenuItem()
          }),
          type: 'POST',
          dataType: 'json',
          timeout: 10000,
          context: self,
          error: function (xhr, textStatus, errorThrown) {
            if (textStatus == 'timeout' || textStatus == 'error') {
              document.querySelector('#TimeoutMon').open();
            }
          },
          success: function (data) {
            document.querySelector('#RepProgress').close();
            self.ExtRpt(data[0]);
            document.querySelector('#ViewExtractRptDialog').open();
            //console.log(self);
            return self;
          }
        })
      }

      self.savePrm = function (event,data) {
          $.ajax({
              url: self.selDepname() + "/saveprm",
              type: 'POST',
              dataType: 'json',
              data: JSON.stringify({
                  procName: self.selectedNodesValue()[0].split(' ')[0],
                  currentParams: self.PrmWrite()
              }),
              TimeoutManage: 20000,
                  context: self,
                  error: function (xhr, textStatus, errorThrown) {
                      if(textStatus == 'TimeoutManage' || textStatus == 'error'){
                          document.querySelector('#SuppLogDialog').close();
                          document.querySelector('#TimeoutManage').open();
                      }
                  },
              success: function (data) {
                  document.querySelector('#ViewExtractRptDialog').open();
                  self.ExtRpt(data[0]);
                  return self;
              }
          })
      }


      self.ViewExtractRptOKClose = function (event) {
        document.querySelector('#ViewExtractRptDialog').close();
      };


      self.selectedILActionMenuItem = ko.observable();

      self.ILActionItem = function (event) {
        self.selectedILActionMenuItem(event.target.value);
        self.ExtRpt([]);
        //console.log(self.currentILJOb())
        document.querySelector('#RepProgress').open();
        $.ajax({
          url: self.DepName() + "/ggilaction",
          data: JSON.stringify({
            jobName: self.currentILJOb(),
            ilops : self.selectedILActionMenuItem()
          }),
          type: 'POST',
          dataType: 'json',
          timeout: 10000,
          context: self,
          error: function (xhr, textStatus, errorThrown) {
            if (textStatus == 'timeout' || textStatus == 'error') {
              document.querySelector('#RepProgress').close();
              document.querySelector('#TimeoutMon').open();
            }
          },
          success: function (data) {
            console.log(self.selectedILActionMenuItem())
            document.querySelector('#RepProgress').close();
            self.ExtRpt(data[0]);
            self.popUpResizeSM('ViewExtractRptDialog');
            if (self.selectedILActionMenuItem()=='stop'){
            self.dialogTitle('Stopping InitalLoad Job ' + self.currentILJOb());
            }
            else if (self.selectedILActionMenuItem()=='start'){
              self.dialogTitle('Starting InitalLoad Job ' + self.currentILJOb());
            }
            else if (self.selectedILActionMenuItem()=='purge'){
              self.dialogTitle('Purging InitalLoad Job ' + self.currentILJOb());
              self.currentILJOb('');
            }
            document.querySelector('#ViewExtractRptDialog').open();
            //console.log(self);
            return self;
          }
        })
    }

      self.stopJobAction = function(){
        document.querySelector('#StopProcess').close();
        //console.log("stop")
      }

      self.stopJobDlg = function (){
        document.querySelector('#StopProcess').open();
    }
    self.CloseOkjob =  function (event) {
      document.querySelector('#StopProcess').close();
  };

   //strt

   const data = [
    { name: "Home",
    id: "home", 
    icons: "oj-ux-ico-home" },
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
          self.router.go('signin');
        }
        else {
          app.onAppSuccess();
          self.currentILJOb(args.params.LoadName);
          if (self.currentILJOb()){
          self.getILTables();
          }
          getILData();
        }
      }

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
      self.transitionCompleted = function () {

      };
    }
  }
  /*
   * Returns a constructor for the ViewModel so that the ViewModel is constructed
   * each time the view is displayed.  Return an instance of the ViewModel if
   * only one instance of the ViewModel is needed.
   */
  return InitManageViewModel;
}
);