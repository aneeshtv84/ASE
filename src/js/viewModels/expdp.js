define(['knockout', 'jquery','appController',  'ojs/ojasyncvalidator-regexp', 'ojs/ojconverterutils-i18n', 'ojs/ojconverter-datetime', 
'ojs/ojconverter-number',"ojs/ojpagingdataproviderview",'ojs/ojarraydataprovider',"ojs/ojlistdataproviderview","ojs/ojkeyset", 
'ojs/ojknockout', 'ojs/ojtrain', 'ojs/ojradioset', 'ojs/ojbutton', 'ojs/ojlabelvalue', 'ojs/ojdatetimepicker', 'ojs/ojlabel',"ojs/ojlistview", "ojs/ojlistitemlayout",
 'ojs/ojformlayout', 'ojs/ojinputtext', 'ojs/ojselectsingle', 'ojs/ojinputnumber', 'ojs/ojvalidationgroup', 'ojs/ojselectcombobox', 
 'ojs/ojdialog', 'ojs/ojswitch','ojs/ojcheckboxset','ojs/ojprogress-bar','ojs/ojtable','ojs/ojhighlighttext',"ojs/ojpagingcontrol","ojs/ojgauge"],
        function (ko, $,app,AsyncRegExpValidator, ConverterUtilsI18n, DateTimeConverter, NumberConverter, PagingDataProviderView,ArrayDataProvider,ListDataProviderView,ojkeyset_1) {

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
                self.dbTgtDetList =  ko.observableArray([]);
                self.onepDepList = ko.observableArray([]);
                self.gatherMeta = ko.observable(false);
                self.deferStart = ko.observable(false);
                self.ApplyMetaButtonVal = ko.observable(true);
                self.OPError = ko.observableArray([]);

                self.LoadOption = ko.observable('file');
                self.SrcOnePDepName = ko.observable();
                self.TgtOnePDepName = ko.observable();

                self.onepUser = ko.observable();
                self.onepPasswd = ko.observable();

                self.repType = ko.observableArray([]);
                self.currentRepType = ko.observable('parallel');
                self.paramValue = ko.observable("text area value");
                self.currentPassThru = ko.observable('passthru');
                self.rmtHostName = ko.observable();
                self.rmtMgrPort = ko.observable();
                self.ButtonVal = ko.observable();
                self.textVal = ko.observable(true);
                self.BtnExprt = ko.observable(true);
                self.BtnImprt = ko.observable(true);
                self.Btnexprtcheck = ko.observable(true);
                self.Btnimprttcheck = ko.observable(true);
                self.BtnCreateJOb = ko.observable(true);
                self.pdbList = ko.observable();
                self.reMap = ko.observable(true);

                self.filter = ko.observable();

                self.currentLoadOption = ko.observable('auto');

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

                self.schemaList = ko.observableArray([]);

                self.LoadName = ko.observable();

                self.ZDTChk = ko.observable(false);
                 self.currentRawValue = ko.observable("");

                

                self.CDBCheck =  ko.observable();
                self.SRConepDepUrl = ko.observable();
                self.TGTonepDepUrl = ko.observable();
                self.CancelBehaviorOpt = ko.observable('icon');
                self.ButtonChltbl = ko.observable(true);
                self.remapSchema = ko.observableArray([]);
                self.reMapSchemaVal = ko.observable(true);
                self.reMapSchemaNameList = ko.observableArray([]);
                self.reMapSchemaNameListDisp = ko.observableArray([]);
                self.remapTgtSchemaNames = ko.observable();
                self.remapTableSpaces = ko.observableArray(["no"]);
                self.remapTablespaceVal = ko.observable(true);
                self.reMapTablespaceList = ko.observableArray([]);
                self.reMapTablespaceListDisp = ko.observableArray([]);
                self.remapTgtTableSpaceNames = ko.observable();
                self.dbMainVersion  = ko.observable();
                self.dbMinorVersion = ko.observable();
                
////


self.schemaCheckboxListener = function (event) {
   if(self.remapSchema()[0] == "yes"){
       self.reMapSchemaVal(false);
       self.reMapSchemaNameListDisp([]);
       self.remapTgtSchemaNames('');
   }else{
    self.reMapSchemaVal(true);
    self.reMapSchemaNameListDisp([]);
    self.remapTgtSchemaNames('');
    self.remapSchema(["no"])
   }
  };

  self.tablespaceCheckboxListener = function (event) {
    if(self.remapTableSpaces()[0] == "yes"){
        self.remapTablespaceVal(false);
        self.reMapTablespaceList([]);
        self.remapTgtTableSpaceNames('');
    }else{
     self.remapTablespaceVal(true);
     self.reMapTablespaceList([]);
     self.remapTgtTableSpaceNames('');
     self.remapTableSpaces(["no"])
    }
    $.ajax({
        url: self.DepName() + "/tablespaceimpdp",
        type: 'POST',
        dataType: 'json',
        data: JSON.stringify({
            jobName : self.LoadName(),
            srcdbName : self.SRCcurrentPDB(),
            tgtdbName : self.TGTcurrentPDB(),
            cdbCheck : self.CDBCheck(),
            pdbName : self.pdbList(),
            schemas : self.schemaList()
        }),
        timeout: sessionStorage.getItem("timeInetrval"),
        context: self,
        error: function (xhr, textStatus, errorThrown) {
            if(textStatus == 'timeout' || textStatus == 'error'){
                document.querySelector('#TimeoutInLoad').open();
            }
        },
        success: function (data) {
            for (var i = 0; i < data[0].length; i++) {   
                    self.reMapTablespaceList.push({'label' : data[0][i].TABLESPACE_NAME , 'value' : data[0][i].TABLESPACE_NAME});
            }
            self.reMapTablespaceList.valueHasMutated();
            // console.log(self.reMapTablespaceList())
          return self;
        }
    })

   };
   self.reMapTablespaceListDP = new ArrayDataProvider(self.reMapTablespaceList, {keyAttributes: 'value'});     


self.DBDet = ko.observableArray([]);
self.currentDB = ko.observable();

function getDB(url) {
    if(url){
    self.DBDet([]);
    $.ajax({
        url: url + "/dbdet",
        type: 'GET',
        dataType: 'json',
        timeout: sessionStorage.getItem("timeInetrval"),
        context: self,
        error: function (xhr, textStatus, errorThrown) {
            if(textStatus == 'timeout' || textStatus == 'error'){
                document.querySelector('#TimeoutInLoad').open();
            }
        },
        success: function (data) {
            for (var i = 0; i < data[0].length; i++) {
                self.DBDet.push({'value' : data[0][i].dbname, 'label' : data[0][i].dbname});
        }

        return self;
    }
    })

    }
    
}

self.DBDetDP = new ArrayDataProvider(self.DBDet, {keyAttributes: 'value'});  
 
self.TgtDBDet = ko.observableArray([]);

function getTgtDB(url) {
    if(url){
    self.TgtDBDet([]);
    $.ajax({
        url: url + "/dbdet",
        type: 'GET',
        dataType: 'json',
        timeout: sessionStorage.getItem("timeInetrval"),
        context: self,
        error: function (xhr, textStatus, errorThrown) {
            if(textStatus == 'timeout' || textStatus == 'error'){
                document.querySelector('#TimeoutInLoad').open();
            }
        },
        success: function (data) {
            for (var i = 0; i < data[0].length; i++) {
                self.TgtDBDet.push({'value' : data[0][i].dbname, 'label' : data[0][i].dbname});
        }

        return self;
    }
    })

    }
    
}


self.TgtDBDetDP = new ArrayDataProvider(self.TgtDBDet, {keyAttributes: 'value'});  

                

                self.SelectSRCDeployment = (event,data) =>{
                    if(self.SrcOnePDepName()){
                    self.SRConepDepUrl('');
                    $.ajax({
                      url: self.DepName() + "/onepdepurl",
                      type: 'POST',
                      data: JSON.stringify({
                        dep: self.SrcOnePDepName()
                    }),
                      dataType: 'json',
                      timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#TimeoutInLoad').open();
                            }
                        },
                      success: function (data) {
                          self.selectedSRCDomCategory('');
                          self.SRCcurrentPDB('');
                          self.pdbList('');
                          self.schemaList([]);
                          self.SRConepDepUrl(data[0]);
                          getDB(data[0]);
                          if(self.ZDTChk() == true){
                          getSrcDomains();
                          }
                          return self;
                      }
                  })
                    }
                 };


                 self.SelectTGTDeployment = (event,data) =>{
                     if (self.TgtOnePDepName()){
                    self.TGTonepDepUrl('');
                    $.ajax({
                      url: self.DepName() + "/onepdepurl",
                      type: 'POST',
                      data: JSON.stringify({
                        dep: self.TgtOnePDepName()
                    }),
                      dataType: 'json',
                      timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#TimeoutInLoad').open();
                            }
                        },
                      success: function (data) {
                          self.selectedTGTDomCategory('');
                          self.TGTcurrentPDB('');
                          self.TGTonepDepUrl(data[0]);
                        //   console.log(self.TGTonepDepUrl())
                          getTgtDB(data[0]);
                           if(self.ZDTChk() == true){
                           getTgtDomains();
                           }
                          return self;
                      }
                  })
                }
                 };

                 self.ExtPrmList = ko.observableArray([]);
                self.ExtTrailName = ko.observable();
                self.queryExtPrm =    function(event,data) {
                    self.ExtPrmList([]);
                    self.ExtTrailName('');
                    $.ajax({
                        url: self.DepName() + "/gggetextprm",
                        type: 'POST',
                        dataType: 'json',
                        data: JSON.stringify({
                            currentextname : self.CurrentExtName()
                        }),
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#TimeoutInLoad').open();
                            }
                        },
                        success: function (data) {
                                    self.ExtPrmList(data[0]);
                                    self.ExtTrailName(data[1]);
                          return self;
                        }
                    })
                }




                self.lmDictSCN = ko.observable(' ');


                self.getItemText = function (itemContext) {
                    return itemContext.data.FIRST_CHANGE;
                  };

               self.tableColumns = [
                    {"headerText": "SCN", "field": "FIRST_CHANGE","template": "cellTemplate"},
                    {"headerText": "Time", "field": "FIRST_TIME","template": "cellTemplate"}
                  ];
              
                  self.regVal = ko.observable('now');
                  self.regOptions = [
                    { id: 'now', value: 'now', label: 'Now' },
                    { id: 'existscn', value: 'existscn', label: 'Existing Dictionary' }
                  ];

                  self.lmShareOpt = ko.observableArray([
                    {label: 'AUTOMATIC', value: 'AUTOMATIC'},
                    {label: 'NONE', value: 'NONE'},
                    {label: 'EXTRACT', value: 'EXTRACT'}
                ]);
                self.lmShareOptDP = new ArrayDataProvider(self.lmShareOpt, {keyAttributes: 'value'});     

                self.currentShareOpt = ko.observable('NONE');


                self.PDBName = ko.observableArray([]);


                
                self.CurrentExtName = ko.observable();
                self.ExtList = ko.observableArray([]);

                function getExtTrails() {
                    self.CurrentExtName('');
                    self.ExtList([]);
                    $.ajax({
                        url: self.DepName() + "/gggetexttrail",
                        type: 'GET',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#TimeoutInLoad').open();
                            }
                        },
                        success: function (data) {
                            for (var i = 0; i < data[0].length; i++) {           
                                self.ExtList.push({'label' : data[0][i].label, 'value' : data[0][i].label});
                            }
                            return self;
                        }
                    })
                }

                self.ExtListDP = new ArrayDataProvider(self.ExtList, {keyAttributes: 'value'});


