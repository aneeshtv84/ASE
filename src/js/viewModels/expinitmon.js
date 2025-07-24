define(['ojs/ojcore', 'knockout', 'jquery', 'appController', 'ojDiagram/viewModels/ggLayout', 'ojs/ojknockout-keyset',
'ojs/ojattributegrouphandler', 'ojs/ojconverter-number', 'ojs/ojconverterutils-i18n', 'ojs/ojconverter-datetime',
'ojs/ojarraydataprovider', 'ojs/ojarraytreedataprovider',"ojs/ojpagingdataproviderview", 'ojs/ojinputnumber', 'ojs/ojdatetimepicker', 'ojs/ojinputtext', 'ojs/ojformlayout',
'ojs/ojknockout', 'ojs/ojactioncard', 'ojs/ojdiagram', 'ojs/ojdialog', 'ojs/ojprogress-bar', 'ojs/ojselectcombobox', 'ojs/ojtable',
'ojs/ojselectsingle', 'ojs/ojradioset', "ojs/ojinputsearch" ,"ojs/ojcollapsible","ojs/ojpagingcontrol",'ojs/ojbutton', 'ojs/ojvalidationgroup'],
function (oj, ko, $, app, layout, keySet, attributeGroupHandler, NumberConverter, ConverterUtilsI18n, DateTimeConverter,ArrayDataProvider, ArrayTreeDataProvider,PagingDataProviderView,ojButtonEventMap) {

  class InitManageViewModel {
    constructor(args) {
      //console.log(args)
      var self = this;
      self.DepName = args.routerState.detail.dep_url;

      self.ILJobData = ko.observableArray([]);
      self.CancelBehaviorOpt = ko.observable('icon');
      self.expState = ko.observable();
      self.expPercentage = ko.observable(0);
      self.currentILJOb = ko.observable();
      self.isFormReadonly = ko.observable(false);
      self.xfrPercent = ko.observableArray([]);
      self.enableExpdp = ko.observable(true);
      self.enableXFR = ko.observable(false);
      self.enableDownload = ko.observable(false);
      self.enableImpdp = ko.observable(false);
      self.enableSummary = ko.observable(false);
      self.downloadPercent = ko.observableArray([]);
      self.impPercentage = ko.observable(0);
      self.impState = ko.observable();
      self.summaryData = ko.observableArray([]);
      self.ExpReport = ko.observableArray([]);
      self.ImpReport = ko.observableArray([]);
      self.downloadS3Report = ko.observableArray([]);
      self.flashbackSCN = ko.observable();
      var reportArray=['transferS3Report','downloadS3Report','ExpReport','ImpReport'];
      self.title = ko.observable();
      self.groupValid = ko.observable();


      self.SRCcurrentPDB = ko.observable();
      self.TGTcurrentPDB = ko.observable();

      //AWS Credentials

self.AWSBucket = ko.observable();
self.AccessKeyID = ko.observable();
self.AccessKey = ko.observable();

      function getILData() {
        self.ILJobData([]);
        $.ajax({
          url: self.DepName() + '/expimpjob',
          type: 'GET',
          dataType: 'json',
          timeout: sessionStorage.getItem("timeInetrval"),
          error: function (xhr, textStatus, errorThrown) {
            if (textStatus == 'timeout' || textStatus == 'error') {
   //           document.querySelector('#TimeoutMon').open();
            }
          },
          success: function (data) {
            for (var i = 0; i < data[0].length; i++) {
              self.ILJobData.push({ 'label': data[0][i] , 'value' :  data[0][i]});
            }
            return self;
          }
        })
      }

      self.SrcDepUrl = ko.observable();
      self.TgtDepUrl = ko.observable();

self.getILTables =    function (event,data)  {
  if (self.currentILJOb()){
    self.SrcDepUrl('');
    self.TgtDepUrl('');
      $.ajax({
        url: self.DepName() + '/expdpmon',
        type: 'POST',
        data: JSON.stringify({
          jobName : self.currentILJOb()
      }),
        timeout: sessionStorage.getItem("timeInetrval"),
        error: function (xhr, textStatus, errorThrown) {
          // console.log(textStatus)
          if (textStatus == 'timeout' || textStatus == 'error') {
//            document.querySelector('#TimeoutMon').open();
          }
        },
        success: function (data) {
          self.SrcDepUrl(data[5]);
          self.TgtDepUrl(data[6]);
          self.ExpReport([]);
          self.summaryData([]);
          self.title('');
          self.expState('');
          self.expPercentage('');
          self.flashbackSCN('');
          document.getElementById('enableExpdpPanel').style.display = "block";
          self.flashbackSCN(data[4]);
          self.expPercentage(data[0]['DONE']);
          self.expState(data[0]['STATE']);
          if (self.expPercentage()==100 &&  self.expState()=='COMPLETED'){
            self.enableExpdp(false);
            self.enableXFR(true);
            self.enableImpdp(false);
            self.xfrPercent([]); 
            document.getElementById("transer_data").style.display="block";
            for (var i = 0; i < data[1].length; i++) {
              var percent = parseInt(data[1][i].Percent,10)
              self.xfrPercent.push({ 'name': data[1][i].fileName ,  'percent':percent });
            }
            if (data[7] == 'YES'){
              self.enableExpdp(false);
              self.enableXFR(false);
              self.enableImpdp(true);
              document.getElementById("import_data").style.display="block";
              self.impPercentage('');
              self.impState('');
              self.impPercentage(data[2].DONE);
              self.impState(data[2].STATE);
            if (self.impPercentage() == 100 && self.impState() == 'COMPLETED' ){
              self.enableExpdp(false);
              self.enableXFR(false);
              self.enableDownload(false);
              self.enableImpdp(false);
              self.enableSummary(true);
              self.summaryData([]);
              for (var key in data[3]) {
              self.summaryData.push({'TabName' : key , 'expRows' : data[3][key].ExportRows , 'impRows' : data[3][key].ImportRows})
            }
            document.getElementById("summary_data").style.display="block";
            // console.log(self.summaryData())
            self.xfrPercent.valueHasMutated();
            self.summaryData.valueHasMutated();
          }
       }
      }
  
          return self;
        }
        
      })
    }
  }

  self.summaryDatacolumnArray = [{headerText: 'Table Name',
  field: 'TabName'},
  {headerText: 'Exported Rows',
  field: 'expRows'},
  {headerText: 'Imported Rows',
  field: 'impRows'}
]

  self.XFRDP = ko.observable(new ArrayDataProvider(self.xfrPercent, {keyAttributes: "name"}));

  self.DownloadDP = ko.observable(new ArrayDataProvider(self.downloadPercent, {keyAttributes: "name"}));

  self.summaryDataDP = ko.observable(new PagingDataProviderView(new ArrayDataProvider(self.summaryData, {idAttribute: "TabName"})));

     var monAll;

     self.ILjobDP = ko.observable(new ArrayDataProvider(self.ILJobData, { keyAttributes: 'id' }));


self.clickTshoot = function(){
  importTshoot();
}

    self.impResumableTask = ko.observableArray([]);
    self.impLockStatus = ko.observableArray([]);
    self.impWaitStatus = ko.observableArray([]);
    self.impLongOps = ko.observableArray([]);

   
function importTshoot() {
  if(self.currentILJOb()){
  $.ajax({
    url: self.TgtDepUrl() + '/tshootimpdp',
    type: 'POST',
    data: JSON.stringify({
      jobName : self.currentILJOb()
  }),
    timeout: sessionStorage.getItem("timeInetrval"),
    error: function (xhr, textStatus, errorThrown) {
      if (textStatus == 'timeout' || textStatus == 'error') {
    //    document.querySelector('#TimeoutMon').open();
      }
    },
    success: function (data) {
      self.title('Monitor Import Session');
      document.getElementById('ExpReport').style.display="none";
      document.getElementById('XFRReport').style.display="none";
      document.getElementById('tshoot').style.display="block";
      self.impResumableTask([]);
      for (var i = 0; i < data[0].length; i++) {
        self.impResumableTask.push({'Session_ID' :  data[0][i].SESSION_ID,'Status' : data[0][i].STATUS, 'Start_Time' :  data[0][i].START_TIME, 'Suspend_Time' : data[0][i].SUSPEND_TIME,'Resume_Time' : data[0][i].RESUME_TIME,'Error_Msg' : data[0][i].ERROR_MSG ,'Sql_Text' : data[0][i].SQL_TEXT})
      }
      self.impResumableTask.valueHasMutated();
      self.impLockStatus([]);
      for (var i = 0; i < data[1].length; i++) {
        self.impLockStatus.push({'Waiting_Session' : data[1][i].WAITING_SESSION,'Holding_Session' :  data[1][i].HOLDING_SESSION,'Serial' : data[1][i].SERIAL, 'Event' :  data[1][i].EVENT, 'W_Program' : data[1][i].WPROGRAM,'B_Program' : data[1][i].BPROGRAM,'W_Module' : data[1][i].WMOD,'B_Module' : data[1][i].BMOD,'Lock_ID': data[1][i].LOCK_ID1})
      }
      self.impLockStatus.valueHasMutated();
      self.impWaitStatus([]);
      for (var i = 0; i < data[2].length; i++) {
        self.impWaitStatus.push({'Session_ID' : data[2][i].SID,'Program' : data[2][i].PROG,'Wait_Sequence' :  data[2][i].SEQ,'Event' : data[2][i].EVENT, 'Wait_Time' :  data[2][i].WAIT_TIME, 'SECONDS_IN_WAIT' : data[2][i].SECONDS_IN_WAIT,'STATE' : data[2][i].STATE,'P1TEXT' : data[2][i].P1TEXT,'P1' : data[2][i].P1,'P2TEXT': data[2][i].P2TEXT ,'P2' : data[2][i].P2 , 'P3TEXT' : data[2][i].P3TEXT , 'P3' :  data[2][i].P3 })
      }
      self.impWaitStatus.valueHasMutated();
      self.impLongOps([]);
      for (var i = 0; i < data[3].length; i++) {
        self.impLongOps.push({'jobName' : data[3][i].JOB_NAME,'State' : data[3][i].STATE,'Workers' : data[3][i].WORKERS,'MESSAGE' :  data[3][i].MESSAGE,'DONE' : data[3][i].DONE,'TIME_REMAINING' : data[3][i].TIME_REMAINING})
      }
      self.impLongOps.valueHasMutated();
      //document.querySelector('#TshootDialog').open();
      return self;
    }
  })
}
}

self.impResumableTaskDP = ko.observable(new PagingDataProviderView(new ArrayDataProvider(self.impResumableTask, {keyAttributes: "Session_ID"})));
self.impLockStatusDP = ko.observable(new PagingDataProviderView(new ArrayDataProvider(self.impLockStatus, {keyAttributes: "Holding_Session"})));
self.impWaitStatusDP = ko.observable(new PagingDataProviderView(new ArrayDataProvider(self.impWaitStatus, {keyAttributes: "Session_ID"})));
self.impLongOpsDP = ko.observable(new PagingDataProviderView(new ArrayDataProvider(self.impLongOps, {keyAttributes: "jobName"})));

self.resumableTaskcolumnArray = [
{headerText: 'Session ID',
field: 'Session_ID'},
{headerText: 'Status',
field: 'Status'},
{headerText: 'Start Time',
field: 'Start_Time'},
{headerText: 'Suspended Time',
field: 'Suspend_Time'},
{headerText: 'Resume Time',
field: 'Resume_Time'},
{headerText: 'Error',
field: 'Error_Msg'},
{headerText: 'SQL Text',
field: 'Sql_Text'}
]

self.impLongOpscolumnArray = [{headerText: 'Job Name',
field: 'jobName'},
{headerText: 'State',
field: 'State'},
{headerText: 'Workers',
field: 'Workers'},
{headerText: 'Message',
field: 'MESSAGE'},
{headerText: 'Percentage Done',
field: 'DONE'},
{headerText: 'Time Remaining',
field: 'TIME_REMAINING'}
]

self.lockStatuscolumnArray = [{headerText: 'Waiting Session',
field: 'Waiting_Session'},
{headerText: 'Holding Session',
field: 'Holding_Session'},
{headerText: 'Serial#',
field: 'Serial'},
{headerText: 'Wait Event',
field: 'Event'},
{headerText: 'Waiting Program',
field: 'W_Program'},
{headerText: 'Blocking Program',
field: 'B_Program'},
{headerText: 'Waiting Module',
field: 'W_Module'},
{headerText: 'Blocking Module',
field: 'B_Module'},
{headerText: 'Lock ID',
field: 'Lock_ID'}
]

self.waitStatuscolumnArray = [{headerText: 'Session ID',
field: 'Session_ID'},
{headerText: 'Program',
field: 'Program'},
{headerText: 'Wait sequence',
field: 'Wait_Sequence'},
{headerText: 'Wait Event',
field: 'Event'},
{headerText: 'Last Wait Time',
field: 'Wait_Time'},
{headerText: 'Seconds in Wait',
field: 'SECONDS_IN_WAIT'},
{headerText: 'State',
field: 'STATE'},
{headerText: 'P1 Text',
field: 'P1TEXT'},
{headerText: 'P1',
field: 'P1'},
{headerText: 'P2 Text',
field: 'P2TEXT'},
{headerText: 'P2',
field: 'P2'},
{headerText: 'P3 Text',
field: 'P3TEXT'},
{headerText: 'P3',
field: 'P3'},
]

self.xfrDataColumnArray = [{headerText: 'Dump File',
field: 'name'},
{headerText: 'Percent',
field: 'percent'},
{headerText: 'Elapsed Time',
field: 'elapTime'},
{headerText: 'Transfer Speed',
field: 'XFRSpeed'},
{headerText: 'Total Bytes',
field: 'TotalBytes'},
{headerText: 'Transfered Bytes',
field: 'XFRBytes'},
{headerText: 'ETA',
field: 'XFReta'}]


    function downLoadFromS3() {
      $.ajax({
        url: self.DepName() + '/downloadfroms3',
        type: 'POST',
        data: JSON.stringify({
          jobName : self.currentILJOb()
      }),
        timeout: sessionStorage.getItem("timeInetrval"),
        error: function (xhr, textStatus, errorThrown) {
          if (textStatus == 'timeout' || textStatus == 'error') {
   //         document.querySelector('#TimeoutMon').open();
          }
        },
        success: function (data) {
    //            console.log('downLoadFromS3')
          return self;
        }
      })

    }



    function readExportLog() {
      document.querySelector('#Working').open();
      $.ajax({
        url: self.SrcDepUrl()  + '/readexportlog',
        type: 'POST',
        data: JSON.stringify({
          jobName : self.currentILJOb()
      }),
        timeout: sessionStorage.getItem("timeInetrval"),
        error: function (xhr, textStatus, errorThrown) {
        
        },
        success: function (data) {
          self.ExpReport([]);
          for(var i = 0; i<data[0].length; i++){
          self.ExpReport.push({'name' : data[0][i]});
          }
          self.ExpReport.valueHasMutated();
          self.title('View Export Log');
          reportView();
          document.querySelector('#Working').close();
         // document.querySelector('#ViewExportRptDialog').open();
        }
      })

    }

    function reportView(){
      document.getElementById('tshoot').style.display="none";
      document.getElementById('XFRReport').style.display="none";
      document.getElementById('ExpReport').style.display="block";
    }

    function xfrView(){
      document.getElementById('tshoot').style.display="none";
      document.getElementById('ExpReport').style.display="none";
      document.getElementById('XFRReport').style.display="block";
    }

    function readImportLog() {
      document.querySelector('#Working').open();
      
      $.ajax({
        url: self.TgtDepUrl() + '/readimportlog',
        type: 'POST',
        data: JSON.stringify({
          jobName : self.currentILJOb()
      }),
        timeout: sessionStorage.getItem("timeInetrval"),
        error: function (xhr, textStatus, errorThrown) {
        
        },
        success: function (data) {
          self.ImpReport([]);
         self.ExpReport([]);
          for(var i = 0; i<data[0].length; i++){
          self.ImpReport.push({'name' : data[0][i]});
          self.ExpReport.push({'name' : data[0][i]});
          }
          self.ImpReport.valueHasMutated();
          self.ExpReport.valueHasMutated();
          reportView();
          self.title('View Import Log');
              document.querySelector('#Working').close();
             // document.querySelector('#ViewImportRptDialog').open();
        }
      })

    }

    self.exportReportAction = () => {
      readExportLog();
    };

    self.importReportAction = () => {
      readImportLog();
    };

    self.downloadS3ReportAction =  function (data,event) {
      document.querySelector('#Working').open();
      $.ajax({
        url: self.DepName() + '/downloads3log',
        type: 'POST',
        data: JSON.stringify({
          jobName : self.currentILJOb()
      }),
        timeout: sessionStorage.getItem("timeInetrval"),
        error: function (xhr, textStatus, errorThrown) {
        
        },
        success: function (data) {
          self.downloadS3Report([]);
          self.ExpReport([]);
          for(var i = 0; i<data[0].length; i++){
          self.downloadS3Report.push({'name' : data[0][i].TEXT});
          self.ExpReport.push({'name' : data[0][i].TEXT});
          }
          self.downloadS3Report.valueHasMutated();
          self.ExpReport.valueHasMutated();
          reportView();
          self.title('View Download from S3 to RDS Log');
              document.querySelector('#Working').close();
              //document.querySelector('#ViewDownloadS3RptDialog').open();
        }
      })

    }

    self.transferS3Report = ko.observableArray([]);

    self.S3transferReportAction =  function (data,event) {
      document.querySelector('#Working').open();
      $.ajax({
        url: self.TgtDepUrl() + '/s3transferlog',
        type: 'POST',
        data: JSON.stringify({
          jobName : self.currentILJOb(),
          src_dep_url : self.SrcDepUrl()
      }),
        timeout: sessionStorage.getItem("timeInetrval"),
        error: function (xhr, textStatus, errorThrown) {
        
        },
        success: function (data) {
          self.transferS3Report([]);
          for (var i = 0; i < data[0].length; i++) {
            var percent = parseInt(data[0][i].Percent,10)
            self.transferS3Report.push({ 'name': data[0][i].fileName ,  'percent':percent ,'elapTime' : data[0][i].elapTime , 'XFRSpeed' : data[0][i].XFRSpeed ,'TotalBytes': data[0][i].TotalBytes,'XFRBytes' : data[0][i].XFRBytes , 'XFReta' : data[0][i].XFReta  });
          }
          self.transferS3Report.valueHasMutated();
          xfrView();
          self.title('View Transfer to Target Database Log');
              document.querySelector('#Working').close();
             // document.querySelector('#transferS3ReportDialog').open();
        }
      })

    }


    self.transferS3RptOKClose =  function (event) {
      document.querySelector('#transferS3ReportDialog').close();
  };

    self.ViewExportRptOKClose = function (event) {
      document.querySelector('#ViewExportRptDialog').close();
  };
  self.ViewImportRptOKClose = function (event) {
    document.querySelector('#ViewImportRptDialog').close();
};

self.ViewDownloadS3RptOKClose = function (event) {
  document.querySelector('#ViewDownloadS3RptDialog').close();
};

self.S3ConfigActionOpen = function (event) {
  document.querySelector('#UpdateS3Config').open();
};

self.UpdateS3ConfigLog = ko.observableArray([]);

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

self.UpdateS3ConfigOKClose = function (data,event) {
  var valid = self._checkValidationGroup("UpdateS3ConfigForm");
     if (valid) {
  document.querySelector('#Working').open();
  $.ajax({
    url: self.DepName() + '/updates3config',
    type: 'POST',
    data: JSON.stringify({
      jobName : self.currentILJOb(),
      bucketName : self.AWSBucket(),
      aws_access_key_id :  self.AccessKeyID(),
      aws_secret_access_key : self.AccessKey()
  }),
    timeout: sessionStorage.getItem("timeInetrval"),
    error: function (xhr, textStatus, errorThrown) {
    
    },
    success: function (data) {
      self.UpdateS3ConfigLog([]);
      for(var i = 0; i<data[0].length; i++){
      self.UpdateS3ConfigLog.push({'name' : data[0][i]});
      }
      self.UpdateS3ConfigLog.valueHasMutated();
          document.querySelector('#Working').close();
          document.querySelector('#UpdateS3Config').close();
          document.querySelector('#UpdateS3SuccessDialog').open();
    }
  })
}

}

self.transferS3ReportDP = ko.observable(new ArrayDataProvider(self.transferS3Report, {keyAttributes: "name"}));
self.UpdateS3ConfigLogDP = ko.observable(new ArrayDataProvider(self.UpdateS3ConfigLog, {keyAttributes: "name"}));

  self.downloadS3LogDP = ko.observable(new ArrayDataProvider(self.downloadS3Report, {keyAttributes: "name"}));
  self.expLogDP = ko.observable(new ArrayDataProvider(self.ExpReport, {keyAttributes: "name"}));
  self.impLogDP = ko.observable(new ArrayDataProvider(self.ImpReport, {keyAttributes: "name"}));
  


     monAll = setInterval(self.getILTables, 25000);
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
          self.currentILJOb(args.params.jobName);
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
        clearInterval(monAll);
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