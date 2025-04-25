
define(['ojs/ojcore', 'knockout', 'jquery','appController','ojs/ojconverter-number', 'ojDiagram/viewModels/ggLayout','ojs/ojknockout-keyset','ojs/ojattributegrouphandler','ojs/ojarraydataprovider', 'ojs/ojarraytreedataprovider','ojs/ojknockout', 'ojs/ojdiagram','ojs/ojdialog','ojs/ojprogress-bar'],
        function (oj, ko, $, app,NumberConverter, layout, keySet ,attributeGroupHandler,ArrayDataProvider,ArrayTreeDataProvider) {

            class DataFlowViewModel {
                constructor(context){
                var self = this;
                self.DepName = context.routerState.detail.dep_url;
                self.ExtName = ko.observable();
               
                self.RepName = ko.observable();
               
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
                                self.decimalHalfDownConverter =
                                new NumberConverter.IntlNumberConverter({
                                    style: 'decimal',
                                    roundingMode: 'HALF_DOWN',
                                    maximumFractionDigits: 0,
                                    useGrouping: false
                                });
        


                self.onepDepList = ko.observableArray([]);

        
                function getOnepDep() {
                    self.onepDepList([]);
                    self.NodeData([]);
                    self.LinkData([]);
                    $.ajax({
                        url: self.DepName() + "/onepdep",
                        type: 'GET',
                        dataType: 'json',
                        context: self,
                        error: function (e) {
                            //console.log(e);
                        },
                        success: function (data) {
                            for (var i = 0; i < data[0].length; i++) {
                            self.onepDepList.push({'dep' : data[0][i].dep , 'dep_url' :  data[0][i].dep_url} );
                            getReplionFlow(data[0][i].dep,data[0][i].dep_url);
                             }             
                             self.NodeData.push({'id' : 'Extracts' , 'nodes' : self.NodeExt()},{'id' : 'Pumps'  , 'nodes' :  self.NodePmp()},{'id' : 'Replicats' , 'nodes' :  self.NodeRep()});

                             //console.log(self.NodeData())
                            self.onepDepList.valueHasMutated();
                            return self;
                        }
        
                    })
                }
        



                function getReplionFlow(dep,dep_url) {
                  self.NodeExt([]);
                  self.NodePmp([]);
                  self.NodeRep([]);
                  $.ajax({
                       url: dep_url + '/gginfodiag',
                      type: 'GET',
                      dataType: 'json',

                      error: function (e) {
                          //console.log(e);
                      },
                      success: function (data) {
                        
                        for(var key in data[0]['nodeext'] ){
                        self.NodeExt.push({'id' : key+ ' '+ dep});
                        }
                        
                        for(var key in data[0]['nodepmp'] ){
                          self.NodePmp.push({'id' : key+ ' '+ dep });
                          }

                          for(var key in data[0]['noderep'] ){
                            self.NodeRep.push({'id' : key+ ' '+ dep });
                            }
                            self.NodeData.valueHasMutated();
                         for (var i = 0; i < data[1].length; i++) {
                              self.LinkData.push({'start' : data[1][i].start+ ' '+ dep,'category' :data[1][i].category ,'end' :data[1][i].end+ ' '+ dep,'id' : i});
                              
                         }                        

                          return self;

                      }
                  })
              };


              self.nodeDataProvider = new ArrayTreeDataProvider(self.NodeData, {keyAttributes: 'id', childrenAttribute: "nodes"});
              self.linkDataProvider = new ArrayDataProvider(self.LinkData,{keyAttributes: 'id'});
              var color = (new attributeGroupHandler.ColorAttributeGroupHandler()).getValue(0);
              self.expandedNodes = new keySet.ObservableKeySet().add(['Extracts','Pumps','Replicats']);
              self.layoutFunc = layout.containerLayout;
      
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
        return {"insert": rootElement};
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
            var w = childContent.w + 90,
                h = childContent.h + 100;
            rootElement = createSVG('nodeSvg' + nodeId, w, h);
            var group = addGroup(rootElement, 'topGroup' + nodeId);
            w-=2, h-=2; //reduce width and height for inner elements
            addRect(group, 'rect' + nodeId, 1, 1, w, h, "white");   
            addRect(group, 'rectHdr' + nodeId, 1, 1, w, 25, color); //header size 
            addChildContent(group, childContent.element);
          }
          else {
            //render collapsed or leaf node
            rootElement = createSVG('nodeSvg' + nodeId, 1000,1000);  //size of the main container
            var group = addGroup(rootElement, 'topGroup' + nodeId);
            addRect(group, 'rectInner' + nodeId, 25 , 15, 250, 45, self.getStyleUrl("gradient1")); //position of the child containers inside main
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
        return {"insert":rootElement};
      };
      // SVG helper functions for node rendering
      function createSVG (id, width, height) {
        var svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
        svg.setAttributeNS(null, 'width', width);
        svg.setAttributeNS(null, 'height', height);
        svg.setAttributeNS(null, 'viewBox', "0 0 " +  width + " " + height);
        return svg;
      };
      function addGroup (parent, id) {
        var group = document.createElementNS('http://www.w3.org/2000/svg','g');
        group.setAttributeNS(null, 'id', id);
        parent.appendChild(group);
        return group;
      };
      function addRect (parent, id, x, y, w, h, fill) {
        var svgRect = document.createElementNS('http://www.w3.org/2000/svg','rect');
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
      function addChildContent (parent, elem) {
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
                if (sessionStorage.getItem("userName")==null) {
                    self.router.go({path : 'signin'});
                }
                else
                {
                app.onAppSuccess();
 //               getReplionFlow();
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
}
);