self.currentExtOptParamList = ko.computed(function() {
    var currentExtOptParamList='';
    if(self.ExtoptParam()) {
        for(var i=0;i< self.ExtoptParam().length;i++){
            currentExtOptParamList = currentExtOptParamList + self.ExtoptParam()[i]  +'\n'
        }
       return currentExtOptParamList;
    }
    else
    {
        return '';
        
    }
    });


    self.currentRepOptParamList = ko.computed(function() {
        var currentRepOptParamList ='';
        if(self.RepoptParam()) {
        for(var i=0;i< self.RepoptParam().length;i++){
            currentRepOptParamList = currentRepOptParamList + self.RepoptParam()[i]  +'\n'
        }
           return currentRepOptParamList;
    }
       else
           {
               return '';
               
           }          
        });

    self.ExtPrmList1 = ko.computed(function() {
        if(self.ExtPrmList()) {
           return self.ExtPrmList().join('');
        }
        else
        {
            return '';
            
        }
        });


                self.currentExtType = ko.observable('SOURCEISTABLE');
                     
                     
                self.extType = ko.observableArray([
                    {label: 'Initial Load Extract', value: 'SOURCEISTABLE'},
                    {label: 'Initial Load Replicat', value: 'ILR'}
                ]);


                self.contentsOptions = ko.observableArray([
                    {label: 'ALL', value: 1 },
                    {label: 'METADATA_ONLY', value: 1 },
                    {label: 'DATA_ONLY', value: 0 }
                ]);

                self.contentsOptionsDP = new ArrayDataProvider(self.contentsOptions, {keyAttributes: 'value'});

                self.compressionOptions = ko.observableArray([
                    {label: 'METADATA_ONLY', value: 'METADATA_ONLY'},
                    {label: 'DATA_ONLY', value: 'DATA_ONLY'},
                    {label: 'ALL', value: 'ALL'}
                ]);

                self.compressionOptionsDP = new ArrayDataProvider(self.compressionOptions, {keyAttributes: 'value'});
                self.compressionAlgo = ko.observableArray([
                    {label: 'BASIC', value: 'BASIC'},
                    {label: 'LOW', value: 'LOW'},
                    {label: 'MEDIUM', value: 'MEDIUM'},
                    {label: 'HIGH', value: 'HIGH'}
                ]);
                self.compressionAlgoDP = new ArrayDataProvider(self.compressionAlgo, {keyAttributes: 'value'});
                self.parallelism = ko.observableArray([
                    {label: '1', value: '1'},
                    {label: '2', value: '2'},
                    {label: '3', value: '3'},
                    {label: '4', value: '4'},
                    {label: '5', value: '5'},
                    {label: '6', value: '6'},   
                    {label: '7', value: '7'},  
                    {label: '8', value: '8'},  
                    {label: '9', value: '9'},  
                    {label: '10', value: '10'},  
                    {label: '11', value: '11'}                 
                ]);
                self.parallelismDP = new ArrayDataProvider(self.parallelism, {keyAttributes: 'value'});

                self.CEOPT = ko.observable('LR');
                self.regExtChk = ko.observable(true);

                self.extractDP = new ArrayDataProvider(self.extType, {keyAttributes: 'value'});
       
                self.isFormReadonly = ko.observable(false);

                
                self.selectedStepValue = ko.observable('stp1');
                self.selectedStepLabel = ko.observable('DataSource');
                self.selectedStepFormLabel = ko.observable('DataSource');

                self.manualStepArray =
                        ko.observableArray([
                            {label: 'DataSource', id: 'stp1'},
                            {label: 'Process Options', id: 'stp2'},
                            {label: 'Parameter File', id: 'stp3'}
                        ]);

                        self.autoStepArray =
                        ko.observableArray([
                            {label: 'DataSource', id: 'stp1'}
                        ]);



                self.categorySelectionChanged = (event) => {
                    self.selectedSubcategory('');
                    let sub = getSubcategories(event.detail.value);
                    self.subcategories(sub);
                };

                self.ctvalue = ko.observable(ConverterUtilsI18n.IntlConverterUtils.dateToLocalIso(new Date()));

                self.secondConverter = new DateTimeConverter.IntlDateTimeConverter(
                        {
                            pattern: "yyyy-MM-dd HH:mm:ss"
                        });
                self.csnvalue = ko.observable();

                self.decimalHalfDownConverter =
                        new NumberConverter.IntlNumberConverter({
                            style: 'decimal',
                            roundingMode: 'HALF_DOWN',
                            maximumFractionDigits: 0,
                            useGrouping: false
                        });


                self.ExtTrail = ko.observable();
                self.ExtTrailSize = ko.observable('500');

                self.modeVal = ko.observable("Integrated Tranlog");

                self.currentbeginmode = ko.observable('Begin Now');

                self.TrailName = ko.observable();
                self.trailSubDir = ko.observable();
                self.trailSubDirSlash = ko.observable('/');
                self.trailSize = ko.observable(500);

                self.beginmode = ko.observableArray([
                    {value: 'Begin Now', label: 'Now'},
                    {value: 'Begin ', label: 'Custom Time'},
                    {value: 'CSN', label: 'CSN'}
                ]);

                self.startOptionDP = new ArrayDataProvider(self.beginmode, {keyAttributes: 'value'});


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

                function getSrcDomains(){
                 if(self.SRConepDepUrl().length>0){
                    //console.log(self.SRConepDepUrl())
                    self.SRCusername1([]);
                    self.SRCothdom([]);
                    self.SRCaliasname1([]);
                    self.SRCdomname1([]);
                    $.ajax({
                        url: self.SRConepDepUrl() + "/ggcredstore",
                        type: 'GET',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#TimeoutInLoad').open();
                            }
                        },
                        success: function (data) {

                            for (var i = 0; i < data[1].length; i++) {
                                self.SRCothdom.push({dom : data[1][i].value});
                                       }

                                       self.SRCaliasname1(data[4]);


                                         for (var i = 0; i < data[2].length; i++) {
                                 self.SRCdomname1.push({label:data[2][i], value:data[2][i] }); 
                             }
    
                          for (var i = 0; i < data[0].length; i++) {
                                 self.SRCusername1.push({label:data[0][i].alias, value:data[0][i].alias,'children': [{label:data[0][i].uname,value:data[0][i].uname}] }); 
                             }
                             //console.log(self)
                            return self;
                        }
                    })
                }
                }

                self.SRCdomname1DP = new ArrayDataProvider(self.SRCdomname1, {keyAttributes: 'value'});

                function getTgtDomains(data, event) {
                    // console.log(self.TGTonepDepUrl())
                if(self.TGTonepDepUrl().length > 0) {
                    self.TGTusername1([]);
                    self.TGTothdom([]);
                    self.TGTaliasname1([]);
                    self.TGTdomname1([]);
                    $.ajax({
                        url: self.TGTonepDepUrl() + "/ggcredstore",
                        type: 'GET',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#TimeoutInLoad').open();
                            }
                        },
                        success: function (data) {

                            for (var i = 0; i < data[1].length; i++) {
                                self.TGTothdom.push({dom : data[1][i].value});
                                       }
                                       self.TGTaliasname1(data[4]);


                                         for (var i = 0; i < data[2].length; i++) {
                                 self.TGTdomname1.push({label:data[2][i], value:data[2][i] }); 
                             }
    
                          for (var i = 0; i < data[0].length; i++) {
                                 self.TGTusername1.push({label:data[0][i].alias, value:data[0][i].alias,'children': [{label:data[0][i].uname,value:data[0][i].uname}] }); 
                             }

                            return self;
                        }
                    })
                    self.dbTgtDetList([]);
                    $.ajax({
                        url: self.TGTonepDepUrl() + "/gginfoall",
                        type: 'GET',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#TimeoutInLoad').open();
                            }
                        },
                        success: function (data) {
                            self.rmtHostName(self.TGTonepDepUrl().split(':')[1].replace("//",''));
                            for (var i = 0; i < data[0].length; i++) {
                            self.rmtMgrPort(data[0][i].mgrport);
                            }
                            //console.log(self);
                            return self;
                            
                        }
                    })
                }
                }

                self.replicatDP = new ArrayDataProvider(self.repType, {keyAttributes: 'value'});
                self.TGTdomname1DP = new ArrayDataProvider(self.TGTdomname1, {keyAttributes: 'value'});


