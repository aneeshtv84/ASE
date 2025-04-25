"use strict";
define(function() {
  
  var DemoContainerLayout = {};
  /**
   * Main function that performs container layout (Layout entry point)
   * Top level nodes are positioned horizontally. Nodes inside containers are positioned vertically.
   * @param {DvtDiagramLayoutContext} layoutContext object that defines a context for layout call
   */
  DemoContainerLayout.containerLayout = function(layoutContext) {
    var nodeCount = layoutContext.getNodeCount();
    var currX = 0;
    for (var ni = 0; ni < nodeCount; ni++) {
      var node = layoutContext.getNodeByIndex(ni);
      if (node.isDisclosed() && node.getChildNodes()) {
        DemoContainerLayout._layoutVertical(layoutContext, node.getChildNodes());
      }
      var bounds = node.getContentBounds();
      node.setPosition({'x':currX, 'y': - bounds.y - bounds.h * .5});
      DemoContainerLayout._positionLabel(node);
      currX += bounds.w + 700;
    }
    
    //position the links
    var linkCount = layoutContext.getLinkCount();
    for (var i = 0; i < linkCount; i++) {
      DemoContainerLayout._createLink(layoutContext, layoutContext.getLinkByIndex(i));
    }
  };

  /**
   * Layout child nodes vertically
   * @param {DvtDiagramLayoutContext} layoutContext layout context
   * @param {array} nodes nodes array
   */  
  DemoContainerLayout._layoutVertical = function (layoutContext, nodes) {
    var padding = 30; 
    var currX = 0;  
    var currY = 0;  
    var nodeCount = nodes.length;
    for (var ni = 0;ni < nodeCount;ni++) {
      var node = nodes[ni];
      if (node.isDisclosed() && node.getChildNodes()) {
        DemoContainerLayout._layoutVertical(layoutContext, node.getChildNodes());
      }
      var bounds = node.getContentBounds();
      node.setPosition({'x': currX - bounds.x - bounds.w * .5, 'y': currY});
      DemoContainerLayout._positionLabel(node);
      currY += bounds.h + padding;
    }
  };

  /**
   * Helper function creates a curved link between nodes
   * @param {DvtDiagramLayoutContext} layoutContext Object that defines a context for layout call
   * @param {DvtDiagramLayoutContextLink} link Link object
   */
  DemoContainerLayout._createLink = function(layoutContext, link) {
      var startId = link.getStartId();
      var endId = link.getEndId();
      var node1 = layoutContext.getNodeById(startId);
      var node2 = layoutContext.getNodeById(endId);
      var commonContainerId = layoutContext.getCommonContainer(startId, endId);
      var n1Position = node1.getRelativePosition(commonContainerId);
      var n2Position = node2.getRelativePosition(commonContainerId);
      link.setCoordinateSpace(commonContainerId);
      
      var n1Bounds = node1.getBounds();
      var n2Bounds = node2.getBounds();
      var startX, startY, endX, endY;
      //find centers
      var cn1X = n1Position.x + .5 * n1Bounds.w;
      var cn2X = n2Position.x + .5 * n2Bounds.w;
      if (Math.abs(cn1X - cn2X) < 10) { //vertical nodes
        var cn1Y = .5 * (n1Position.y + n1Bounds.h);
        var cn2Y = .5 * (n2Position.y + n2Bounds.h);
        startX = n1Position.x + .5*n1Bounds.w;
        endX = n2Position.x + .5*n2Bounds.w;
        if (cn1Y < cn2Y) {
          startY = n1Position.y + n1Bounds.h + link.getStartConnectorOffset();
          endY = n2Position.y - link.getEndConnectorOffset();
        }
        else {
          startY = n1Position.y - link.getEndConnectorOffset()
          endY = n2Position.y + n2Bounds.h + link.getStartConnectorOffset();
        }
        link.setPoints(DemoContainerLayout._createVerticalLinkPath(startX, startY, endX, endY));
      }
      else { //horizontal
        if (cn1X < cn2X) //left to right
        {
          startX = n1Position.x + n1Bounds.x + n1Bounds.w + link.getStartConnectorOffset();
          endX = n2Position.x - link.getEndConnectorOffset();
        }
        else { //right to left
          startX = n1Position.x - link.getStartConnectorOffset();
          endX = n2Position.x + n2Bounds.x + n2Bounds.w + link.getEndConnectorOffset();
        }
        startY = n1Position.y + n1Bounds.y + .5 * n1Bounds.h;
        endY = n2Position.y + n2Bounds.y + .5 * n2Bounds.h;
        link.setPoints(DemoContainerLayout._createSideLinkPath(startX, startY, endX, endY));
      }

      //center label on link
      var labelBounds = link.getLabelBounds();
      if (labelBounds) {
        var labelX = startX;
        var labelY = startY - labelBounds.h;
        //link.setLabelPosition(new DvtDiagramPoint(labelX, labelY));
        link.setLabelPosition({'x':labelX, 'y': labelY});
      }    
  };

  /**
   * Helper function creates a curved link that connects nodes sides
   * The function uses quadratic Bezier to create a curve
   * @param {number} startX X coordinate for the link start
   * @param {number} startY Y coordinate for the link start
   * @param {number} endX X coordinate for the link end
   * @param {number} endY Y coordinate for the link end
   */
  DemoContainerLayout._createSideLinkPath = function(startX, startY, endX, endY) {
    var path = ["M", startX, startY];
    var midX = startX + .5 * (endX - startX);
    var midY = startY + .5 * (endY - startY);
    var c1X = midX;   // X coordinate for the first control point
    var c1Y = startY; // Y coordinate for the first control point
    var c2X = midX;   // X coordinate for the second control point
    var c2Y = endY;   // Y coordinate for the second control point
    path.push("Q");
    path.push(c1X);
    path.push(c1Y);
    path.push(midX);
    path.push(midY);
    path.push("Q");
    path.push(c2X);
    path.push(c2Y);
    path.push(endX);
    path.push(endY);
    return path;
  };

  /**
   * Helper function creates a plain link that connects nodes bottom to top
   * @param {number} startX X coordinate for the link start
   * @param {number} startY Y coordinate for the link start
   * @param {number} endX X coordinate for the link end
   * @param {number} endY Y coordinate for the link end
   */  
  DemoContainerLayout._createVerticalLinkPath = function(startX, startY, endX, endY) {
    var path = ["M", startX, startY];
    path.push("L");
    path.push(endX);
    path.push(endY);
    return path;
  };
  
  /**
   * Helper function that sets label position in the middle of the diagram node
   * @param {DvtDiagramLayoutContextNode} node object that defines node context for the layout
   */
  DemoContainerLayout._positionLabel = function (node) {
    var nodeBounds = node.getContentBounds();
    var nodePos = node.getPosition();
    var nodeLabelBounds = node.getLabelBounds();
    if (nodeLabelBounds) {
      if (node.isDisclosed()) {
        //position label in the middle of top 20 px of the node
        var labelY = nodeBounds.y + nodePos.y + .5 * (20 - nodeLabelBounds.h);
      }
      else {
        //position label in the middle of the node
        var labelY = nodeBounds.y + nodePos.y + .5 * (nodeBounds.h - nodeLabelBounds.h);
      }
      var labelX = nodeBounds.x + nodePos.x + .5 * (nodeBounds.w);
      node.setLabelPosition({'x': labelX, 'y': labelY});        
      node.setLabelHalign("center");
    }
  };  
  return DemoContainerLayout;
});