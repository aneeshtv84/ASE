define(['ojs/ojcore', 'knockout', 'jquery', 'appController',
    'ojs/ojtranslation', 'ojs/ojconverter-number', 'ojs/ojconverterutils-i18n', 'ojs/ojconverter-datetime', 'ojs/ojarraydataprovider',"ojs/ojpagingdataproviderview",
    'ojs/ojmasonrylayout', 'ojs/ojtable', 'ojs/ojselectsingle',
    'ojs/ojbutton', 'ojs/ojinputnumber', 'ojs/ojdatetimepicker', 'ojs/ojinputtext', 'ojs/ojdialog', 'ojs/ojmenu', 'ojs/ojoption',
    'ojs/ojselectcombobox', 'ojs/ojavatar', 'ojs/ojlabel', 'ojs/ojlabelvalue', 'ojs/ojprogress-bar', 'ojs/ojcheckboxset',
    'ojs/ojformlayout', 'ojs/ojradioset','ojs/ojvalidationgroup',"ojs/ojpagingcontrol"],
    function (oj, ko, $, app, Translations, NumberConverter, ConverterUtilsI18n, DateTimeConverter, ArrayDataProvider,PagingDataProviderView) {

        class ManageViewModel {
            constructor(args) {
                var self = this;
                self.DepName = args.routerState.detail.dep_url;
                //console.log(self.DepName());
                self.MgrName = ko.observable();
                self.ExtName = ko.observable();
                self.PmpName = ko.observable();
                self.RepName = ko.observable();
                self.maxRowsStretch = ko.observable();
                self.dynamicPortList = ko.observable();
                self.mgrPortCheck = ko.observable(true);
                self.dynamicPortListCheck = ko.observable(false);
                self.dynamicPortListCheckEnable = ko.observable(false);
                self.style = ko.observable();


                if (self.dynamicPortListCheckEnable == false) {
                    self.dynamicPortListCheck == false;
                }

                self.MgrData1 = ko.observableArray([]);
                self.ExtData1 = ko.observableArray([]);
                self.PmpData1 = ko.observableArray([]);
                self.RepData1 = ko.observableArray([]);


                self.styleMgr = ko.observable();
                self.styleExt = ko.observable();
                self.stylePmp = ko.observable();
                self.styleRep = ko.observable();

                self.ExtATCSN = ko.observable();
                self.ExtAFTERCSN = ko.observable();
                self.RepATCSN = ko.observable();
                self.RepAFTERCSN = ko.observable();
                self.groupValid = ko.observable();

                self.decimalHalfDownConverter =
                    new NumberConverter.IntlNumberConverter({
                        style: 'decimal',
                        roundingMode: 'HALF_DOWN',
                        maximumFractionDigits: 0,
                        useGrouping: false
                    });

                var monAll;
                function refresh() {
                    $.ajax({
                        url: self.DepName() + "/gginfoall",
                        type: 'GET',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#SuppLogDialog').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            self.MgrData1([]);
                            self.ExtData1([]);
                            self.PmpData1([]);
                            self.RepData1([]);
                            console.log(data)
                            for (var i = 0; i < data[0].length; i++) {
                                if (data[0][i].extstat == 'ABENDED') {
                                    self.styleExt = { "background-color": "IndianRed" };
                                    self.ExtData1.push({ ExtName: data[0][i].extname, ExtStat: data[0][i].extstat, ExtLag: data[0][i].extlag, ExtChkLag: data[0][i].extchklag, collapsedSizeClass: 'oj-masonrylayout-tile-1x1', expandedSizeClass: 'oj-masonrylayout-tile-1x2', expanded: ko.observable(false) });

                                } else if (data[0][i].extstat == 'STOPPED') {
                                    self.styleExt = { "background-color": "Chocolate" };
                                    self.ExtData1.push({ ExtName: data[0][i].extname, ExtStat: data[0][i].extstat, ExtLag: data[0][i].extlag, ExtChkLag: data[0][i].extchklag, collapsedSizeClass: 'oj-masonrylayout-tile-1x1', expandedSizeClass: 'oj-masonrylayout-tile-1x2', expanded: ko.observable(false) });

                                } else if (data[0][i].extstat == 'RUNNING' || data[0][i].extstat == 'STARTING') {
                                    self.styleExt = { "background-color": "ForestGreen" };
                                    self.ExtData1.push({ ExtName: data[0][i].extname, ExtStat: data[0][i].extstat, ExtLag: data[0][i].extlag, ExtChkLag: data[0][i].extchklag, collapsedSizeClass: 'oj-masonrylayout-tile-1x1', expandedSizeClass: 'oj-masonrylayout-tile-1x2', expanded: ko.observable(false) });
                                }
                                if (data[0][i].pmpstat == 'ABENDED') {

                                    self.stylePmp = { "background-color": "IndianRed" };
                                    self.PmpData1.push({ PmpName: data[0][i].pmpname, PmpStat: data[0][i].pmpstat, PmpLag: data[0][i].pmplag, PmpChkLag: data[0][i].pmpchklag, collapsedSizeClass: 'oj-masonrylayout-tile-1x1', expandedSizeClass: 'oj-masonrylayout-tile-1x2', expanded: ko.observable(false) });

                                } else if (data[0][i].pmpstat == 'STOPPED') {

                                    self.stylePmp = { "background-color": "Chocolate" };
                                    self.PmpData1.push({ PmpName: data[0][i].pmpname, PmpStat: data[0][i].pmpstat, PmpLag: data[0][i].pmplag, PmpChkLag: data[0][i].pmpchklag, collapsedSizeClass: 'oj-masonrylayout-tile-1x1', expandedSizeClass: 'oj-masonrylayout-tile-1x2', expanded: ko.observable(false) });

                                } else if (data[0][i].pmpstat == 'RUNNING' || data[0][i].pmpstat == 'STARTING') {

                                    self.stylePmp = { "background-color": "ForestGreen" };
                                    self.PmpData1.push({ PmpName: data[0][i].pmpname, PmpStat: data[0][i].pmpstat, PmpLag: data[0][i].pmplag, PmpChkLag: data[0][i].pmpchklag, collapsedSizeClass: 'oj-masonrylayout-tile-1x1', expandedSizeClass: 'oj-masonrylayout-tile-1x2', expanded: ko.observable(false) });
                                }

                                if (data[0][i].repstat == 'ABENDED') {
                                    self.styleRep = { "background-color": "IndianRed" };
                                    self.RepData1.push({ RepName: data[0][i].repname, RepStat: data[0][i].repstat, RepLag: data[0][i].replag, RepChkLag: data[0][i].repchklag, collapsedSizeClass: 'oj-masonrylayout-tile-1x1', expandedSizeClass: 'oj-masonrylayout-tile-1x2', expanded: ko.observable(false) });
                                } else if (data[0][i].repstat == 'STOPPED') {

                                    self.styleRep = { "background-color": "Chocolate" };
                                    self.RepData1.push({ RepName: data[0][i].repname, RepStat: data[0][i].repstat, RepLag: data[0][i].replag, RepChkLag: data[0][i].repchklag, collapsedSizeClass: 'oj-masonrylayout-tile-1x1', expandedSizeClass: 'oj-masonrylayout-tile-1x2', expanded: ko.observable(false) });
                                } else if (data[0][i].repstat == 'RUNNING' || data[0][i].repstat == 'STARTING') {
                                    self.styleRep = { "background-color": "ForestGreen" };
                                    self.RepData1.push({ RepName: data[0][i].repname, RepStat: data[0][i].repstat, RepLag: data[0][i].replag, RepChkLag: data[0][i].repchklag, collapsedSizeClass: 'oj-masonrylayout-tile-1x1', expandedSizeClass: 'oj-masonrylayout-tile-1x2', expanded: ko.observable(false) });
                                }

                                if (data[0][i].mgrstat == 'DOWN!' || data[0][i].mgrstat == 'down!') {
                                    self.styleMgr = { "background-color": "IndianRed" };
                                    self.MgrData1.push({ MgrName: 'Manager', MgrStat: data[0].mgrstat, collapsedSizeClass: 'oj-masonrylayout-tile-1x1', expandedSizeClass: 'oj-masonrylayout-tile-1x2', expanded: ko.observable(false) });
                                }
                                else if (data[0][i].mgrstat == 'running') {
                                    self.styleMgr = { "background-color": "ForestGreen" };
                                    self.MgrData1.push({ MgrName: 'Manager', MgrStat: data[0][i].mgrstat, collapsedSizeClass: 'oj-masonrylayout-tile-1x1', expandedSizeClass: 'oj-masonrylayout-tile-1x2', expanded: ko.observable(false) });
                                }
                            }

                            return self;
                        }
                    })

                }

                self.currentbeginmode = ko.observable('Now');

                self.beginmode = ko.observableArray([
                    { value: 'Now', label: 'Begin Now' },
                    { value: 'Time', label: 'Custom Time' },
                    { value: 'LOC', label: 'Location' }
                ]);


             
                self.startOptionDP = new ArrayDataProvider(self.beginmode, { keyAttributes: 'value' });



                self.currentExtBeginMode = ko.observable('Now');

                self.currentPmpBeginMode = ko.observable('');

                self.extBeginMode = ko.observableArray([
                    { value: 'Now', label: 'Begin Now' },
                    { value: 'Time', label: 'Custom Time' },
                    { value: 'SCN', label: 'SCN' }
                ]);

                self.extStartOptionDP = new ArrayDataProvider(self.extBeginMode, { keyAttributes: 'value' });

                self.secondConverter = new DateTimeConverter.IntlDateTimeConverter(
                    {
                        pattern: "yyyy-MM-dd HH:mm:ss"
                    });

                self.ctvalue = ko.observable(ConverterUtilsI18n.IntlConverterUtils.dateToLocalIso(new Date()));

                self.seqnovalue = ko.observable(0);
                self.rbavalue = ko.observable(0);

                self.decimalHalfDownConverter =
                    new NumberConverter.IntlNumberConverter({
                        style: 'decimal',
                        roundingMode: 'HALF_DOWN',
                        maximumFractionDigits: 0,
                        useGrouping: false
                    });

                self.args = args;
                self.router = self.args.parentRouter;



                self.selectedExtractMenuItem = ko.observable('');
                self.selectedPumpMenuItem = ko.observable('');
                self.selectedReplicatMenuItem = ko.observable('');
                self.stopTextValue = ko.observable('');
                var parameter = '';




                self.menuExtractItemAction = function (event) {
                    self.selectedExtractMenuItem(event.target.value);
                    //Manager Report File
                    if (self.selectedExtractMenuItem() == 'addext') {
                    self.router.go({ path: 'Designer' })
                    }
                    else if (self.selectedExtractMenuItem() == 'stopallext'){
                        self.delTitle('Stop All Primary Extracts ?');
                        self.stopTextValue('This Action will stop all Primary Extracts . Do you want to continue ?');
                        document.querySelector('#StopAllProcessDialog').open();
                        parameter =   {
                            ops : self.selectedExtractMenuItem(),
                            processName : self.ExtData1()                    
                         }
                    }
                    else if ( self.selectedExtractMenuItem() == 'startallext') {
                        parameter =   {
                            ops : self.selectedExtractMenuItem(),
                            processName : self.ExtData1()                    
                         }
                         self.delTitle('Start All Primary Extracts');
                        ProcessAction();

                    }
            }


            self.stopAllProc = function(data,event){
                document.querySelector('#StopAllProcessDialog').close();
                ProcessAction();
            }


                self.menuPumpItemAction = function () {
                    self.selectedPumpMenuItem(event.target.value);
                    //Manager Report File
                    if (self.selectedPumpMenuItem() == 'addpmp') {
                    self.router.go({ path: 'Designer' })
                    }
                    else if(self.selectedPumpMenuItem() == 'stopallpmp'){
                        self.delTitle('Stop All Pump Extracts ?');
                        self.stopTextValue('This Action will stop all Pump Extracts . Do you want to continue ?');
                        document.querySelector('#StopAllProcessDialog').open();
                        parameter =   {
                            ops : self.selectedPumpMenuItem(),
                            processName : self.PmpData1()                    
                         }
                    }
                    else if (self.selectedPumpMenuItem() == 'startallpmp') {
                        parameter =   {
                            ops : self.selectedPumpMenuItem(),
                            processName : self.PmpData1()                    
                         }
                         self.delTitle('Start All Pump Extracts');
                         ProcessAction();
                    }
            }
    

                self.menuReplicatItemAction = function () {
                    self.selectedReplicatMenuItem(event.target.value);
                    //Manager Report File
                    if (self.selectedReplicatMenuItem() == 'addrep') {
                    self.router.go({ path: 'Designer' })
                    }
                    else if(self.selectedReplicatMenuItem() == 'stopallrep'){
                        self.delTitle('Stop All Replicats ?');
                        self.stopTextValue('This Action will stop all Replicats . Do you want to continue ?');
                        document.querySelector('#StopAllProcessDialog').open();
                        parameter =   {
                            ops : self.selectedReplicatMenuItem(),
                            processName : self.RepData1()                    
                         }
                         
                    }
                    else if (self.selectedReplicatMenuItem() == 'startallrep') {
                        parameter =   {
                            ops : self.selectedReplicatMenuItem(),
                            processName : self.RepData1()                    
                         }

                         self.delTitle('Start All Replicats');
                         ProcessAction();
                    }
                };


                function ProcessAction() {
                    document.querySelector('#Progress').open();
                    self.ExtRpt([]);
                    $.ajax({
                        url: self.DepName() + "/ggprocessaction",
                        type: 'POST',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        data: JSON.stringify(parameter),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#Progress').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            document.querySelector('#Progress').close();
                            self.popUpResizeSM("ViewExtractRptDialog");
                            document.querySelector('#ViewExtractRptDialog').open();
                            self.ExtRpt(data[0]);
                            return self;
                
                        }
                
                    })
                }




                self.handledMgrCollapse = false;
                self.handledExtCollapse = false;
                self.handledPmpCollapse = false;
                self.handledRepCollapse = false;

                var closestByClass = function (el, className) {
                    while (!el.classList.contains(className)) {
                        // Increment the loop to the parent node
                        el = el.parentNode;
                        if (!el) {
                            return null;
                        }
                    }
                    return el;
                };


                self.MgrResizeTile = function (event, current) {
                    var target = event.target;

                    var tile = closestByClass(target, 'mgr-tile');
                    var masonryLayout = closestByClass(tile, 'oj-masonrylayout');
                    // get the data for the tile, which will be an item in the
                    // chemicals array defined above
                    var data = current.data;
                    self.MgrName = current.data.MgrName;
                    masonryLayout.resizeTile(
                        '#' + tile.getAttribute('id'),
                        data.expanded() ? data.collapsedSizeClass : data.expandedSizeClass);
                };

                // This listener is called before the tile is resized  for the Extract
                self.MgrHandleBeforeResize = function (event) {
                    var tile = event.detail.tile;
                    var context = ko.contextFor(tile);
                    var data = context.$current.data;
                    self.MgrName = context.$current.data.MgrName;
                    // If the tile is being collapsed, hide the additional
                    // expanded content before the tile is resized.
                    if (data.expanded()) {
                        data.expanded(false);
                        // Remember that this resize is a collapse so that the
                        // "resize" event listener called after the tile is resized
                        // does not also try to handle the operation.
                        self.handledMgrCollapse = true;
                    }
                };


                // This listener is called after the tile is resized  for the Extract
                self.MgrHandleResize = function (event) {
                    // Only handle the event if the tile is being expanded.
                    if (!self.handledMgrCollapse) {
                        clearInterval(monAll);
                        var tile = event.detail.tile;
                        // get the ko binding context for the tile DOM element
                        var context = ko.contextFor(tile);
                        // get the data for the tile, which will be an item in the
                        // chemicals array defined above
                        var data = context.$current.data;

                        self.MgrName = context.$current.data.MgrName;
                        // If the tile is being expanded, show the additional
                        // content after the tile is resized.
                        if (!data.expanded()) {
                            data.expanded(true);
                        }
                    }
                    else{
                        monAll = setInterval(refresh, 20000);
                    }
                    // Reset the flag for the next resize.
                    self.handledMgrCollapse = false;
                };



                // This listener is called when the resize button in the tile
                // is clicked.
                self.ExtResizeTile = function (event, current) {
                    var target = event.target;

                    var tile = closestByClass(target, 'ext-tile');
                    var masonryLayout = closestByClass(tile, 'oj-masonrylayout');
                    // get the data for the tile, which will be an item in the
                    // chemicals array defined above
                    var data = current.data;
                    self.ExtName = current.data.ExtName;
                    masonryLayout.resizeTile(
                        '#' + tile.getAttribute('id'),
                        data.expanded() ? data.collapsedSizeClass : data.expandedSizeClass);
                };

                // This listener is called before the tile is resized  for the Extract
                self.ExtHandleBeforeResize = function (event) {
                    var tile = event.detail.tile;
                    var context = ko.contextFor(tile);
                    var data = context.$current.data;
                    self.ExtName = context.$current.data.ExtName;
                    // If the tile is being collapsed, hide the additional
                    // expanded content before the tile is resized.
                    if (data.expanded()) {
                        data.expanded(false);
                        // Remember that this resize is a collapse so that the
                        // "resize" event listener called after the tile is resized
                        // does not also try to handle the operation.
                        self.handledExtCollapse = true;
                    }
                };


                // This listener is called after the tile is resized  for the Extract
                self.ExtHandleResize = function (event) {
                    // Only handle the event if the tile is being expanded.
                    if (!self.handledExtCollapse) {
                        clearInterval(monAll);
                        var tile = event.detail.tile;
                        // get the ko binding context for the tile DOM element
                        var context = ko.contextFor(tile);
                        // get the data for the tile, which will be an item in the
                        // chemicals array defined above
                        var data = context.$current.data;

                        self.ExtName = context.$current.data.ExtName;
                        // If the tile is being expanded, show the additional
                        // content after the tile is resized.
                        if (!data.expanded()) {
                            data.expanded(true);

                        }
                    }
                    else{
                        monAll = setInterval(refresh, 20000);
                    }
                    // Reset the flag for the next resize.
                    self.handledExtCollapse = false;
                };


                // This listener is called when the resize button in the tile
                // is clicked.
                self.PmpResizeTile = function (event, current) {
                    var target = event.target;

                    var tile = closestByClass(target, 'pmp-tile');
                    var masonryLayout = closestByClass(tile, 'oj-masonrylayout');
                    // get the data for the tile, which will be an item in the
                    // chemicals array defined above
                    var data = current.data;
                    self.PmpName = current.data.PmpName;
                    masonryLayout.resizeTile(
                        '#' + tile.getAttribute('id'),
                        data.expanded() ? data.collapsedSizeClass : data.expandedSizeClass);
                };

                // This listener is called before the tile is resized for thre Pump.
                self.PmpHandleBeforeResize = function (event) {
                    var tile = event.detail.tile;
                    var context = ko.contextFor(tile);
                    var data = context.$current.data;
                    self.PmpName = context.$current.data.PmpName;
                    // If the tile is being collapsed, hide the additional
                    // expanded content before the tile is resized.
                    if (data.expanded()) {
                        data.expanded(false);

                        // Remember that this resize is a collapse so that the
                        // "resize" event listener called after the tile is resized
                        // does not also try to handle the operation.
                        self.handledPmpCollapse = true;
                    }
                };

                // This listener is called after the tile is resized  for the Pump
                self.PmpHandleResize = function (event) {
                    // Only handle the event if the tile is being expanded.
                    if (!self.handledPmpCollapse) {
                        clearInterval(monAll);
                        var tile = event.detail.tile;
                        // get the ko binding context for the tile DOM element
                        var context = ko.contextFor(tile);
                        // get the data for the tile, which will be an item in the
                        // chemicals array defined above
                        var data = context.$current.data;

                        self.PmpName = context.$current.data.PmpName;
                        // If the tile is being expanded, show the additional
                        // content after the tile is resized.
                        if (!data.expanded()) {
                            data.expanded(true);
                                                  }
                    }
                    else{
                        monAll = setInterval(refresh, 20000);
                    }
                    // Reset the flag for the next resize.
                    self.handledPmpCollapse = false;
                };

                self.RepResizeTile = function (event, current) {
                    var target = event.target;

                    var tile = closestByClass(target, 'rep-tile');
                    var masonryLayout = closestByClass(tile, 'oj-masonrylayout');
                    // get the data for the tile, which will be an item in the
                    // chemicals array defined above
                    var data = current.data;
                    self.RepName = current.data.RepName;
                    masonryLayout.resizeTile(
                        '#' + tile.getAttribute('id'),
                        data.expanded() ? data.collapsedSizeClass : data.expandedSizeClass);
                };

                // This listener is called before the tile is resized for Replicat.
                self.RepHandleBeforeResize = function (event) {
                    var tile = event.detail.tile;
                    var context = ko.contextFor(tile);
                    var data = context.$current.data;
                    self.RepName = context.$current.data.RepName;
                    // If the tile is being collapsed, hide the additional
                    // expanded content before the tile is resized.
                    if (data.expanded()) {
                        data.expanded(false);
                        // Remember that this resize is a collapse so that the
                        // "resize" event listener called after the tile is resized
                        // does not also try to handle the operation.
                        self.handledRepCollapse = true;
                    }
                };

                // This listener is called after the tile is resized for the Replicat.
                self.RepHandleResize = function (event) {
                    // Only handle the event if the tile is being expanded.
                    if (!self.handledRepCollapse) {
                        clearInterval(monAll);
                        var tile = event.detail.tile;
                        // get the ko binding context for the tile DOM element
                        var context = ko.contextFor(tile);
                        // get the data for the tile, which will be an item in the
                        // chemicals array defined above
                        var data = context.$current.data;

                        self.RepName = context.$current.data.RepName;
                        // If the tile is being expanded, show the additional
                        // content after the tile is resized.
                        if (!data.expanded()) {
                            data.expanded(true);
                        }
                    }
                    else{
                        monAll = setInterval(refresh, 20000);
                    }
                    // Reset the flag for the next resize.
                    self.handledRepCollapse = false;
                };


                //Manager

                self.getMgrTileId = function (index) {
                    return 'mgr-tile' + (index + 1);
                };

                self.getMgrLabelId = function (index) {
                    return 'mgr-label' + (index + 1);
                };

                self.getMgrButtonId = function (index) {
                    return 'mgr-resizeButton' + (index + 1);
                };

                self.getMgrButtonLabelledBy = function (index) {
                    return self.getMgrButtonId(index) + ' ' + self.getMgrLabelId(index);
                };

                self.getMgrButtonLabel = function (data) {
                    return data.expanded() ?
                        Translations.getTranslatedString(
                            'oj-panel.labelAccButtonCollapse') :
                        Translations.getTranslatedString(
                            'oj-panel.labelAccButtonExpand');
                };

                self.getMgrButtonIcon = function (data) {
                    return {
                        'oj-panel-expand-icon': !data.expanded(),
                        'oj-panel-collapse-icon': data.expanded()
                    };
                };


                //Extract
                self.getExtTileId = function (index) {
                    return 'ext-tile' + (index + 1);
                };

                self.getExtLabelId = function (index) {
                    return 'ext-label' + (index + 1);
                };

                self.getExtButtonId = function (index) {
                    return 'ext-resizeButton' + (index + 1);
                };

                self.getExtButtonLabelledBy = function (index) {
                    return self.getExtButtonId(index) + ' ' + self.getExtLabelId(index);
                };

                self.getExtButtonLabel = function (data) {
                    return data.expanded() ?
                        Translations.getTranslatedString(
                            'oj-panel.labelAccButtonCollapse') :
                        Translations.getTranslatedString(
                            'oj-panel.labelAccButtonExpand');
                };

                self.getExtButtonIcon = function (data) {
                    return {
                        'oj-panel-expand-icon': !data.expanded(),
                        'oj-panel-collapse-icon': data.expanded()
                    };
                };


                //Pump 

                self.getPmpTileId = function (index) {
                    return 'pmp-tile' + (index + 1);
                };

                self.getPmpLabelId = function (index) {
                    return 'pmp-label' + (index + 1);
                };

                self.getPmpButtonId = function (index) {
                    return 'pmp-resizeButton' + (index + 1);
                };

                self.getPmpButtonLabelledBy = function (index) {
                    return self.getPmpButtonId(index) + ' ' + self.getPmpLabelId(index);
                };

                self.getPmpButtonLabel = function (data) {
                    return data.expanded() ?
                        Translations.getTranslatedString(
                            'oj-panel.labelAccButtonCollapse') :
                        Translations.getTranslatedString(
                            'oj-panel.labelAccButtonExpand');
                };

                self.getPmpButtonIcon = function (data) {
                    return {
                        'oj-panel-expand-icon': !data.expanded(),
                        'oj-panel-collapse-icon': data.expanded()
                    };
                };




                self.getRepTileId = function (index) {
                    return 'rep-tile' + (index + 1);
                };

                self.getRepLabelId = function (index) {
                    return 'rep-label' + (index + 1);
                };

                self.getRepButtonId = function (index) {
                    return 'rep-resizeButton' + (index + 1);
                };

                self.getRepButtonLabelledBy = function (index) {
                    return self.getRepButtonId(index) + ' ' + self.getRepLabelId(index);
                };

                self.getRepButtonLabel = function (data) {
                    return data.expanded() ?
                        Translations.getTranslatedString(
                            'oj-panel.labelAccButtonCollapse') :
                        Translations.getTranslatedString(
                            'oj-panel.labelAccButtonExpand');
                };

                self.getRepButtonIcon = function (data) {
                    return {
                        'oj-panel-expand-icon': !data.expanded(),
                        'oj-panel-collapse-icon': data.expanded()
                    };
                };



                self.CancelBehaviorOpt = ko.observable('icon');

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
                    self.selectedAliascategory('');
                    self.selectedUsercategory('');
                    self.uRepPass()
                    self.uName('');
                    self.uPasswd('');
                    self.uRepPass('');
                    self.valdom('')
                    $.ajax({
                        url: self.DepName() + "/ggcredstore",
                        type: 'GET',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#TimeoutManage').open();
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

                self.domname1DP = new ArrayDataProvider(self.domname1, {keyAttributes: 'value'});

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

                self.aliascategoriesDP = new ArrayDataProvider(self.aliascategories, {keyAttributes: 'value'});

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



                self.chkTblList = ko.observableArray([]);
                self.currentChkptTbl = ko.observable();

                self.infoChkptTbl = function (event, data) {
                    self.chkTblList([]);
                    self.currentChkptTbl('');
                    $.ajax({
                        url: self.DepName() + "/infochkpttbl",
                        type: 'POST',
                        data: JSON.stringify({
                            domain: self.selectedDomCategory(),
                            alias: self.selectedAliascategory(),
                        }),
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        contrep: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {

                            for (var i = 0; i < data[0].length; i++) {
                                self.chkTblList.push({ 'label': data[0][i], 'value': data[0][i] });
                            }
                            return self;
                        }

                    })
                }
                self.chkpttblDP = new ArrayDataProvider(self.chkTblList, { keyAttributes: 'value' });

                self.dialogStyle = ko.observable();


                //**************************************************************************** */            
                // Manager Functions
                //**************************************************************************** */

                function mgrOper() {
                    document.querySelector('#Progress').open();
                    self.MgrRpt([]);
                    $.ajax({
                        url: self.DepName() + "/ggmgrops",
                        type: 'POST',
                        dataType: 'json',
                        data: JSON.stringify({
                            mgrOps: self.selectedMgrMenuItem()
                        }),
                        context: self,
                        error: function (e) {
                            //console.log(e);
                            document.querySelector('#Progress').close();
                        },
                        success: function (data) {
                            document.querySelector('#Progress').close();
                            document.querySelector('#ViewMgrRptDialog').open();
                            self.MgrRpt(data[0]);
                            //console.log(self);
                            return self;
                        }
                    })
                }

                self.MgrRpt = ko.observableArray([]);
                self.selectedMgrMenuItem = ko.observable('');

                self.menuMgrItemAction = function (event) {
                    self.selectedMgrMenuItem(event.target.value);
                    //Manager Report File
                    if (self.selectedMgrMenuItem() == 'mgrrpt') {
                        document.querySelector('#Progress').open();
                        self.MgrRpt([]);
                        $.ajax({
                            url: self.DepName() + "/viewmgrrpt",
                            type: 'GET',
                            dataType: 'json',
                            timeout: sessionStorage.getItem("timeInetrval"),
                            context: self,
                            error: function (xhr, textStatus, errorThrown) {
                                if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                    document.querySelector('#Progress').close();
                                    document.querySelector('#TimeoutManage').open();
                                }
                            },
                            success: function (data) {
                                document.querySelector('#Progress').close();
                                self.popUpResize("ViewMgrRptDialog");
                                document.querySelector('#ViewMgrRptDialog').open();
                                self.MgrRpt(data[0]);
                                //console.log(self);
                                return self;

                            }

                        })
                    }
                    else if (self.selectedMgrMenuItem() == 'mgredit') {
                        document.querySelector('#Progress').open();
                        self.mgrPrmRead([]);
                        $.ajax({
                            url: self.DepName() + "/readmgrprm",
                            type: 'GET',
                            dataType: 'json',
                            timeout: sessionStorage.getItem("timeInetrval"),
                            context: self,
                            error: function (xhr, textStatus, errorThrown) {
                                if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                    document.querySelector('#TimeoutManage').open();
                                }
                            },
                            success: function (data) {
                                self.popUpResizeSM("ViewMgrRptDialog");
                                document.querySelector('#Progress').close();
                                document.querySelector('#EditMgrDialog').open();
                                self.mgrPrmRead(data[0]);
                                //console.log(self);
                                return self;
                            }
                        })
                    }
                    else if (self.selectedMgrMenuItem() == 'mgrstart' || self.selectedMgrMenuItem() == 'mgrrefresh' )  {
                        self.popUpResizeSM("ViewMgrRptDialog");
                        mgrOper();
                    }
                    else if (self.selectedMgrMenuItem() == 'mgrchildstatus' || self.selectedMgrMenuItem() == 'mgrportinfo' || self.selectedMgrMenuItem() == 'mgrpurgeold' ){
                        self.popUpResize("ViewMgrRptDialog");
                        mgrOper();
                    }
                    else if (self.selectedMgrMenuItem() == 'mgrstop') {
                        self.popUpResizeSM("ViewMgrRptDialog");
                        document.querySelector('#StopMgrDialog').open();
                    }

                    else if (self.selectedMgrMenuItem() == 'mgrkill') {
                        self.popUpResizeSM("ViewMgrRptDialog");
                        document.querySelector('#KillMgrDialog').open();
                    }
                }
                self.ViewMgrRptOKClose = function (event) {
                    refresh();
                    document.querySelector('#ViewMgrRptDialog').close();
                };



                self.mgrPrmRead = ko.observable();
                self.mgrPrmWrite = ko.observable();


                self.stopMgr = function (event, data) {
                    document.querySelector('#StopMgrDialog').close();
                    mgrOper();
                }


                self.killMgr = function (event, data) {
                    document.querySelector('#KillMgrDialog').close();
                    mgrOper();
                }

                self.saveMgrPrm = function (event, data) {
                    $.ajax({
                        url: self.DepName() + "/writemgrprm",
                        type: 'POST',
                        dataType: 'json',
                        data: JSON.stringify({
                            currentMgrParams: self.mgrPrmWrite()
                        }),
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#SuppLogDialog').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            document.querySelector('#EditMgrDialog').close();
                            document.querySelector('#ViewMgrRptDialog').open();
                            self.MgrRpt(data[0]);
                            return self;
                        }
                    })
                }

                //**************************************************************************** */            
                // Extract Functions
                //**************************************************************************** */


                self.ExtRpt = ko.observableArray([]);
                self.addExtTrailName = ko.observable();
                self.addExtTrailType = ko.observable('exttrail');
                self.addExtTrailSize = ko.observable('500');
                self.DBLoginTitle = ko.observable();
                self.extStats = ko.observableArray([]);

                self.selectedMenuItem = ko.observable();
                self.ExtOpenTrans = ko.observableArray([]);

                function getOpenTrans() {
                    document.querySelector('#FetchOpenTrans').open();
                    self.ExtOpenTrans([]);
                    $.ajax({
                        url: self.DepName() + "/ggextshowtrans",
                        data: JSON.stringify({
                            extname: self.ExtName,
                        }),
                        type: 'POST',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            document.querySelector('#FetchOpenTrans').close();
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            self.ExtOpenTrans(data[0]);
                            document.querySelector('#FetchOpenTrans').close();
                            return self;
                        }
                    })
                }

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
                    if (self.selectedMenuItem() == 'extrpt' || self.selectedMenuItem() == 'extchk' || self.selectedMenuItem() == 'extstats' || self.selectedMenuItem() == 'extstartdef' || self.selectedMenuItem() == 'extstop' || self.selectedMenuItem() == 'extforcestop' || self.selectedMenuItem() == 'extkill' || self.selectedMenuItem() == 'cachemgr' || self.selectedMenuItem() == 'extstatus') {
                        document.querySelector('#Progress').open();
                        self.extStats([]);
                        self.ExtRpt([]);
                        self.delTitle('');
                        //console.log(self.selectedMenuItem())
                        $.ajax({
                            url: self.DepName() + "/ggextops",
                            data: JSON.stringify({
                                extname: self.ExtName,
                                extops: self.selectedMenuItem()
                            }),
                            type: 'POST',
                            dataType: 'json',
                            timeout: sessionStorage.getItem("timeInetrval"),
                            context: self,
                            error: function (xhr, textStatus, errorThrown) {
                                if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                    document.querySelector('#Progress').close();
                                    document.querySelector('#TimeoutManage').open();
                                }
                            },
                            success: function (data) {
                                document.querySelector('#Progress').close();
                                self.delTitle('View  Extract ' + self.ExtName + ' Info');
                                if (self.selectedMenuItem() == 'extstartdef' || self.selectedMenuItem() == 'extstop' || self.selectedMenuItem() == 'extforcestop' || self.selectedMenuItem() == 'extkill') {
                                    self.popUpResizeSM("ViewExtractRptDialog");
                                    document.querySelector('#ViewExtractRptDialog').open();
                                }
                                else if (self.selectedMenuItem() == 'extstats')
                                {
                                    self.delTitle('Extract ' + self.ExtName + ' Statistics');
                                    
                                    for (var key in data[2]){
                                        self.extStats.push({'TabName' : key ,'Inserts' : data[2][key]['Totalinserts'] ,'Updates' :  data[2][key]['Totalupdates'],'Deletes' : data[2][key]['Totaldeletes'] ,'Discards' : data[2][key]['Totaldiscards'] , 'Operations' : data[2][key]['Totaloperations']})
                                    }
                                    console.log(self.extStats())
                                    self.popUpResize("ViewExtractStatDialog");
                                    document.querySelector('#ViewExtractStatDialog').open();
                                }
                                else {
                                    self.popUpResize("ViewExtractRptDialog");
                                    document.querySelector('#ViewExtractRptDialog').open();
                                }
                                
                                self.ExtRpt(data[0]);
                                //console.log(self);
                                return self;

                            }

                        })
                    }


                    //Extract Start ATCSN  
                    else if (self.selectedMenuItem() == 'extatcsn') {
                        self.ExtATCSN();
                        document.querySelector('#ExtractATCSNDialog').open();

                    }
                    //Extract Start After CSN  
                    else if (self.selectedMenuItem() == 'extaftercsn') {
                        self.ExtAFTERCSN(0);
                        document.querySelector('#ExtractAFTERCSNDialog').open();

                    }
                    //Extract Upgrade to IE 
                    else if (self.selectedMenuItem() == 'upgie') {
                        self.DBLoginTitle('DBLogin for Extract ' + self.ExtName);
                        document.querySelector('#ExtLoginDialog').open();
                    }
                    //Extract Downgrade to CE 
                    else if (self.selectedMenuItem() == 'dwnie') {
                        self.DBLoginTitle('DBLogin for Extract ' + self.ExtName);
                        document.querySelector('#ExtLoginDialog').open();
                    }
                    //Extract Delete
                    else if (self.selectedMenuItem() == 'extdel') {
                        self.DBLoginTitle('DBLogin for Extract ' + self.ExtName);
                        document.querySelector('#ExtLoginDialog').open();
                    }
                    else if (self.selectedMenuItem() == 'extunreg') {
                        self.DBLoginTitle('DBLogin for Extract ' + self.ExtName);
                        document.querySelector('#ExtLoginDialog').open();
                    }
                    else if (self.selectedMenuItem() == 'extshowtrans') {
                        self.delTitle('Current Open Transactions for Extract ' + self.ExtName)
                        document.querySelector('#ViewExtOpenTransDialog').open();
                        getOpenTrans();
                    }
                    else if (self.selectedMenuItem() == 'exttraildel') {
                        self.delTitle('Delete Trail for Extract ' + self.ExtName);
                        document.querySelector('#GettingTrailName').open();
                        self.ExtRpt([]);
                        $.ajax({
                            url: self.DepName() + "/getexttrailname",
                            data: JSON.stringify({
                                extname: self.ExtName
                            }),
                            type: 'POST',
                            dataType: 'json',
                            timeout: sessionStorage.getItem("timeInetrval"),
                            context: self,
                            error: function (xhr, textStatus, errorThrown) {
                                if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                    document.querySelector('#GettingTrailName').close();
                                    document.querySelector('#TimeoutManage').open();
                                }
                            },
                            success: function (data) {
                                console.log(data[0])
                                document.querySelector('#GettingTrailName').close();
                                if (data[0].length > 0) {
                                    document.querySelector('#TrailForDelete').open();
                                    self.ExtRpt(data[0]);
                                }
                                else {
                                    document.querySelector('#TrailForDelete').open();
                                    self.ExtRpt('No Trails available to delete');
                                }

                                return self;
                            }
                        })
                    }

                    else if (self.selectedMenuItem() == 'exttrailadd') {
                        self.addExtTrailType('exttrail');
                        $.ajax({
                            url: self.DepName() + "/gggetrmttrail",
                            data: JSON.stringify({
                                extName: self.ExtName
                            }),
                            type: 'POST',
                            dataType: 'json',
                            timeout: sessionStorage.getItem("timeInetrval"),
                            context: self,
                            error: function (xhr, textStatus, errorThrown) {
                                if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                    document.querySelector('#Progress').close();
                                    document.querySelector('#TimeoutManage').open();
                                }
                            },
                            success: function (data) {
                                self.delTitle('ADD Remote Trail for ' + self.ExtName);
                                document.querySelector('#AddExtTrailDialog').open();
                                self.addExtTrailName(data[0]);
                                return self;

                            }

                        })
                    }
                    else if (self.selectedMenuItem() == 'extbegin') {
                        self.delTitle('Alter extract ' + self.ExtName);
                        document.querySelector('#ExtractBegin').open();
                    }
                    else if (self.selectedMenuItem() == 'extetroll') {
                        document.querySelector('#Progress').open();
                        $.ajax({
                            url: self.DepName() + "/ggextops",
                            data: JSON.stringify({
                                extname: self.ExtName,
                                extops: self.selectedMenuItem()
                            }),
                            type: 'POST',
                            dataType: 'json',
                            timeout: sessionStorage.getItem("timeInetrval"),
                            context: self,
                            error: function (xhr, textStatus, errorThrown) {
                                if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                    document.querySelector('#Progress').close();
                                    document.querySelector('#TimeoutManage').open();
                                }
                            },
                            success: function (data) {
                                document.querySelector('#Progress').close();
                                self.delTitle('Alter Extract ' + self.ExtName + ' ETROLLOVER');
                                self.popUpResizeSM("ViewExtractRptDialog");
                                document.querySelector('#ViewExtractRptDialog').open();
                                self.ExtRpt(data[0]);
                                return self;
                            }
                        })
                    }
                        }

                        self.extStatsDP =  ko.observable(new PagingDataProviderView(new ArrayDataProvider(self.extStats, { keyAttributes: 'TabName' })));

                self.DeleteTrailOKClose = function (event) {
                    document.querySelector('#TrailForDelete').close();
                    document.querySelector('#GettingTrailName').open();
                    $.ajax({
                        url: self.DepName() + "/ggextops",
                        data: JSON.stringify({
                            extname: self.ExtName,
                            trailname: self.ExtRpt(),
                            extops: self.selectedMenuItem()
                        }),
                        type: 'POST',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#GettingTrailName').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            document.querySelector('#GettingTrailName').close();
                            document.querySelector('#DeleteTrail').open();
                            self.ExtRpt(data[0]);
                            return self;
                        }
                    })
                };


                self.unregisterExtract = function (event) {
                    var valid = self._checkValidationGroup("ExtLoginDialogForm");
               if (valid) {
                    document.querySelector('#ExtLoginDialog').close();
                    document.querySelector('#Progress').open();
                    $.ajax({
                        url: self.DepName() + "/ggextops",
                        data: JSON.stringify({
                            extname: self.ExtName,
                            domain: self.selectedDomCategory(),
                            alias: self.selectedAliascategory(),
                            extops: self.selectedMenuItem()
                        }),
                        type: 'POST',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#Progress').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            document.querySelector('#Progress').close();
                            self.delTitle('Unregister  Extract ' + self.ExtName);
                            self.popUpResizeSM("ViewExtractRptDialog");
                            document.querySelector('#ViewExtractRptDialog').open();
                            self.ExtRpt(data[0]);
                            return self;
                        }
                    })
                }
                };


                self.AlterExtractBegin = function (data, event) {
                    var valid = self._checkValidationGroup("ExtractBeginForm");
               if (valid) {
                    document.querySelector('#ExtractBegin').close();
                    self.ExtRpt([]);
                    document.querySelector('#Progress').open();
                    $.ajax({
                        url: self.DepName() + "/ggextops",
                        data: JSON.stringify({
                            extname: self.ExtName,
                            domain: self.selectedDomCategory(),
                            alias: self.selectedAliascategory(),
                            beginmode: self.currentExtBeginMode(),
                            ctvalue: self.ctvalue(),
                            scnvalue: self.seqnovalue(),
                            extops: self.selectedMenuItem()
                        }),
                        type: 'POST',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#Progress').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            document.querySelector('#Progress').close();
                            self.popUpResizeSM("ViewExtractRptDialog");
                            document.querySelector('#ViewExtractRptDialog').open();
                            self.ExtRpt(data[0]);
                            return self;
                        }
                    })
                }
                }

                self.AddExtTrail = function (event, data) {
                    var valid = self._checkValidationGroup("AddExtTrailDialogFOrm");
                    if(valid){
                    document.querySelector('#GettingTrailName').open();
                    $.ajax({
                        url: self.DepName() + "/ggextops",
                        data: JSON.stringify({
                            extname: self.ExtName,
                            trailname: self.addExtTrailName(),
                            trailtype: self.addExtTrailType(),
                            trailsize: self.addExtTrailSize(),
                            extops: self.selectedMenuItem()
                        }),
                        type: 'POST',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#GettingTrailName').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            document.querySelector('#GettingTrailName').close();
                            document.querySelector('#ViewExtractRptDialog').open();
                            self.ExtRpt(data[0]);
                            return self;
                        }
                    })
                }
                };

                self.TrailOKClose = function (event) {
                    document.querySelector('#DeleteTrail').close();
                }

                self.showTransDP = new ArrayDataProvider(self.ExtOpenTrans, { keyAttributes: 'XID' });

                self.showTranscolumnArray = [
                    {
                        headerText: 'Transaction ID',
                        field: 'XID'
                    },
                    {
                        headerText: '# of Records',
                        field: 'Items'
                    },
                    {
                        headerText: 'Extract Name',
                        field: 'Extract'
                    },
                    {
                        headerText: 'Redo Thread',
                        field: 'Redo Thread'
                    },
                    {
                        headerText: 'Start Time',
                        field: 'Start Time'
                    },
                    {
                        headerText: 'SCN',
                        field: 'SCN'
                    },
                    {
                        headerText: 'Redo Sequence',
                        field: 'Redo Seq'
                    },
                    {
                        headerText: 'Redo RBA',
                        field: 'Redo RBA'
                    },
                    {
                        headerText: 'Status',
                        field: 'Status'
                    },
                    {
                        headerText: "Action",
                        headerStyle: "text-align: center;",
                        style: "text-align: center; padding-top: 0px; padding-bottom: 0px;",
                        template: "actionTemplate"
                    }
                ]


                self.extStatscolumnArray = [
                    {
                        headerText: 'Table Name',
                        field: 'TabName'
                    },
                    {
                        headerText: 'Total Inserts',
                        field: 'Inserts'
                    },
                    {
                        headerText: 'Total Updates',
                        field: 'Updates'
                    },
                    {
                        headerText: 'Total Deletes',
                        field: 'Deletes'
                    },
                    {
                        headerText: 'Total Discards',
                        field: 'Discards'
                    },
                    {
                        headerText: 'Total Operations',
                        field: 'Operations'
                    }
                ]


                self.actionListener = function (event) {
                    event.detail.originalEvent.stopPropagation();
                };
                self.xid = ko.observable();

                self.menuListener = function (event, context) {
                    self.xid('');
                    var rowIndex = self.ExtRpt.indexOf(context.row);
                    self.xid(context.row.XID);
                    if (event.target.value === 'skiptrans') {
                        self.ExtRpt.splice(rowIndex, 1);
                        self.ExtRpt([]);
                        $.ajax({
                            url: self.DepName() + "/ggextskiptrans",
                            data: JSON.stringify({
                                extname: self.ExtName,
                                xid: self.xid()
                            }),
                            type: 'POST',
                            dataType: 'json',
                            timeout: sessionStorage.getItem("timeInetrval"),
                            context: self,
                            error: function (xhr, textStatus, errorThrown) {
                                if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                    document.querySelector('#TimeoutManage').open();
                                }
                            },
                            success: function (data) {
                                document.querySelector('#ViewExtTransSkipRpt').open();
                                self.ExtRpt(data[0]);
                                return self;
                            }
                        })
                    }
                };


                self.ViewExtractRptOKClose = function (event) {
                    refresh();
                    document.querySelector('#ViewExtractRptDialog').close();
                    document.querySelector('#ExtLoginDialog').close();
                    document.querySelector('#AddExtTrailDialog').close();
                    document.querySelector('#DeleteConfirm').close();
                };


                self.ViewExtractStatRefresh  = function (event) {
                    document.querySelector('#Progress').open();
                    //console.log(self.selectedMenuItem())
                    $.ajax({
                        url: self.DepName() + "/ggextops",
                        data: JSON.stringify({
                            extname: self.ExtName,
                            extops: 'extstats'
                        }),
                        type: 'POST',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#Progress').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            document.querySelector('#Progress').close();
                            self.extStats([]);
                            for (var key in data[2]){
                                self.extStats.push({'TabName' : key ,'Inserts' : data[2][key]['Totalinserts'] ,'Updates' :  data[2][key]['Totalupdates'],'Deletes' : data[2][key]['Totaldeletes'] ,'Discards' : data[2][key]['Totaldiscards'] , 'Operations' : data[2][key]['Totaloperations']})
                            }
                            self.extStats.valueHasMutated();
                            return self;

               }
            })
        };


        self.ViewPumpStatRefresh  = function (event) {
            document.querySelector('#Progress').open();
            //console.log(self.selectedMenuItem())
            $.ajax({
                url: self.DepName() + "/ggextops",
                data: JSON.stringify({
                    extname: self.PmpName,
                    extops: 'extstats'
                }),
                type: 'POST',
                dataType: 'json',
                timeout: sessionStorage.getItem("timeInetrval"),
                context: self,
                error: function (xhr, textStatus, errorThrown) {
                    if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                        document.querySelector('#Progress').close();
                        document.querySelector('#TimeoutManage').open();
                    }
                },
                success: function (data) {
                    document.querySelector('#Progress').close();
                    self.extStats([]);
                    for (var key in data[2]){
                        self.extStats.push({'TabName' : key ,'Inserts' : data[2][key]['Totalinserts'] ,'Updates' :  data[2][key]['Totalupdates'],'Deletes' : data[2][key]['Totaldeletes'] ,'Discards' : data[2][key]['Totaldiscards'] , 'Operations' : data[2][key]['Totaloperations']})
                    }
                    self.extStats.valueHasMutated();
                    return self;

       }
    })
};


                self.ViewExtOpenTransrefresh = function (event) {
                    getOpenTrans();
                    self.ExtOpenTrans.valueHasMutated();
                }

                self.ViewExtTransSkipRptOKClose = function (event) {
                    getOpenTrans();
                    self.ExtOpenTrans.valueHasMutated();
                    document.querySelector('#ViewExtTransSkipRpt').close();
                };



                self.ExtStartATCSN = function (data, event) {
                    var valid = self._checkValidationGroup("ExtractATCSNDialogForm");
                if (valid) {
                        self.ExtRpt([]);
                        $.ajax({
                            url: self.DepName() + "/ggextops",
                            data: JSON.stringify({
                                extname: self.ExtName,
                                extatcsn: self.ExtATCSN(),
                                extops: self.selectedMenuItem()
                            }),
                            type: 'POST',
                            dataType: 'json',
                            timeout: sessionStorage.getItem("timeInetrval"),
                            context: self,
                            error: function (xhr, textStatus, errorThrown) {
                                if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                    document.querySelector('#ExtractATCSNDialog').close();
                                    document.querySelector('#TimeoutManage').open();
                                }
                            },
                            success: function (data) {
                                document.querySelector('#ViewExtractRptDialog').open();
                                self.ExtRpt(data[0]);
                                document.querySelector('#ExtractATCSNDialog').close();
                                return self;

                            }

                        })
                    }
                }



                self.ExtStartAFTERCSN = function (data, event) {
                    var valid = self._checkValidationGroup("ExtractAFTERCSNDialogForm");
                    if (valid) {
                    self.ExtRpt([]);
                    $.ajax({
                        url: self.DepName() + "/ggextops",
                        data: JSON.stringify({
                            extname: self.ExtName,
                            extaftercsn: self.ExtAFTERCSN(),
                            extops: self.selectedMenuItem()
                        }),
                        type: 'POST',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#ExtractAFTERCSNDialog').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            document.querySelector('#ViewExtractRptDialog').open();
                            self.ExtRpt(data[0]);
                            document.querySelector('#ExtractAFTERCSNDialog').close();
                            return self;

                        }

                    })
                }
                }


                self.ExtUpgTOIE = function (data, event) {
                    var valid = self._checkValidationGroup("ExtLoginDialogForm");
                if (valid) {
                    self.ExtRpt([]);
                    document.querySelector('#UpgExtractDialog').open();
                    $.ajax({
                        url: self.DepName() + "/ggextops",
                        data: JSON.stringify({
                            extname: self.ExtName,
                            domain: self.selectedDomCategory(),
                            alias: self.selectedAliascategory(),
                            extops: self.selectedMenuItem()
                        }),
                        type: 'POST',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#UpgExtractDialog').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            document.querySelector('#UpgExtractDialog').close();
                            document.querySelector('#ViewExtractRptDialog').open();
                            self.ExtRpt(data[0]);

                            return self;
                        }

                    })
                }
                }


                self.ExtDwnTOCE = function (data, event) {
                    var valid = self._checkValidationGroup("ExtLoginDialogForm");
               if (valid) {
                    self.ExtRpt([]);
                    document.querySelector('#UpgExtractDialog').open();
                    $.ajax({
                        url: self.DepName() + "/ggextops",
                        data: JSON.stringify({
                            extname: self.ExtName,
                            domain: self.selectedDomCategory(),
                            alias: self.selectedAliascategory(),
                            extops: self.selectedMenuItem()
                        }),
                        type: 'POST',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#UpgExtractDialog').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            document.querySelector('#UpgExtractDialog').close();
                            document.querySelector('#ViewExtractRptDialog').open();
                            self.ExtRpt(data[0]);

                            return self;
                        }

                    })
                }
                }



                self.DelExt = function (data, event) {
                    var valid = self._checkValidationGroup("ExtLoginDialogForm");
                    if (valid) {
                    document.querySelector('#Progress').open();
                    self.ExtRpt([]);
                    $.ajax({
                        url: self.DepName() + "/ggextops",
                        data: JSON.stringify({
                            extname: self.ExtName,
                            domain: self.selectedDomCategory(),
                            alias: self.selectedAliascategory(),
                            extops: self.selectedMenuItem()
                        }),
                        type: 'POST',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#Progress').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            self.selectedDomCategory('');
                            self.selectedAliascategory('');
                            document.querySelector('#Progress').close();
                            self.delTitle('Deleted Extract ' + self.ExtName)
                            document.querySelector('#ViewExtractRptDialog').open();
                            self.ExtRpt(data[0]);
                            return self;
                        }

                    })
                }
                }

                //**************************************************************************** */            
                // Pump Functions
                //**************************************************************************** */

                self.PmpRpt = ko.observableArray([]);
                self.delTitle = ko.observable();

                self.addRmtTrailName = ko.observable();
                self.addRmtTrailType = ko.observable('rmttrail');
                self.addRmtTrailSize = ko.observable(500);

                self.selectedPmpMenuItem = ko.observable('');

                self.menuPmpItemAction = function (event) {
                    self.selectedPmpMenuItem(event.target.value);
                    if (self.selectedPmpMenuItem() == 'extrpt' || self.selectedPmpMenuItem() == 'extchk' || self.selectedPmpMenuItem() == 'extstats' || self.selectedPmpMenuItem() == 'extstartdef' || self.selectedPmpMenuItem() == 'extstop' || self.selectedPmpMenuItem() == 'extforcestop' || self.selectedPmpMenuItem() == 'extkill' || self.selectedPmpMenuItem() == 'cachemgr' || self.selectedPmpMenuItem() == 'extstatus') {
                        document.querySelector('#Progress').open();
                        self.extStats([]);
                        self.PmpRpt([]);
                        self.delTitle('');
                        $.ajax({
                            url: self.DepName() + "/ggextops",
                            data: JSON.stringify({
                                extname: self.PmpName,
                                extops: self.selectedPmpMenuItem()
                            }),
                            type: 'POST',
                            dataType: 'json',
                            timeout: sessionStorage.getItem("timeInetrval"),
                            context: self,
                            error: function (xhr, textStatus, errorThrown) {
                                if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                    document.querySelector('#Progress').close();
                                    document.querySelector('#TimeoutManage').open();
                                }
                            },
                            success: function (data) {
                                document.querySelector('#Progress').close();


                                if (self.selectedPmpMenuItem() == 'extstartdef' || self.selectedPmpMenuItem() == 'extstop' || self.selectedPmpMenuItem() == 'extforcestop' || self.selectedPmpMenuItem() == 'extkill') {
                                    self.popUpResizeSM("ViewPumpRptDialog");
                                    self.delTitle('View Pump ' + self.PmpName + ' Info');

                                document.querySelector('#ViewPumpRptDialog').open();
                                } 
                                
                                else if (self.selectedPmpMenuItem() == 'extstats')
                                {
                                    self.delTitle('Extract ' + self.PmpName + ' Statistics');
                                    
                                    for (var key in data[2]){
                                        self.extStats.push({'TabName' : key ,'Inserts' : data[2][key]['Totalinserts'] ,'Updates' :  data[2][key]['Totalupdates'],'Deletes' : data[2][key]['Totaldeletes'] ,'Discards' : data[2][key]['Totaldiscards'] , 'Operations' : data[2][key]['Totaloperations']})
                                    }
                                    self.popUpResize("ViewExtractStatDialog");
                                    document.querySelector('#ViewExtractStatDialog').open();
                                }

                                else {
                                    self.delTitle('View Pump ' + self.PmpName + ' Info');
                                    self.popUpResize("ViewPumpRptDialog");
                                document.querySelector('#ViewPumpRptDialog').open();
                                }

                                self.PmpRpt(data[0]);
                                //console.log(self);
                                return self;
                            }
                        })
                    }
                    //Extract Start ATCSN  
                    else if (self.selectedPmpMenuItem() == 'pmpatcsn') {
                        self.ExtATCSN();
                        document.querySelector('#ExtractATCSNDialog').open();

                    }
                    //Extract Start After CSN  
                    else if (self.selectedPmpMenuItem() == 'extaftercsn') {
                        self.ExtAFTERCSN(0);
                        document.querySelector('#ExtractAFTERCSNDialog').open();

                    }
                    else if (self.selectedPmpMenuItem() == 'exttrailadd') {
                        $.ajax({
                            url: self.DepName() + "/gggetrmttrail",
                            data: JSON.stringify({
                                extName: self.PmpName
                            }),
                            type: 'POST',
                            dataType: 'json',
                            timeout: sessionStorage.getItem("timeInetrval"),
                            context: self,
                            error: function (xhr, textStatus, errorThrown) {
                                if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                    document.querySelector('#Progress').close();
                                    document.querySelector('#TimeoutManage').open();
                                }
                            },
                            success: function (data) {
                                self.delTitle('');
                                self.delTitle('ADD Remote Trail for ' + self.PmpName);
                                document.querySelector('#AddRmtTrailDialog').open();
                                self.addRmtTrailName(data[0]);
                                return self;

                            }

                        })

                    }
                    else if (self.selectedPmpMenuItem() == 'extdelrmt') {
                        self.delTitle('Delete Remote Trail of Pump ' + self.PmpName + ' ?')
                        document.querySelector('#DeleteConfirm').open();
                    }

                    else if (self.selectedPmpMenuItem() == 'pmpdel') {
                        self.delTitle('Delete Pump ' + self.PmpName + ' ?')
                        document.querySelector('#DeleteConfirm').open();

                    }
                    else if (self.selectedPmpMenuItem() == 'extbegin') {
                        self.delTitle('Alter Pump ' + self.PmpName)
                        document.querySelector('#PumpBegin').open();
                        self.currentPmpBeginMode('pmpextseqno');
                    }
                    else if (self.selectedPmpMenuItem() == 'extetroll') {
                        self.ExtRpt([]);
                        document.querySelector('#Progress').open();
                        $.ajax({
                            url: self.DepName() + "/ggextops",
                            data: JSON.stringify({
                                extname: self.PmpName,
                                extops: self.selectedPmpMenuItem()
                            }),
                            type: 'POST',
                            dataType: 'json',
                            timeout: sessionStorage.getItem("timeInetrval"),
                            context: self,
                            error: function (xhr, textStatus, errorThrown) {
                                if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                    document.querySelector('#Progress').close();
                                    document.querySelector('#TimeoutManage').open();
                                }
                            },
                            success: function (data) {
                                document.querySelector('#Progress').close();
                                self.delTitle('Alter Extract ' + self.PmpName + ' ETROLLOVER');
                                self.popUpResizeSM("ViewExtractRptDialog");
                                document.querySelector('#ViewExtractRptDialog').open();
                                self.ExtRpt(data[0]);
                                return self;
                            }
                        })
                    }

                }
                self.DeleteRMTOKClose = function (data, event) {
                    document.querySelector('#DeleteConfirm').close();
                    document.querySelector('#Progress').open();
                    self.PmpRpt([]);
                    $.ajax({
                        url: self.DepName() + "/ggdelrmt",
                        data: JSON.stringify({
                            pmpName: self.PmpName
                        }),
                        type: 'POST',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#Progress').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            document.querySelector('#Progress').close();
                            document.querySelector('#ViewPumpRptDialog').open();

                            self.PmpRpt(data[0]);

                            return self;

                        }

                    })
                }

                self.AlterPumpBegin = function (event, data) {
                    var valid = self._checkValidationGroup("PumpBeginForm");
               if (valid) {
                    document.querySelector('#PumpBegin').close();
                    document.querySelector('#Progress').open();
                    $.ajax({
                        url: self.DepName() + "/ggextops",
                        data: JSON.stringify({
                            extname: self.PmpName,
                            seqnovalue: self.seqnovalue(),
                            rbavalue: self.rbavalue(),
                            beginmode :  self.currentPmpBeginMode(),
                            extops: self.selectedPmpMenuItem()
                        }),
                        type: 'POST',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#Progress').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            document.querySelector('#Progress').close();
                            self.popUpResizeSM("ViewExtractRptDialog");
                            document.querySelector('#ViewExtractRptDialog').open();
                            self.ExtRpt(data[0]);
                            return self;
                        }
                    })
                }
                };


                self.AddRmtTrail = function (event, data) {
                    var valid = self._checkValidationGroup("AddRmtTrailDialogForm");
               if (valid) {
                    document.querySelector('#AddRmtTrailDialog').close();
                    document.querySelector('#GettingTrailName').open();
                    $.ajax({
                        url: self.DepName() + "/ggextops",
                        data: JSON.stringify({
                            extname: self.PmpName,
                            trailname: self.addRmtTrailName(),
                            trailtype: self.addRmtTrailType(),
                            trailsize: self.addRmtTrailSize(),
                            extops: self.selectedPmpMenuItem()
                        }),
                        type: 'POST',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#GettingTrailName').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            document.querySelector('#GettingTrailName').close();
                            self.popUpResizeSM("ViewExtractRptDialog");
                            document.querySelector('#ViewExtractRptDialog').open();
                            self.ExtRpt(data[0]);
                            return self;
                        }
                    })
                }
                };


                self.DelPmp = function (event, data) {
                    document.querySelector('#DeleteConfirm').close();
                    document.querySelector('#Progress').open();
                    self.selectedMenuItem('');
                    self.ExtRpt([]);
                    $.ajax({
                        url: self.DepName() + "/ggextops",
                        data: JSON.stringify({
                            extname: self.PmpName,
                            extops: self.selectedPmpMenuItem()
                        }),
                        type: 'POST',
                        dataType: 'json',
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#Progress').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            self.delTitle('Deleted Pump ' + self.PmpName);
                            document.querySelector('#Progress').close();
                            document.querySelector('#ViewExtractRptDialog').open();
                            self.ExtRpt(data[0]);
                            return self;
                        }

                    })
                }


                self.ViewPumpRptOKClose = function (event) {
                    document.querySelector('#ViewPumpRptDialog').close();
                    refresh();
                };

                //**************************************************************************** */            
                // Replicat Functions
                //**************************************************************************** */


                self.RepRpt = ko.observableArray([]);
                self.selectedRepMenuItem = ko.observable('');

                self.menuRepItemAction = function (event) {
                    self.selectedRepMenuItem(event.target.value);
                    //Replicat Functions
                    if (self.selectedRepMenuItem() == 'reprpt' || self.selectedRepMenuItem() == 'repstats' || self.selectedRepMenuItem() == 'repchk' || self.selectedRepMenuItem() == 'repstartdef' || self.selectedRepMenuItem() == 'repskiptrans' || self.selectedRepMenuItem() == 'repnofilterdup' || self.selectedRepMenuItem() == 'repstop' || self.selectedRepMenuItem() == 'repforcestop' || self.selectedRepMenuItem() == 'repkill'
                    ) {
                        document.querySelector('#Progress').open();
                        self.delTitle('');
                        self.RepRpt([]);
                        $.ajax({
                            url: self.DepName() + "/ggrepops",
                            data: JSON.stringify({
                                repops: self.selectedRepMenuItem(),
                                repname: self.RepName
                            }),
                            type: 'POST',
                            dataType: 'json',
                            timeout: sessionStorage.getItem("timeInetrval"),
                            context: self,
                            error: function (xhr, textStatus, errorThrown) {
                                if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                    document.querySelector('#Progress').close();
                                    document.querySelector('#TimeoutManage').open();
                                }
                            },
                            success: function (data) {
                                document.querySelector('#Progress').close();
                                self.delTitle('View  Replicat ' + self.RepName + ' Info');
                                self.RepRpt(data[0]);

                                if (self.selectedRepMenuItem() == 'repstartdef' || self.selectedRepMenuItem() == 'repstop' || self.selectedRepMenuItem() == 'repforcestop' || self.selectedRepMenuItem() == 'repkill') {
                                    self.popUpResizeSM("ViewReplicatRptDialog");
                                } else {
                                    self.popUpResize("ViewReplicatRptDialog");
                                }
                                document.querySelector('#ViewReplicatRptDialog').open();
                                //console.log(self);
                                return self;
                            }
                        })
                    }
                    else if (self.selectedRepMenuItem() == 'repatcsn') {
                        self.RepATCSN('');
                        document.querySelector('#ReplicatATCSNDialog').open();
                    }
                    else if (self.selectedRepMenuItem() == 'repaftercsn') {
                        self.RepATCSN('');
                        document.querySelector('#ReplicatAFTERCSNDialog').open();
                    }

                    else if (self.selectedRepMenuItem() == 'repdel' || self.selectedRepMenuItem() == 'upgir' || self.selectedRepMenuItem() == 'dwnir') {
                        self.DBLoginTitle('DBLogin for Replicat ' + self.RepName);
                        document.querySelector('#RepLoginDialog').open();
                    }
                    else if (self.selectedRepMenuItem() == 'repbegin') {
                        document.querySelector('#ReplicatBegin').open();
                    }

                }
                self.DelRep = function (data, event) {
                    var valid = self._checkValidationGroup("RepLoginDialogForm");
                     if (valid) {
                    document.querySelector('#RepLoginDialog').close();
                    self.RepRpt([]);
                    document.querySelector('#Progress').open();
                    $.ajax({
                        url: self.DepName() + "/ggrepops",
                        data: JSON.stringify({
                            repname: self.RepName,
                            domain: self.selectedDomCategory(),
                            alias: self.selectedAliascategory(),
                            repops: self.selectedRepMenuItem()
                        }),
                        type: 'POST',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#RepProgress').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            document.querySelector('#Progress').close();
                            self.RepRpt(data[0]);
                            self.delTitle('Deleted Replicat ' + self.RepName);
                            document.querySelector('#ViewReplicatRptDialog').open();
                            //console.log(self);
                            return self;
                        }
                    })
                }
                }

                self.RepStartATCSN = function (data, event) {
                    var valid = self._checkValidationGroup("ReplicatATCSNDialogForm");
                    if (valid) {
                    document.querySelector('#ReplicatATCSNDialog').close();
                    self.RepRpt([]);
                    document.querySelector('#Progress').open();
                    $.ajax({
                        url: self.DepName() + "/ggrepops",
                        data: JSON.stringify({
                            repname: self.RepName,
                            domain: self.selectedDomCategory(),
                            alias: self.selectedAliascategory(),
                            repatcsn: self.RepATCSN(),
                            repops: self.selectedRepMenuItem()
                        }),
                        type: 'POST',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#Progress').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            document.querySelector('#Progress').close();
                            self.RepRpt(data[0]);
                            document.querySelector('#ViewReplicatRptDialog').open();
                            //console.log(self);
                            return self;
                        }
                    })
                }
                }


                self.RepStartAFTERCSN = function (data, event) {
                    var valid = self._checkValidationGroup("ReplicatAFTERCSNDialogForm");
                    if (valid) {
                    document.querySelector('#ReplicatAFTERCSNDialog').close();
                    self.RepRpt([]);
                    document.querySelector('#Progress').open();
                    $.ajax({
                        url: self.DepName() + "/ggrepops",
                        data: JSON.stringify({
                            repname: self.RepName,
                            domain: self.selectedDomCategory(),
                            alias: self.selectedAliascategory(),
                            repaftercsn: self.RepAFTERCSN(),
                            repops: self.selectedRepMenuItem()
                        }),
                        type: 'POST',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#Progress').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            document.querySelector('#Progress').close();
                            self.RepRpt(data[0]);
                            document.querySelector('#ViewReplicatRptDialog').open();
                            //console.log(self);
                            return self;
                        }
                    })
                }
                }

                self._checkValidationGroup = (value) => {
                    var tracker = document.getElementById(value);
                    if (tracker.valid === "valid") {
                        return true;
                    }
                    else {
                       
                        tracker.showMessages();
                        tracker.focusOn("@firstInvalidShown");
                        return false;
                    }
                };

                self.RepUpgradetoIntegrated = function (data, event) {
                    var valid = self._checkValidationGroup("RepLoginDialogForm");
                    if (valid) {
                    document.querySelector('#RepLoginDialog').close();
                    self.RepRpt([]);
                    document.querySelector('#Progress').open();
                    $.ajax({
                        url: self.DepName() + "/ggrepops",
                        data: JSON.stringify({
                            repname: self.RepName,
                            domain: self.selectedDomCategory(),
                            alias: self.selectedAliascategory(),
                            repops: self.selectedRepMenuItem()
                        }),
                        type: 'POST',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#RepProgress').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            document.querySelector('#Progress').close();
                            self.RepRpt(data[0]);
                            document.querySelector('#ViewReplicatRptDialog').open();
                            //console.log(self);
                            return self;
                        }
                    })
                }
                }

                self.RepDowngradetoClassic = function (data, event) {
                    var valid = self._checkValidationGroup("RepLoginDialogForm");
               if (valid) {
                    document.querySelector('#RepLoginDialog').close();
                    self.RepRpt([]);
                    document.querySelector('#Progress').open();
                    $.ajax({
                        url: self.DepName() + "/ggrepops",
                        data: JSON.stringify({
                            repname: self.RepName,
                            domain: self.selectedDomCategory(),
                            alias: self.selectedAliascategory(),
                            chktbl: self.currentChkptTbl(),
                            repops: self.selectedRepMenuItem()
                        }),
                        type: 'POST',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#RepProgress').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            document.querySelector('#Progress').close();
                            self.RepRpt(data[0]);
                            document.querySelector('#ViewReplicatRptDialog').open();
                            //console.log(self);
                            return self;
                        }
                    })
               }
                }

                self.AlterReplicatBegin = function (data, event) {
                    var valid = self._checkValidationGroup("ReplicatBeginForm");
                    if (valid) {
                    document.querySelector('#ReplicatBegin').close();
                    self.RepRpt([]);
                    document.querySelector('#Progress').open();
                    $.ajax({
                        url: self.DepName() + "/ggrepops",
                        data: JSON.stringify({
                            repname: self.RepName,
                            domain: self.selectedDomCategory(),
                            alias: self.selectedAliascategory(),
                            beginmode: self.currentbeginmode(),
                            ctvalue: self.ctvalue(),
                            seqnovalue: self.seqnovalue(),
                            rbavalue: self.rbavalue(),
                            repops: self.selectedRepMenuItem()
                        }),
                        type: 'POST',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if (textStatus == 'TimeoutManage' || textStatus == 'error') {
                                document.querySelector('#Progress').close();
                                document.querySelector('#TimeoutManage').open();
                            }
                        },
                        success: function (data) {
                            document.querySelector('#Progress').close();
                            self.RepRpt(data[0]);
                            document.querySelector('#ViewReplicatRptDialog').open();
                            //console.log(self);
                            return self;
                        }
                    })
                }
                }

                self.ViewReplicatRptOKClose = function (event) {
                    refresh();
                    document.querySelector('#ViewReplicatRptDialog').close();
                    document.querySelector('#RepLoginDialog').close();
                    document.querySelector('#Progress').close();
                };



                self.connected = function () {
                    if (sessionStorage.getItem("userName") == null) {
                        self.router.go('signin');
                    }
                    else {
                        app.onAppSuccess();
                        getDomains();
                        refresh();
                        monAll = setInterval(refresh, 20000);

                    }
                }

                /**
                 * Optional ViewModel method invoked after the View is disconnected from the DOM.
                 */
                self.disconnected = function () {
                    // Implement if needed
                    clearInterval(monAll);
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
        return ManageViewModel;
    }
);