//SRC
                let SRCgetAliascategories = (category) => {
                    let found = self.SRCaliasname1().find(c => c.value === category);
                    return found ? found.children : null;
                };
                let SRCgetUnamecategories = (category) => {
                    let found = self.SRCusername1().find(c => c.value === category);
                    return found ? found.children : null;
                };
                self.SRCdomSelectionChanged = (event) => {
                    self.selectedSRCAliascategory('');
                    let children = SRCgetAliascategories(event.detail.value);
                    self.SRCaliascategories(children);
                    self.schemaList([]);
                    self.pdbList();
                };

                self.SRCaliascategoriesDP = new ArrayDataProvider(self.SRCaliascategories, {keyAttributes: 'value'});

                self.SRCDBSelectionChanged = (event) => {
                    self.textVal(false);
                };


                                self.ZDTChkChanged = (event) => {
                                    self.BtnCreateJOb(true);
                    // console.log(self.SrcOnePDepName());
                    if (self.ZDTChk() == true){
                        self.SrcOnePDepName("");
                        self.selectedSRCDomCategory("");
                        self.SRCcurrentPDB("");
                        self.pdbList("");
                        self.schemaList([]);
                        self.LoadName("");
                        self.textVal(true);
                        self.CDBCheck('NO');
                        self.dbDetList([]);
                        self.dbDetList.valueHasMutated();
                        setTimeout(function(){ 
                            self.BtnExprt(true);
                            self.ButtonVal(true);
                        }, 30);
                        
                    }else{
                        self.dbDetList([]);
                        self.dbDetList.valueHasMutated();
                        self.SrcOnePDepName("");
                        self.SRCcurrentPDB("");
                        self.pdbList("");
                        self.LoadName("");
                        self.textVal(true);
                        self.CDBCheck('NO');
                        setTimeout(function(){ 
                            self.BtnExprt(true);
                            self.ButtonVal(true);
                            
                        }, 30);
                    }
                };

                self.SRCaliasSelectionChanged = (event) => {
                    self.selectedSRCUsercategory('');
                    let children = SRCgetUnamecategories(event.detail.value);
                    self.SRCunamecategories(children);
                };


//TGT
                let TGTgetAliascategories = (category) => {
                    let found = self.TGTaliasname1().find(c => c.value === category);
                    return found ? found.children : null;
                };
                let TGTgetUnamecategories = (category) => {
                    let found = self.TGTusername1().find(c => c.value === category);
                    return found ? found.children : null;
                };
                self.TGTdomSelectionChanged = (event) => {
                    self.selectedTGTAliascategory('');
                    let children = TGTgetAliascategories(event.detail.value);
                    self.TGTaliascategories(children);
                };

                self.TGTaliascategoriesDP = new ArrayDataProvider(self.TGTaliascategories, {keyAttributes: 'value'});

                self.TGTaliasSelectionChanged = (event) => {
                    self.selectedTGTUsercategory('');
                    let children = TGTgetUnamecategories(event.detail.value);
                    self.TGTunamecategories(children);
                };




                self.value = ko.observable();

                self.groupValid = ko.observable();
                
                self.tmpPrm = ko.observable();

               


                self.isRequired = ko.observable(true);
                self.checkboxValues = ko.observableArray(['required', 'helpSource', 'helpDef']);

                self.isRequired = ko.computed(function () {
                    return self.checkboxValues.indexOf('required') !== -1;
                });
                self.helpDef = ko.computed(function () {
                    return (self.checkboxValues.indexOf('helpDef') !== -1) ? self._HELP_DEF : null;
                });
                self.helpSource = ko.computed(function () {
                    return (self.checkboxValues.indexOf('helpSource') !== -1) ? self._HELP_SOURCE : null;
                });


                self.regExpValidatorRemap =
                new AsyncRegExpValidator({
                    pattern: "[a-zA-Z0-9,.'-]{1,}",
                    hint: "comma seperated",
                    messageDetail: "You must enter at least 1 letter"
                });

                self.regExpValidator =
                        new AsyncRegExpValidator({
                            pattern: "[a-zA-Z0-9,.'-]{1,}",
                            hint: "1 or more letters",
                            messageDetail: "You must enter at least 1 letter"
                        });



                        self.emailRegExpValidator =
                        new AsyncRegExpValidator({
                            pattern: ".+\@.+\..+",
                            hint: "email format",
                            messageDetail: "Invalid email format"
                        });

                self.previousStep = function () {
                    var train = document.getElementById('train');
                    var prev = train.getPreviousSelectableStep();
                    if (prev != null) {
                        self.selectedStepValue(prev);
                        self.selectedStepLabel(train.getStep(prev).label);
                        self.selectedStepFormLabel(train.getStep(prev).label);
                    }
                };

                self.nextStep = function (event) {
                    var train = document.getElementById('train');
                    var next = train.getNextSelectableStep();
                    if(next == "stp2"){
                        var valid = self._checkValidationGroup("SRC");
                    }else{
                        var valid = self._checkValidationGroup("dataSrc");
                    }
                   
                    
                    if (valid) {
                        //The previous step will have a confirmation message type icon
                        self.selectedStepLabel.messageType = 'confirmation';
                        document.getElementById("train").updateStep(self.selectedStepValue, self.selectedStepValue);
                        //Now the clicked step could be selected
                        self.selectedStepValue(next);
                        self.selectedStepLabel(train.getStep(next).label);
                        self.selectedStepFormLabel(train.getStep(next).label);
                        return;
                    } else {
                        //The ojBeforeSelect can be cancelled by calling event.preventDefault().
                        event.preventDefault();
                        //The previous step will have an error message type icon
                        self.selectedStepLabel.messageType = 'error';
                        document.getElementById("train").updateStep(self.selectedStepLabel.id, self.selectedStepLabel);
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
                    }
                    else {
                       
                        tracker.showMessages();
                        tracker.focusOn("@firstInvalidShown");
                        return false;
                    }
                };

                this.validate = (event) => {
                    var next = train.getNextSelectableStep();
                   if(next == "stp2"){
                        var valid = self._checkValidationGroup("SRC");
                    }else{
                        var valid = self._checkValidationGroup("dataSrc");
                    }
                    if (valid) {
                      
                        return;
                    }
                    else {
                        //The ojBeforeSelect can be cancelled by calling event.preventDefault().
                        event.preventDefault();
                       
                        setTimeout(function () {
                            tracker.showMessages();
                            tracker.focusOn("@firstInvalidShown");
                        }, 0);
                        return;
                    }
                }
                self.chkTblList = ko.observableArray([]);
                self.currentChkptTbl = ko.observable();

 function queryChkTbl(data, event) {
     if (self.TGTonepDepUrl().length > 0){
    self.chkTblList([]);
    self.currentChkptTbl('');
    $.ajax({
        url: self.TGTonepDepUrl() + "/infochkpttbl",
        type: 'POST',
        data: JSON.stringify({
            domain: self.selectedTGTDomCategory(),
            alias: self.TGTcurrentPDB(),
        }),
        dataType: 'json',
        timeout: sessionStorage.getItem("timeInetrval"),
        contrep: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#TimeoutInLoad').open();
                            }
                        },
        success: function (data) {

            for (var i = 0; i < data[0].length; i++) {
            self.chkTblList.push({'label':data[0][i],'value':data[0][i]});
            }
            self.chkTblList.valueHasMutated();
            return self;

        }

    })
}
}
self.chkpttblDP = new ArrayDataProvider(self.chkTblList, {keyAttributes: 'value'});


