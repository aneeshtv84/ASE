"use strict";
define(function() {

  /**
   * Sankey demo
   * A columnar layout, with sources and sinks based on maximum source distance
   *
   * @param {DvtDiagramLayoutContext} ctx the layout context object
   */
  var DemoSankeyLayout = function(ctx) {
    this._ctx = ctx;
  };

  DemoSankeyLayout.COLUMN_WIDTH = 2800;
  DemoSankeyLayout.ROW_GAP = 15;
  DemoSankeyLayout.LABEL_GAP = 20;
  DemoSankeyLayout.LINK_CURVATURE = .33;

  /**
   * Main function that does the sankey layout (Layout entry point)
   * A columnar layout, with sources and sinks based on maximum source distance
   *
   * @param {DvtDiagramLayoutContext} ctx the layout context object
   */
  DemoSankeyLayout.layout = function(ctx) {
    new DemoSankeyLayout(ctx).layout();
  };

  /**
   * Performs the layout
   */
  DemoSankeyLayout.prototype.layout = function() {
    this._positionNodes();
    this._positionLinks();
  }

  /**
   * Positions the nodes in columns with sources on the left and sinks on the right.  All other nodes will be placed
   * in columns based on maximal distance from a source
   */
  DemoSankeyLayout.prototype._positionNodes = function() {
    var columns = this._getColumns();
    // Calculate node positions iteratively
    for (var i = 0; i < 25; i++) {
      this._iterateNodePositions(columns, true);
      this._iterateNodePositions(columns, false);
    }

    // Position Node Labels
    for (var i = 0; i < columns.length; i++) {
      var column = columns[i];
      for (var j = 0; j < column.length; j++) {
        // Get the position of the node
        var node = this._ctx.getNodeById(column[j]);
        var position = node.getPosition();
        // Set the position of the node label on the right or left depending on the column index
        var bounds = node.getContentBounds();
        var labelBounds = node.getLabelBounds();
        var labelPositionX = 0;
        if (i < columns.length / 2) {
          node.setLabelHalign("left");
          labelPositionX = position.x + bounds.w + DemoSankeyLayout.LABEL_GAP;
        }
        else{
          node.setLabelHalign("right");
          labelPositionX = position.x - DemoSankeyLayout.LABEL_GAP;
        }
        node.setLabelPosition(
          {'x': labelPositionX,
           'y': position.y + (bounds.h - labelBounds.h)/2});
      }
    }
  };

  /**
   * Positions a single column in order separated only by the rowGap
   *
   * @param {array} columns the array of columns
   * @param {number} columnIndex the index of the column to position
   */
  DemoSankeyLayout.prototype._positionColumn = function(columns, columnIndex) {
    var column = columns[columnIndex];
    var x = columnIndex * DemoSankeyLayout.COLUMN_WIDTH;
    var y = 0;
    for (var i = 0; i < column.length; i++) {
      // Set the position of the node
      var node = this._ctx.getNodeById(column[i]);
      node.setPosition({'x': x, 'y': y});
      var bounds = node.getContentBounds();
      y += bounds.h + DemoSankeyLayout.ROW_GAP;
    }
  };

  /**
   * Reposition nodes using weighted average of incoming or outgoing links
   *
   * @param {array} columns the array of columns
   * @param {boolean} upsteam whether to start at the sources and average downstream nodes or
   *                          to start at the sinks and average upstream nodes
   */
  DemoSankeyLayout.prototype._iterateNodePositions = function(columns, upstream) {
    var start = upstream ? columns.length - 1 : 0;
    var end = upstream ? 0 : columns.length - 1;
    var step = upstream ? -1 : 1;
    var linkMap = upstream ? this._outLinkMap : this._inLinkMap;
    // Explicitly position start column
    this._positionColumn(columns, start);
    // Use weighted average to position each successive column
    for (var i = start + step; i != end + step; i += step) {
      var column = columns[i];
      for (var j = 0; j < column.length; j++) {
        var node = this._ctx.getNodeById(column[j]);
        //var nodeSize = parseFloat(node.getLayoutAttributes()['size']);
        var nodeSize = this._getNodeSize(node);
        var links = linkMap[node.getId()];
        var centerY = 0;
        for (var k = 0; k < links.length; k++) {
          var link = this._ctx.getLinkById(links[k]);
          //var linkSize = parseFloat(link.getLayoutAttributes()['size']);
          var linkSize = this._getLinkSize(link, null);
          var linkedNodeId = upstream ? link.getEndId() : link.getStartId();
          var linkedNode = this._ctx.getNodeById(linkedNodeId);
          centerY += (linkedNode.getPosition().y + linkedNode.getContentBounds().h / 2) * linkSize / nodeSize;
        }
        node.setPosition({'x': i * DemoSankeyLayout.COLUMN_WIDTH, 'y': centerY - node.getContentBounds().h/2});
      }
    }
    for (var i = 0; i < columns.length; i++) {
      this._separateNodes(columns, i);
    }
  }

  /**
   * Separates any overlapping nodes in the specified column
   *
   * @param {array} columns the array of columns
   * @param {number} columnIndex the index of the column to separate
   */
  DemoSankeyLayout.prototype._separateNodes = function(columns, columnIndex) {
    var ctx = this._ctx;
    var column = columns[columnIndex];
    // Sort the column based on center y position
    column.sort(function (a, b) {
      var nodeA = ctx.getNodeById(a);
      var nodeB = ctx.getNodeById(b);
      var centerA = nodeA.getPosition().y + nodeA.getContentBounds().h/2;
      var centerB = nodeB.getPosition().y + nodeB.getContentBounds().h/2;
      return centerA - centerB;
    });
    // If any consecutive nodes overlap, move the first node (and any preceding nodes) up by half the overlap and the
    // second node (and any following nodes) down by half the overlap
    if (column.length > 1) {
      for (var i = 0; i < column.length - 1; i++) {
        var nodeA = this._ctx.getNodeById(column[i]);
        var nodeB = this._ctx.getNodeById(column[i+1]);
        var bottomA = nodeA.getPosition().y + nodeA.getContentBounds().h
        var topB = nodeB.getPosition().y;
        if (bottomA + DemoSankeyLayout.ROW_GAP > topB) {
          // Nodes overlap, calculate the adjustment
          var adjustment = (bottomA + DemoSankeyLayout.ROW_GAP - topB)/2;
          for (var j = 0; j <= i; j++) {
            var node = this._ctx.getNodeById(column[j]);
            var position = node.getPosition();
            node.setPosition({'x': position.x, 'y': position.y - adjustment});
          }
          for (var j = i+1; j < column.length; j++) {
            var node = this._ctx.getNodeById(column[j]);
            var position = node.getPosition();
            node.setPosition({'x': position.x, 'y': position.y + adjustment});
          }
        }
      }
    }
  };

  /**
   * Positions the links as thick sequential curves down the sides of nodes
   */
  DemoSankeyLayout.prototype._positionLinks = function() {
    var ctx = this._ctx;
    for (var nodeId in this._inLinkMap) {
      var inLinks = this._inLinkMap[nodeId];
      inLinks.sort(function(a, b) {
        var nodeA = ctx.getNodeById(ctx.getLinkById(a).getStartId());
        var nodeB = ctx.getNodeById(ctx.getLinkById(b).getStartId());
        var centerA = nodeA.getPosition().y + nodeA.getContentBounds().h/2;
        var centerB = nodeB.getPosition().y + nodeB.getContentBounds().h/2;
        return centerA - centerB;
      });
    }
    for (var nodeId in this._outLinkMap) {
      var outLinks = this._outLinkMap[nodeId];
      outLinks.sort(function(a, b) {
        var nodeA = ctx.getNodeById(ctx.getLinkById(a).getEndId());
        var nodeB = ctx.getNodeById(ctx.getLinkById(b).getEndId());
        var centerA = nodeA.getPosition().y + nodeA.getContentBounds().h/2;
        var centerB = nodeB.getPosition().y + nodeB.getContentBounds().h/2;
        return centerA - centerB;
      });
    }

    var linkCount = this._ctx.getLinkCount();
    for (var i = 0; i < linkCount; i++) {
      var link = this._ctx.getLinkByIndex(i);
      //var size = parseFloat(link.getLayoutAttributes()['size']);
      var size = this._getLinkSize(link, null);
      var startNode = this._ctx.getNodeById(link.getStartId());
      var endNode = this._ctx.getNodeById(link.getEndId());
      var startNodeLinks = this._outLinkMap[link.getStartId()];
      var endNodeLinks = this._inLinkMap[link.getEndId()];
      var linkStartTop = 0;
      for (var j = 0; j < startNodeLinks.length; j++) {
        if (startNodeLinks[j] == link.getId()) {
          break;
        }
        var previousLink = this._ctx.getLinkById(startNodeLinks[j]);
        //linkStartTop += parseFloat(previousLink.getLayoutAttributes()['size']);
        linkStartTop += this._getLinkSize(previousLink, null);
      }
      var linkEndTop = 0;
      for (var j = 0; j < endNodeLinks.length; j++) {
        if (endNodeLinks[j] == link.getId()) {
          break;
        }
        var previousLink = this._ctx.getLinkById(endNodeLinks[j]);
        //linkEndTop += parseFloat(previousLink.getLayoutAttributes()['size']);
        linkEndTop += this._getLinkSize(previousLink, null);
      }
      var startX = startNode.getPosition().x + startNode.getContentBounds().w;
      var startY = startNode.getPosition().y + linkStartTop + size/2;
      var endX = endNode.getPosition().x;
      var endY = endNode.getPosition().y + linkEndTop + size/2;
      link.setPoints(['M', startX, startY,
                      'C', DemoSankeyLayout.LINK_CURVATURE * startX + (1 - DemoSankeyLayout.LINK_CURVATURE) * endX, startY,
                           (1 - DemoSankeyLayout.LINK_CURVATURE) * startX + DemoSankeyLayout.LINK_CURVATURE * endX, endY,
                           endX, endY]);
    }
  };

  /**
   * Gets the center position of a node
   *
   * @param {string} id the id of the specified node
   * @return {Object} the center position of the specified node - an object containing x, y coordinates
   */
  DemoSankeyLayout.prototype._getCenter = function(id) {
    var node = this._ctx.getNodeById(id);
    var position = node.getPosition();
    var bounds = node.getContentBounds();
    var center = {'x':position.x + bounds.w/2, 'y':position.y + bounds.h/2};
    return center;
  };

  /**
   * Creates maps of in links and out links indexed by node id
   */
  DemoSankeyLayout.prototype._generateLinkMaps = function() {
    this._inLinkMap = {};
    this._outLinkMap = {};
    var linkCount = this._ctx.getLinkCount();
    for (var i = 0; i < linkCount; i++) {
      var link = this._ctx.getLinkByIndex(i);
      var linkId = link.getId();
      var startId = link.getStartId();
      var endId = link.getEndId();
      var inLinks = this._inLinkMap[endId];
      inLinks = inLinks ? inLinks : [];
      var outLinks = this._outLinkMap[startId];
      outLinks = outLinks ? outLinks : [];
      inLinks.push(linkId);
      outLinks.push(linkId);
      this._inLinkMap[endId] = inLinks;
      this._outLinkMap[startId] = outLinks;
    }
  };

  /**
   * Splits the nodes into columns
   *
   * @return {array} an array of arrays representing the columns from left to right
   */
  DemoSankeyLayout.prototype._getColumns = function() {
    this._generateLinkMaps();
    var nodeCount = this._ctx.getNodeCount();
    var sources = [];
    var sinks = [];
    var distances = {};
    // Identify the sources and sinks
    // Initialize the distance map
    for (var i = 0; i < nodeCount; i++) {
      var nodeId = this._ctx.getNodeByIndex(i).getId();
      if (!this._inLinkMap[nodeId]) {
        sources.push(nodeId);
      }
      if (!this._outLinkMap[nodeId]) {
        sinks.push(nodeId);
      }
      distances[nodeId] = 0;
    }
    // Breadth-first search following links from the sources and incrementing node distances as we find them
    var currentNodes = sources.slice(0);
    var distance = 1;
    var maxDistance;
    while (currentNodes.length > 0) {
      var nextNodes = [];
      for (var i = 0; i < currentNodes.length; i++) {
        var outLinks = this._outLinkMap[currentNodes[i]];
        if (outLinks) {
          for (var j = 0; j < outLinks.length; j++) {
            var link = this._ctx.getLinkById(outLinks[j]);
            var end = link.getEndId();
            distances[end] = distance;
            maxDistance = distance;
            if (nextNodes.indexOf(end) == -1) {
              nextNodes.push(end);
            }
          }
        }
      }
      currentNodes = nextNodes;
      distance++;
    }
    var columnCount = maxDistance + 1;
    // Place all sinks in the rightmost column
    for (var i = 0; i < sinks.length; i++) {
      distances[sinks[i]] = columnCount - 1;
    }
    var columns = [];
    for (var i = 0; i < columnCount; i++) {
      columns[i] = [];
    }
    for (var i = 0; i < nodeCount; i++) {
      var node = this._ctx.getNodeByIndex(i);
      var id = node.getId();
      columns[distances[id]].push(id);
    }
    return columns;
  };

  DemoSankeyLayout.prototype._getNodeSize = function(node, nodeData) {
    return node.getContentBounds().h;
  };

  DemoSankeyLayout.prototype._getLinkSize = function(link) {
    return link.getLinkWidth();
  };

  return DemoSankeyLayout;
});