//start 
self.chkptTblName = ko.observable();
self.domname1 = ko.observableArray([]);
self.selectedDomCategory = ko.observable();
self.aliascategories = ko.observableArray([]);
self.selectedAliascategory = ko.observable();
self.aliasname1 = ko.observableArray([]);
self.AddChkptTblMsg = ko.observable();

self.gotoGGAdmin = function (data, event) {
    self.aliasname1([]);
    self.domname1([]);
    $.ajax({
        url: self.DepName() + "/ggcredstore",
        type: 'GET',
        dataType: 'json',
        timeout: sessionStorage.getItem("timeInetrval"),
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#TimeoutInLoad').open();
                            }
                        },
        success: function (data) {
            
            self.aliasname1.push(data[4]);
            self.aliasname1.valueHasMutated();
            for (var i = 0; i < data[2].length; i++) {
                self.domname1.push({label:data[2][i], value:data[2][i] }); 
            }      
            self.domname1.valueHasMutated();        
                
            return self;
        }
    })

    document.querySelector('#chkDlg').open();
}
     
self.addsuppOKClose = function (event) {
    document.querySelector('#chkDlg').close();
};

self.DBErrorOKClose = function (event) {
    document.querySelector('#DBErrDialog').close();
};

this.domSelectionChanged = (event) => {
    self.selectedAliascategory('');
    let children = getAliascategories(event.detail.value);
    self.aliascategories(children);
};

let getAliascategories = (category) => {
    let found = self.aliasname1().find(c => c.value === category);
    return found ? found.children : null;
};

self.addChkptTbl = function (data, event) {
    let valid = self._checkValidationGroup("chktbl");
     if (valid) {
        self.AddChkptTblMsg('');
        $.ajax({
            url: self.TGTonepDepUrl() + "/ggaddchkpttbl",
            type: 'POST',
            data: JSON.stringify({
                domain: self.selectedTGTDomCategory(),
                alias: self.TGTcurrentPDB(),
                chkpttbl : self.chkptTblName()
            }),
            dataType: 'json',
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#TimeoutInLoad').open();
                            }
                        },
            success: function (data) {
                document.querySelector('#chkDlg').close();
                document.querySelector('#ChkptTblDialog').open();
                self.AddChkptTblMsg(data[0]);
                queryChkTbl();
                return self;
            }

        })
     }
  }

  self.AddChkptTblMsgOKClose = function (event) {
    self.selectedDomCategory(''),
    self.selectedAliascategory(''),
    self.chkptTblName('')
    document.querySelector('#ChkptTblDialog').close();
    queryChkTbl();
};
  //end

self.currentExtParamList = ko.observable();
self.currentPmpParamList = ko.observable();

self.newExtParamList =  ko.observable('');
self.newRepParamList =  ko.observable('');

//start

////console.log(selectedData[1]);



self.currentexpExcludeParam = ko.computed( { 
    read:function() {
        var currentexpExcludeParam ='';
        if (self.selectionInfo().length > 0){
        let selectedData = self.selectionInfo().split(",");
        let selectedData1 = '';
        for(var i =0 ; i< selectedData.length; i++){
            selectedData1 = selectedData[i].split('.')[1]
            currentexpExcludeParam = currentexpExcludeParam + '\'\'' +  selectedData1 + '\'\'' + ',';
        }
        currentexpExcludeParam = currentexpExcludeParam.slice(0,-1);
        console.log(currentexpExcludeParam)
    }
      return currentexpExcludeParam;
        
  },
  write: function(newVal) {
      var currentexpExcludeParam = newVal;
      return newVal;
  }
  });


  self.currentSchemaParam = ko.computed( { 
    read:function() {
        var currentSchemaParam ='';
        if (self.selectionInfo().length > 0){
        let selectedData = self.selectionInfo().split(",");
        for(var i =0 ; i< selectedData.length; i++){
            currentSchemaParam = currentSchemaParam +'TABLEEXCLUDE ' +  selectedData[i] + '\n';
        }
    }
      return currentSchemaParam;
        
  },
  write: function(newVal) {
      var currentSchemaParam = newVal;
      return newVal;
  }
  });

  self.ExtSchemaParam = ko.computed( { 
    read:function() {
        var ExtSchemaParam ='';
        for(var i =0 ; i< self.schemaList().length; i++){
            if (self.CDBCheck()=='YES' && self.pdbList().length > 0)
{
            ExtSchemaParam = ExtSchemaParam  + 'TABLE ' +  self.schemaList()[i] + ".*;" + '\n';
}
else{
    ExtSchemaParam = ExtSchemaParam +'TABLE ' +  self.schemaList()[i] + ".*;" + '\n';

}
        }
      return ExtSchemaParam;
        
  },    
  write: function(newVal) {
      var ExtSchemaParam = newVal;
      return newVal;
  }
  });


  self.RepSchemaParam = ko.computed( { 
    read:function() {
        var RepSchemaParam ='';
        for(var i =0 ; i< self.schemaList().length; i++){
            RepSchemaParam = RepSchemaParam +'MAP ' +  self.schemaList()[i] + ".* , TARGET " + self.schemaList()[i] + ".*;" + '\n';
        }
      return RepSchemaParam;
        
  },
  write: function(newVal) {
      var RepSchemaParam = newVal;
      return newVal;
  }
  });

  self.rmthostParam = ko.computed( { 
    read:function() {
        var rmthostParam ='';
        if (self.LoadOption() === 'file')
        {
        var rmthostParam = 'RMTHOST ' + self.rmtHostName() + ',MGRPORT '  + self.rmtMgrPort() + ' , TCPBUFSIZE  4194304,ENCRYPT AES256'+  '\n' + 'rmtfile ' +  '  ' + self.trailSubDir() + self.trailSubDirSlash() +  self.TrailName() + '\n'  + 'ENCRYPTTRAIL';
        }
        else {
        var rmthostParam = 'RMTHOST ' + self.rmtHostName() + ',MGRPORT '  + self.rmtMgrPort() + ' , TCPBUFSIZE  4194304,ENCRYPT AES256'+ '\n' + 'RMTTASK  replicat, GROUP  ' + self.RepName() ;
        }

      return rmthostParam;
        
  },
  write: function(newVal) {
      var rmthostParam = newVal;
      return newVal;
  }
  });

//end

self.currentExtParam = ko.computed( { 
    read:function() {
        if (self.CDBCheck()=='YES' && self.pdbList().length > 0)
        {
            if (self.LoadOption() === 'sqlldr')
                {
                    self.currentRepType('SPECIALRUN');  
                    var currentExtParam = 'EXTRACT ' + self.ExtName() + '\n' + 'useridalias '+ self.SRCcurrentPDB() + ' domain ' + self.selectedSRCDomCategory() + '\n' + self.rmthostParam()  + '\n' + 'BULKLOAD' + '\n' + 'REPORTCOUNT EVERY 1 MINUTES, RATE' + '\n'  + self.currentExtOptParamList()  + '\n' + 'SOURCECATALOG ' + self.pdbList() + '\n' + self.currentSchemaParam() + self.ExtSchemaParam() ;
                }
            else if  (self.LoadOption() === 'file')
                {
                    var currentExtParam = 'EXTRACT ' + self.ExtName() + '\n' + 'useridalias '+ self.SRCcurrentPDB() + ' domain ' + self.selectedSRCDomCategory() + '\n' + self.rmthostParam()  + '\n' + 'REPORTCOUNT EVERY 1 MINUTES, RATE' + '\n'  + self.currentExtOptParamList() + '\n' + 'SOURCECATALOG ' + self.pdbList() + '\n' + self.currentSchemaParam() + self.ExtSchemaParam() ;
                }
            }
        else{
            if (self.LoadOption() === 'sqlldr')
            {
                self.currentRepType('SPECIALRUN');  
                var currentExtParam = 'EXTRACT ' + self.ExtName() + '\n' + 'useridalias '+ self.SRCcurrentPDB() + ' domain ' + self.selectedSRCDomCategory() + '\n' + self.rmthostParam()  + '\n' + 'BULKLOAD' + '\n' + 'REPORTCOUNT EVERY 1 MINUTES, RATE' + '\n'  + self.currentExtOptParamList()  + '\n' + self.currentSchemaParam() + self.ExtSchemaParam() ;
            }
            else if  (self.LoadOption() === 'file')
            {
                var currentExtParam = 'EXTRACT ' + self.ExtName() + '\n' + 'useridalias '+ self.SRCcurrentPDB() + ' domain ' + self.selectedSRCDomCategory() + '\n' + self.rmthostParam()  + '\n' + 'REPORTCOUNT EVERY 1 MINUTES, RATE' + '\n'  + self.currentExtOptParamList()  + '\n' + self.currentSchemaParam() + self.ExtSchemaParam() ;
            }
        }
      return currentExtParam;
  },
  write: function(newVal) {
      var currentExtParam = newVal;
      return newVal;
  }
  });

    self.currentExtParamList = self.currentExtParam;


    self.currentRepParam = ko.computed( { 
        read:function() {
            if (self.CDBCheck()=='YES' && self.pdbList().length > 0)
            {      
               var currentRepParam = 'REPLICAT ' + self.RepName() + '\n' + 'useridalias '+ self.TGTcurrentPDB() + ' domain ' + self.selectedTGTDomCategory() + '\n' + 'REPORTCOUNT EVERY 1 MINUTES, RATE' + '\n'  + self.currentRepOptParamList() + '\n' + 'SOURCECATALOG ' + self.pdbList() + '\n' + self.RepSchemaParam();
            }
            else{
                var currentRepParam = 'REPLICAT ' + self.RepName() + '\n' + 'useridalias '+ self.TGTcurrentPDB() + ' domain ' + self.selectedTGTDomCategory() + '\n' + 'REPORTCOUNT EVERY 1 MINUTES, RATE' + '\n'  + self.currentRepOptParamList() + '\n'  + self.RepSchemaParam();

            }
          return currentRepParam;
      },
      write: function(newVal) {
          var currentRepParam = newVal;
          return newVal;
      }
      });

      self.currentRepParamList = self.currentRepParam;



                
                //The method updates the label text to show what step the user is on
                self.updateLabelText = function (event) {
                    if (self.selectedStepValue == 'stp2') {
                        self.selectedStepFormLabel('Extract Options');
                        self.isFormReadonly(false);
                    } else if (self.selectedStepValue == "stp1") {
                        self.selectedStepFormLabel('DataSource / Extract Type');
                        self.isFormReadonly(false);
                    } else if (self.selectedStepValue == "stp3") {
                        self.selectedStepFormLabel('Parameter File');
                        self.isFormReadonly(true);
                    }
                }.bind(this);

                self.AddExtractMsg = ko.observableArray([]);
                self.AddReplicatMsg = ko.observableArray([]);

                self.cancel = function () {
                    self.router.go({path : 'manage'});
                }

                self.onepDepList = ko.observableArray([]);

                function getOnepDep() {
                    self.onepDepList([]);
                    $.ajax({
                        url: self.DepName() + "/onepdep",
                        type: 'GET',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                                    error: function (xhr, textStatus, errorThrown) {
                                        if(textStatus == 'timeout' || textStatus == 'error'){
                                            document.querySelector('#TimeoutInLoad').open();
                                        }
                                    },
                        success: function (data) {
                            for (var i = 0; i < data[0].length; i++) {
                            self.onepDepList.push({'label' : data[0][i].dep , value :  data[0][i].dep} );
                            }
                            //self.onepDepList.valueHasMutated();
                            return self;
                        }

                    })
                }

                self.onepDepListDP = new ArrayDataProvider(self.onepDepList, {keyAttributes: 'value'});

                self.args = args;
                // Create a child router with one default path
                self.router = self.args.parentRouter;



                self.addAutoILProcOKClose = function(){
                    self.router.go({ path: 'initmon' , params: { LoadName: self.LoadName() } });
                }
                


                self.AddInitialLoadExtOKClose = function (data,event) {
                    document.querySelector('#AddInitailLoadExtDialog').close();
                    $.ajax({
                        url: self.DepName() + "/addilext",
                        type: 'POST',
                        data: JSON.stringify({
                            srcdep : self.SrcOnePDepName(),
                            extname: self.ExtName(),
                            trail : self.trailSubDir() + self.trailSubDirSlash() + self.TrailName()
                        }),
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                                    error: function (xhr, textStatus, errorThrown) {
                                        if(textStatus == 'timeout' || textStatus == 'error'){
                                            document.querySelector('#TimeoutInLoad').open();
                                        }
                                    },
                        success: function (data) {

                            return self;
                        }

                    })
                };


                self.AddInitialLoadRepOKClose = function () {
                    document.querySelector('#AddInitailLoadRepDialog').close();
                    $.ajax({
                        url: self.DepName() + "/addilrep",
                        type: 'POST',
                        data: JSON.stringify({
                            tgtdep : self.TgtOnePDepName(),
                            repname: self.RepName(),
                            trail : self.trailSubDir() + self.trailSubDirSlash() + self.TrailName()
                        }),
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                                    error: function (xhr, textStatus, errorThrown) {
                                        if(textStatus == 'timeout' || textStatus == 'error'){
                                            document.querySelector('#TimeoutInLoad').open();
                                        }
                                    },
                        success: function (data) {
                            if (self.AddReplicatMsg().toString().includes('ERROR'))
                            {
                            //      self.router.go({path : 'addextract'});
                            }
                            else 
                            {
                                self.router.go({path :'initmon'});
                            }

                                return self;
                            }

                    })
                    
                };

                self.PDBNameList = ko.observableArray([]);
                self.schemaNameList = ko.observableArray([]);
                self.dbDetList = ko.observableArray([]);
                
               self.CDBData  =  function(data, event) {
                   if(self.SRCcurrentPDB()){
                    self.CDBCheck('');
                    self.OPError();
                    self.PDBNameList([]);
                    self.dbDetList([]);
                    self.schemaNameList([]);
                    self.schemaList([]);
                    self.pdbList('');
                    self.trailSubDir('');
                    self.dbMainVersion(0);
                    self.dbMinorVersion(0);
                    document.querySelector('#SelectSchemaDialog').open();
                    $.ajax({
                        url: self.SRConepDepUrl() + "/cdbcheck",
                        type: 'POST',
                        data: JSON.stringify({
                            dbname : self.SRCcurrentPDB()
                        }),
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                                    error: function (xhr, textStatus, errorThrown) {
                                        if(textStatus == 'timeout' || textStatus == 'error'){
                                            document.querySelector('#SelectSchemaDialog').close();
                                            document.querySelector('#TimeoutInLoad').open();
                                        }
                                    },
                        success: function (data) {
                            self.CDBCheck(data[0]);
                            console.log(data)
                            if(!Object.values(data[1]).some(val => typeof val === 'string' && val.includes('ORA-'))){
                                // for (var i = 0; i < data[1].length; i++) {
                                //     self.PDBNameList.push({ 'label': data[1][i].NAME, 'value': data[1][i].NAME });
                                // }
                                // for (var i = 0; i < data[2].length; i++) {
                                //     self.schemaNameList.push({ 'label': data[2][i].USERNAME, 'value': data[2][i].USERNAME });
                                // }
                                for (var i = 0; i < data[1].length; i++) {
                                    self.dbDetList.push({ 'dbid': data[1][i].DBID,'dbname' : data[1][i].DBNAME,'pdbname' : data[1][i].PDBNAME,'platform' : data[1][i].PLATFORM_NAME  ,'host' : data[1][i].HOST,'version' : data[1][i].VERSION,'dbedition' : data[1][i].DB_EDITION , 'db_role' : data[1][i].DATABASE_ROLE , 'current_scn' : data[1][i].CURRENT_SCN , 'cdb' : data[1][i].CDB});
                                }
                                // self.trailSubDir(data[4]);
                                // self.dbMainVersion(data[5]);
                                // self.dbMinorVersion(data[6]);
                                document.querySelector('#SelectSchemaDialog').close();
                            }
                            else{
                                document.querySelector('#SelectSchemaDialog').close();
                                document.querySelector('#DBErrDialog').open();
                                self.OPError(data[1]);
                            }
                            return self;                            
                        }    
                    })
                   }
                    
                }

                self.PDBNameListDP =  new ArrayDataProvider(self.PDBNameList, {keyAttributes: 'value'});    
                self.schemaNameListDP = new ArrayDataProvider(self.schemaNameList, {keyAttributes: 'value'});     

                self.schemaNameCDBList = ko.observableArray([]);

                self.SRCDBSchema = function (data, event) {
                    document.querySelector('#SelectSchemaDialog').open();
                    self.schemaNameCDBList([]);
                    self.OPError([]);
                    $.ajax({
                        url: self.SRConepDepUrl() + "/supplogschema",
                        type: 'POST',
                        data: JSON.stringify({
                            dbname : self.SRCcurrentPDB(),
                            cdbCheck : self.CDBCheck(),
                            pdbName : self.pdbList()
                        }),
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#SelectSchemaDialog').close();
                                document.querySelector('#TimeoutInLoad').open();
                            }
                        },
                        success: function (data) {
                            if (data[0].includes('ORA-')){
                                document.querySelector('#SelectSchemaDialog').close();
                                document.querySelector('#ErrorLoad').open();
                                self.OPError(data[0]);
                            }

                            for (var i = 0; i < data[0].length; i++) {
                                self.schemaNameCDBList.push({ 'label': data[0][i].USERNAME, 'value': data[0][i].USERNAME});
                            }
                            self.schemaNameCDBList.valueHasMutated();
                            document.querySelector('#SelectSchemaDialog').close();
                            return self;
                            
                        }
    
                    })
                }

                self.schemaNameCDBListDP = new ArrayDataProvider(self.schemaNameCDBList, {keyAttributes: 'value'}); 
                self.dbDetListDP = new ArrayDataProvider(self.dbDetList, {keyAttributes: 'dbid'});    

                self.dbVer = ko.observable(0);
                self.DBTgtSchema = function (data, event) {
                    if(self.TGTcurrentPDB()){
                    
                        if(self.BtnExprt()==false){
                            self.BtnImprt(false)
                        }
    
                        document.querySelector('#SelectSchemaDialog').open();
                        self.trailSubDir('');
                        self.dbTgtDetList([]);
                        self.OPError([]);
                        self.dbVer('');
                        $.ajax({
                            url: self.TGTonepDepUrl() + "/cdbcheck",
                            type: 'POST',
                            data: JSON.stringify({
                                dbname : self.TGTcurrentPDB()
                            }),
                            dataType: 'json',
                            timeout: sessionStorage.getItem("timeInetrval"),
                            context: self,
                            error: function (xhr, textStatus, errorThrown) {
                                if(textStatus == 'timeout' || textStatus == 'error'){
                                    document.querySelector('#SelectSchemaDialog').close();
                                    document.querySelector('#TimeoutInLoad').open();
                                }
                            },
                            success: function (data) {
                                console.log(data)
                                self.ButtonChltbl(false);
                                if(!Object.values(data[1]).some(val => typeof val === 'string' && val.includes('ORA-'))){    
                                    for (var i = 0; i < data[1].length; i++) {
                                        self.dbTgtDetList.push({ 'dbid': data[1][i].DBID,'dbname' : data[1][i].DBNAME,'pdbname' : data[1][i].PDBNAME,'platform' : data[1][i].PLATFORM_NAME  ,'host' : data[1][i].HOST,'version' : data[1][i].VERSION,'dbedition' : data[1][i].DB_EDITION , 'db_role' : data[1][i].DATABASE_ROLE , 'current_scn' : data[1][i].CURRENT_SCN , 'cdb' : data[1][i].CDB});
                                        self.dbVer(data[1][i].VERSION);
                                    }
                                    self.dbTgtDetList.valueHasMutated();
                                    self.trailSubDir(data[4]);
                                    queryChkTbl();
                                    document.querySelector('#SelectSchemaDialog').close();
                                }
                                else{
                                    document.querySelector('#SelectSchemaDialog').close();
                                    document.querySelector('#DBErrDialog').open();
                                    self.OPError(data[1]);    
                                }
                                return self;                                
                            }
        
                        })
                    }
                   
                }
                self.dbTgtDetListDP = new ArrayDataProvider(self.dbTgtDetList, {keyAttributes: 'dbid'});    

                self.avg_space = ko.observable(0);

                self.tableNameList = ko.observableArray([]);

                self.qualifySplitList = ko.observableArray([]);

                self.SrcDBSchemaFetch = function (data, event) {
                    document.querySelector('#SelectSchemaDialog').open();
                    self.tableNameList([]);
                    self.qualifySplitList([]);
                    self.avg_space(0);
                    $.ajax({
                        url: self.SRConepDepUrl() + "/tablelist",
                        type: 'POST',
                        data: JSON.stringify({
                            dbname : self.SRCcurrentPDB(),
                            schemaList : self.schemaList(),
                            cdbCheck : self.CDBCheck(),
                            pdbName : self.pdbList(),
                            gatherMeta : self.gatherMeta(),
                            LoadName : self.LoadName()
                        }),
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                                    error: function (xhr, textStatus, errorThrown) {
                                        if(textStatus == 'timeout' || textStatus == 'error'){
                                            document.querySelector('#SelectSchemaDialog').close();
                                            document.querySelector('#TimeoutInLoad').open();
                                        }
                                    },
                        success: function (data) {
                            document.getElementById('tableNameList').refresh();
                            let total=0;
                            for (var i = 0; i < data[0].length; i++) {
                                self.tableNameList.push({'TABLE_NAME': data[0][i].owner + '.' + data[0][i].table_name , 'ROWCNT' : data[0][i].num_rows ,'AVGSPC': data[0][i].avg_space,'ANALYZETIME' : data[0][i].last_analyzed});
                                total = total + parseInt(data[0][i].avg_space);
                            }
                            self.avg_space(total);
                            for (var i = 0; i < data[2].length; i++) {
                            self.qualifySplitList.push({'TABLE_NAME' : data[2][i].table_name });
                            }
                            self.tableNameList.valueHasMutated();
                            self.qualifySplitList.valueHasMutated();
                            //console.log(self);
                            document.querySelector('#SelectSchemaDialog').close();
                            if (self.gatherMeta() == true) {
                                self.ApplyMetaButtonVal(false);
                            }
                            else {
                                self.ApplyMetaButtonVal(true);
                            }
                            return self;
                        }
    
                    })
                }
                
                self.tableNameListDP = new PagingDataProviderView(new ArrayDataProvider(self.tableNameList, {idAttribute: 'TABLE_NAME'}));   
                
                self.dataproviderView = new ListDataProviderView(self.tableNameListDP, {
                    sortCriteria: [{ attribute: "AVGSPC", direction: "descending" }],
                });
                self.qualifySplitListDP = new ArrayDataProvider(self.qualifySplitList, {idAttribute: 'TABLE_NAME'}); 

                self.tableListcolumnArray = [
                {headerText: 'Schema.Table Name',
                field: 'TABLE_NAME',
                footerTemplate: "revenueLabelTemplate"},
                {headerText: 'Row Count',
                field: 'ROWCNT'},
                {headerText: 'Average Size(MB)',
                footerTemplate: "revenueTotalTemplate",
                field: 'AVGSPC'},
                {headerText: 'Analyze Time',
                field: 'ANALYZETIME'}]

          self.dbDetcolumnArray = [{headerText: 'DB Name',
                field: 'dbname'},
                {headerText: 'PDB Name',
                field: 'pdbname'},
                {headerText: 'Platform',
                field: 'platform'},
                {headerText: 'Host',
                field: 'host'},
                {headerText: 'Version',
                field: 'version'} ,
                {headerText: 'DB Edition',
                field: 'dbedition'} ,
                {headerText: 'DB Role',
                field: 'db_role'} ,
                {headerText: 'Current SCN',
                field: 'current_scn'} ,
                {headerText: 'CDB',
                field: 'cdb'} ,
             ]

             self.submitInput = function(data,event){
                setTimeout(function(){  self.LoadName(self.currentRawValue().toUpperCase());}, 1);
             }
             
             self.valueChangedHandler1 = (event) => {
                self.ButtonVal(false);
                self.BtnExprt(false);
                self.ApplyMetaButtonVal(false);
            };



            self.valueChangedHandler = (event) => {
                self.textVal(false);
                self.reMapSchemaNameList([]);
                for (var i = 0; i < self.schemaList().length; i++) {
                    self.reMapSchemaNameList.push({ 'label': self.schemaList()[i], 'value': self.schemaList()[i] });
                }
                self.reMapSchemaNameListDisp.push(self.schemaList());
            };
            self.reMapSchemaNameListDP = new ArrayDataProvider(self.reMapSchemaNameList, {keyAttributes: 'value'}); 

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
                { value: { row: "none", column: "multiple" }, label: "Multiple Column" },
                { value: { row: "single", column: "none" }, label: "Single Row" },
                { value: { row: "multiple", column: "none" }, label: "Multiple Row" },
            ];
            this.selectionModeDP = new ArrayDataProvider(this.selectionModes, {
                keyAttributes: "value",
            });

            this.selectedChangedListener = (event) => {
                let selectionText = "";
                if (event.detail.value.row.isAddAll()) {
                     const iterator = event.detail.value.row.deletedValues();
                    const row=self.tableNameList();
                    for(var i=0;i<row.length;i++) {
                        selectionText = selectionText +  row[i].TABLE_NAME + ", " ;
                    }
                   if(event.detail.value.row._keys.size>0){
                    event.detail.value.row._keys.forEach(function (key) {
                        selectionText = selectionText.replace(key+",", "");
                    });
                    
                   }
                   selectionText = selectionText.replace(/,\s*$/,"");
                }
                else {
                    const row = event.detail.value.row;
                    const column = event.detail.value.column;
                    if (row.values().size > 0) {
                        row.values().forEach(function (key) {
                            selectionText += selectionText.length === 0 ? key : ", " + key;
                        });
                        selectionText = '' + selectionText;
                    }
                    if (column.values().size > 0) {
                        column.values().forEach(function (key) {
                            selectionText += selectionText.length === 0 ? key : ", " + key;
                        });
                        selectionText = "Column Selection:\nColumn Keys: " + selectionText;
                    }
                }
                this.selectionInfo(selectionText);
            };
            this.selectedSelectionMode.subscribe((newValue) => {
                // Reset selected Items on selection mode change.
                this.selectedItems({ row: new ojkeyset_1.KeySetImpl(), column: new ojkeyset_1.KeySetImpl() });
            });


///New Begin

self.expDirNames = ko.observableArray([]);
self.srcExpDir = ko.observable();
self.srcCompression = ko.observable('ALL');
self.srcContents = ko.observable(1);
self.srcCompAlgo = ko.observable('HIGH');
self.srcExpParallel = ko.observable('5');

//AWS Credentials

self.AWSBucket = ko.observable();
self.AccessKeyID = ko.observable();
self.AccessKey = ko.observable();


self.expdpOptions = function (data, event) {
        self.expDirNames([]);
        $.ajax({
            url: self.SRConepDepUrl() + "/expdirs",
            type: 'POST',
            data: JSON.stringify({
                alias : self.SRCcurrentPDB(),
                cdbCheck : self.CDBCheck(),
                pdbList : self.pdbList()
            }),
            dataType: 'json',
            timeout: sessionStorage.getItem("timeInetrval"),
            context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#TimeoutInLoad').open();
                            }
                        },
            success: function (data) {
                document.querySelector('#expdpOptDialog').open();
                for (var i = 0; i < data[0].length; i++) {
                self.expDirNames.push({'label' : data[0][i] , 'value' : data[0][i]});
                }
        
                return self;
                
            }

        })
   
}

self.expXID = ko.observableArray([]);

function currTransaction() {
    self.expXID([]);
    $.ajax({
        url: self.SRConepDepUrl() + "/xiddet",
        type: 'POST',
        data: JSON.stringify({
            jobName : self.LoadName(),
            alias : self.SRCcurrentPDB(),
            cdbCheck : self.CDBCheck(),
            pdbList : self.pdbList()
        }),
        dataType: 'json',
        timeout: sessionStorage.getItem("timeInetrval"),
        context: self,
                    error: function (xhr, textStatus, errorThrown) {
                        if(textStatus == 'timeout' || textStatus == 'error'){
                            document.querySelector('#TimeoutInLoad').open();
                        }
                    },
        success: function (data) {
            document.querySelector('#currTranscationDialog').open();
            if(data[0].length>0){
                self.expXID.push({'INST_ID' : data[0][0].inst_id,'XID' : data[0][0].XIDUSN + '.' + data[0][0].XIDSLOT + '.' + data[0][0].XIDSLOT ,'CURRENT_TIME' : data[1],'START_TIME' : data[0][0].start_time , 'CAPTURE_TIME' : data[2]});   
            }
            console.log(self.expXID())
            return self;
        }

    })

}

self.expXIDDP = new ArrayDataProvider(self.expXID, { keyAttributes: "XID"});

self.expDirNamesDP = new ArrayDataProvider(self.expDirNames, { keyAttributes: "value"});

self.impDirNames = ko.observableArray([]);

self.impdpOptions = function (data, event) {
    document.querySelector('#impdpOptDialog').open();
    self.impDirNames([]);
    $.ajax({
        url: self.TGTonepDepUrl() + "/expdirs",
        type: 'POST',
        data: JSON.stringify({
            alias : self.TGTcurrentPDB(),
            cdbCheck : 'NO' , 
            pdbList : ''
        }),
        dataType: 'json',
        timeout: sessionStorage.getItem("timeInetrval"),
        context: self,
                    error: function (xhr, textStatus, errorThrown) {
                        if(textStatus == 'timeout' || textStatus == 'error'){
                            document.querySelector('#TimeoutInLoad').open();
                        }
                    },
        success: function (data) {
            document.querySelector('#impdpOptDialog').open();
            for (var i = 0; i < data[0].length; i++) {
            self.impDirNames.push({'label' : data[0][i], 'value' : data[0][i]});
            }
            console.log(self.impDirNames())
            return self;
            
        }

    })

}

self.impDirNamesDP = new ArrayDataProvider(self.impDirNames, { keyAttributes: "value"});

self.expdpOptionsOKClose = function(){
    var valid = self._checkValidationGroup("dataPumpexport");
     if (valid) {
        self.Btnexprtcheck(false);
        if((self.Btnexprtcheck() == false) && (self.Btnimprttcheck() == false)) {
            self.BtnCreateJOb(false);
        }
        document.querySelector('#expdpOptDialog').close();
    } 
}

self.checkTableEvent = function(event){
    self.BtnCreateJOb(false);
}

self.impdpOptionsOKClose = function(){
    let flag = 0;
    if(self.remapSchema()[0] == "yes"){
        let valid = self._checkValidationGroup("RemapSchemaForm");
     if (!valid) {
        flag = 1;
     }
    }
    if(self.remapTableSpaces()[0] == "yes"){
        let valid = self._checkValidationGroup("RemapTablespaceForm");
        if (!valid) {
            flag = 1;
         }
    }
    if(flag == 0){
        var valid = self._checkValidationGroup("dataPumpImport");
            if (valid) {
                self.Btnimprttcheck(false);
                if((self.Btnexprtcheck() == false) && (self.Btnimprttcheck() == false)) {
                    console.log(self.ZDTChk());
                    if(self.ZDTChk() == false){
                        self.BtnCreateJOb(false);
                    }
                }
                document.querySelector('#impdpOptDialog').close();
            }
    }
}


self.XIDcolumnArray = [{headerText: 'Current Time',
field: 'CURRENT_TIME'},
{headerText: 'Transaction Start Time',
field: 'START_TIME'},
{headerText: 'Capture Start Time',
field: 'CAPTURE_TIME'},
{headerText: 'Instance ID',
field: 'INST_ID'},
{headerText: 'Transaction ID',
field: 'XID'},
]



self.tgtImpDir = ko.observable();

self.tgtImpParallel = ko.observable(5);
self.pdbRegList =ko.observableArray([]);

self.createJob = function(){
    if (self.ZDTChk() == true){
            self.AddExtractMsg([]);
            self.pdbRegList([]);
            var extName = 'E' + self.LoadName() + 'P'
            self.trailSubDirSlash('/');
            self.TrailName('ZP');
            self.trailSize('500');
            self.startExtChk(false);
            self.pdbRegList.push(self.pdbList());

            document.querySelector('#CreateExtractDialog').open();
            console.log(self.dbMainVersion())
            console.log(self.dbMinorVersion())
if(self.dbMainVersion() == 11 &&  self.dbMinorVersion() <4 )
{
    console.log('Inside CE')
    self.currentTrailType('exttrail');
    self.newExtParamList('EXTRACT ' + extName + '\n' + 'useridalias ' + self.SRCcurrentPDB() + ' domain ' + self.selectedSRCDomCategory() + '\n' + 'exttrail ' +  self.trailSubDir() + self.trailSubDirSlash() + self.TrailName()  + '\nREPORTCOUNT EVERY 5 MINUTES, RATE\nTRANLOGOPTIONS DBLOGREADER\nTRANLOGOPTIONS _DISABLESTREAMLINEDDBLOGREADER\n'  + self.currentSchemaParam() + self.ExtSchemaParam() );
    $.ajax({
        url: self.SRConepDepUrl() + "/ggaddce",
        type: 'POST',
        data: JSON.stringify({
            extname: extName,
            extdesc: '',
            domain: self.selectedSRCDomCategory(),            
            alias: self.SRCcurrentPDB(),
            mode: 'TRANLOG',
            threads: 1,
            beginmode: self.currentbeginmode(),
            trailtype: self.currentTrailType(),
            trailsubdir: self.trailSubDir(),
            trailsubdirslash: self.trailSubDirSlash(),
            trail: self.TrailName(),
            trailsize: self.trailSize(),
            currentExtParamList: self.newExtParamList(),
            startExtChk: self.startExtChk(),
            regExtChk: 'True'
        }),
        dataType: 'json',
        timeout: sessionStorage.getItem("timeInetrval"),
        context: self,
        error: function (xhr, textStatus, errorThrown) {
            if(textStatus == 'timeout'){
                document.querySelector('#Timeout').open();
            }
        },
        success: function (data) {
            document.querySelector('#CreateExtractDialog').close();
            self.dialogTitle('Integrated Extract ' + self.ExtName());
            document.querySelector('#AddExtractDialog').open();
            self.AddExtractMsg(data[0]);
            return self;
        }

    })

}

else
{
    console.log('Inside IE')
    if (self.SRConepDepUrl() == self.TGTonepDepUrl())
    {
        self.currentTrailType('exttrail');
        if (self.CDBCheck()=='YES') {
        self.newExtParamList('EXTRACT ' + extName + '\n' + 'useridalias ' + self.SRCcurrentPDB() + ' domain ' + self.selectedSRCDomCategory() + '\n' + 'exttrail ' +  self.trailSubDir() + self.trailSubDirSlash() + self.TrailName()  + '\n' + 'REPORTCOUNT EVERY 5 MINUTES, RATE' + '\n' + 'SOURCECATALOG ' + self.pdbList() + '\n' + self.currentSchemaParam() + self.ExtSchemaParam() );
        }
        else{
            self.newExtParamList('EXTRACT ' + extName + '\n' + 'useridalias ' + self.SRCcurrentPDB() + ' domain ' + self.selectedSRCDomCategory() + '\n' + 'exttrail ' +  self.trailSubDir() + self.trailSubDirSlash() + self.TrailName()  + '\n' + 'REPORTCOUNT EVERY 5 MINUTES, RATE' + '\n' + self.currentSchemaParam() + self.ExtSchemaParam() );
        }
    }
    else {
        self.currentTrailType('exttrail');
        if (self.CDBCheck()=='YES') {
            self.newExtParamList('EXTRACT ' + extName + '\n' + 'useridalias ' + self.SRCcurrentPDB() + ' domain ' + self.selectedSRCDomCategory() + '\n' + 'exttrail ' +  self.trailSubDir() + self.trailSubDirSlash() + self.TrailName()  + '\n' +  'REPORTCOUNT EVERY 5 MINUTES, RATE' + '\n' + 'SOURCECATALOG ' + self.pdbList() + '\n' + self.currentSchemaParam() + self.ExtSchemaParam() ) ;
            }
            else{
                self.newExtParamList('EXTRACT ' + extName + '\n' + 'useridalias ' + self.SRCcurrentPDB() + ' domain ' + self.selectedSRCDomCategory() + '\n' + 'exttrail ' +  self.trailSubDir() + self.trailSubDirSlash() + self.TrailName()  + '\n' +  'REPORTCOUNT EVERY 5 MINUTES, RATE' + '\n' + self.currentSchemaParam() + self.ExtSchemaParam()) ;
            }

    }

            $.ajax({
                url: self.SRConepDepUrl() + "/ggaddie",
                type: 'POST',
                data: JSON.stringify({
                    regExtChk: 'True',
                    regVal: 'now',
                    lmDictSCN: '',
                    currentShareOpt: '',
                    CaptureName: '',
                    extname: extName ,
                    extdesc: '',
                    domain: self.selectedSRCDomCategory(),
                    alias: self.SRCcurrentPDB(),
                    mode: self.currentExtType(),
                    beginmode: 'Begin Now',
                    trailtype: self.currentTrailType(),
                    trailsubdir: self.trailSubDir(),
                    trailsubdirslash: self.trailSubDirSlash(),
                    trail: self.TrailName(),
                    trailsize: self.trailSize(),
                    currentExtParamList: self.newExtParamList(),
                    startExtChk: self.startExtChk(),
                    CDBCheck: self.CDBCheck(),
                    PDBName: self.pdbList(),
                    pdbSelList: self.pdbRegList()
                }),
                dataType: 'json',
                timeout: sessionStorage.getItem("timeInetrval"),
                context: self,
                error: function (xhr, textStatus, errorThrown) {
                    if(textStatus == 'timeout'){
                        document.querySelector('#Timeout').open();
                    }
                },
                success: function (data) {
                    document.querySelector('#CreateExtractDialog').close();
                    document.querySelector('#AddExtractDialog').open();
                    self.AddExtractMsg(data[0]);

                    console.log(self.AddExtractMsg())
                    return self;
                }
            })
        }
    }
    else {
        addAutoILProc();
    }
}
self.AddExtractOKClose = function () {
    document.querySelector('#AddExtractDialog').close();
    if (self.AddExtractMsg().toString().includes('ERROR')) {
    }
    else {
        currTransaction();
        }
};

self.currTxnRefresh = function(){
    currTransaction();
}

self.startExportJob = function(){
    addAutoILProc();
}


function addAutoILProc(){
    console.log('Inside AddAuto')
    document.querySelector('#expdpOptDialog').close();
    document.querySelector('#expdpJob').open();
    console.log(self.pdbList())
    $.ajax({
        url: self.SRConepDepUrl() + "/expdp",
        type: 'POST',
        data: JSON.stringify({
            srcDep : self.SrcOnePDepName(),
            tgtDep : self.TgtOnePDepName(),
            srcdbName : self.SRCcurrentPDB(),
            jobName : self.LoadName(),
            schemas : self.schemaList(),
            srcDirName : self.srcExpDir(),
            expParallel : self.srcExpParallel(),
            contentOpt : self.srcContents(),
            compOpt : self.srcCompression(),
            compAlgo : self.srcCompAlgo(),
            AWSBucket: self.AWSBucket(),
            aws_access_key_id : self.AccessKeyID(),
            aws_secret_access_key : self.AccessKey(),
            tgtDirName : self.tgtImpDir(),
            impParallel : self.tgtImpParallel(),
            tgtdbName : self.TGTcurrentPDB(),
            currentSCN : self.dbDetList()[0].current_scn,
            cdbCheck: self.CDBCheck(),
            pdbName : self.pdbList(),
            tabExclude : self.currentexpExcludeParam(),
            remapSchema : self.remapSchema()[0],
            reMapSchemaNameListDisp : self.reMapSchemaNameListDisp(),
            remapTgtSchemaNames : self.remapTgtSchemaNames(),
            remapTableSpaces : self.remapTableSpaces()[0],
            reMapTablespaceListDisp : self.reMapTablespaceListDisp(),
            remapTgtTableSpaceNames : self.remapTgtTableSpaceNames()
        }),
        dataType: 'json',
        timeout: sessionStorage.getItem("timeInetrval"),
        context: self,
                    error: function (xhr, textStatus, errorThrown) {
                        if(textStatus == 'timeout' || textStatus == 'error'){
                            document.querySelector('#expdpJob').close();
                            document.querySelector('#TimeoutInLoad').open();
                        }
                    },
        success: function (data) {
            document.querySelector('#expdpJob').close();
            self.router.go({ path: 'expinitmon', params: { jobName : self.LoadName() } })
            return self;
            
        }

    })
}




                self.connected = function () { 
                    if (sessionStorage.getItem("userName")==null) {
                        self.router.go({path : 'signin'});
                    }
                    else
                    {
                    app.onAppSuccess();
                    getOnepDep();
                    self.selectedSRCAliascategory('');
                    self.selectedSRCUsercategory('');
                    self.selectedTGTAliascategory('');
                    self.selectedTGTUsercategory('');
                    self.ExtoptParam([]);
                    self.RepoptParam([]);
                    self.onepDepList([]);
                    self.selectedStepValue('stp1');
                    self.selectedStepLabel('DataSource');
                    self.selectedStepFormLabel('DataSource');
                    self.currentExtType('SOURCEISTABLE');
                    self.ExtName('');
                    self.ExtDesc('');
                    self.currentbeginmode('Begin Now');
                    self.trailSubDir('');
                    self.TrailName('');
                    self.regVal('now');
                    self.regExtChk(true);
                    self.CDBCheck('');
                    self.ButtonVal(true);
                    self.pdbList([]);
                    self.SrcOnePDepName('');
                    self.TgtOnePDepName('');
                    self.remapSchema(["no"]);
                    self.remapTableSpaces(["no"]);
                    self.remapTgtTableSpaceNames('');
                    self.remapTgtSchemaNames('');
                    }
                }

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

                };
            }
        }
            return  InitialLoadViewModel;
        }
);