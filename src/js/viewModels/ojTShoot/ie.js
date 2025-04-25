
define(['knockout', 'jquery','appController' ,'ojs/ojarraydataprovider', 'ojs/ojbutton', 'ojs/ojtable','ojs/ojprogress-bar', 'ojs/ojselectcombobox',
'ojs/ojdialog', 'ojs/ojinputtext', 'ojs/ojselectsingle','ojs/ojformlayout'],
function (ko, $, app, ArrayDataProvider) {

    class ietshootViewModel {
        constructor(context){
        var self = this;
        self.DepName = context.DepName;
        self.DBMainVer = ko.observable();
        self.DBMinorVer = ko.observable();
        self.IEStats = ko.observableArray([]);
        self.IEMem = ko.observableArray([]);
        self.IEParams = ko.observableArray([]);
        self.IEStreams = ko.observableArray([]);
        self.IEStreamsStats =  ko.observableArray([]);
        self.IELogmnrMem = ko.observableArray([]);
        self.IELongRun = ko.observableArray([]);
        self.IEReader = ko.observableArray([]);
        self.IEBuilder = ko.observableArray([]);
        self.IEPreparer = ko.observableArray([]);
        self.IEDBDet = ko.observableArray([]);
        self.DBDet = ko.observableArray([]);
        self.currentDB = ko.observable();
        self.LogmnrStats = ko.observableArray([]);
        self.IEMerger = ko.observableArray([]);
        self.IEReaderASH = ko.observableArray([]);

        self.ButtonVal = ko.observable(true);

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

        function getDB() {
            self.DBDet([]);
            $.ajax({
                url: self.DepName() + "/dbdet",
                type: 'GET',
                dataType: 'json',
                context: self,
                error: function (e) {
                    //console.log(e);
                },
                success: function (data) {
                    for (var i = 0; i < data[0].length; i++) {
                        self.DBDet.push({'value' : data[0][i].dbname, 'label' : data[0][i].dbname});
                }
                self.ButtonVal(true);
            }
            })
        }



        self.DBDetDP = new ArrayDataProvider(self.DBDet, {keyAttributes: 'value'});


        self.OPError = ko.observableArray([]);

    self.IETShoot =     function(data,event) {
        document.querySelector('#getExtractTshoot').open();
            self.OPError([]);
            self.IEStats([]);
            self.IEMem([]);
            self.IEParams([]);
            self.IEStreams([]);
            self.IEStreamsStats([]);
            self.IELogmnrMem([]);
            self.IELongRun([]);
            self.IEReader([]);
            self.IEBuilder([]);
            self.IEPreparer([]);
            self.IEDBDet([]);
            self.LogmnrStats([]);
            self.IEMerger([]);
            self.IEReaderASH ([]);
            $.ajax({
                url: self.DepName() + "/ietshoot",
                type: 'POST',
                data: JSON.stringify({
                    dbname: self.currentDB()
                }),
                dataType: 'json',
                context: self,
                error: function (e) {
                    //console.log(e);
                },
                success: function (data) {
                    if (data[0].includes('ORA-')){
                        document.querySelector('#getExtractTshoot').close();
                        document.querySelector('#ErrorLoad').open();
                            self.OPError.push(data[0]);
                       //console.log(self.OPError())
                    }
                    else{

                    for (var i = 0; i < data[0].length; i++) {
                        self.IEStats.push({'CURRENT_TIME' : data[0][i].CURRENT_TIME,
                        'SOURCE_DATABASE': data[0][i].SOURCE_DATABASE,
                        'INST_ID' : data[0][i].INST_ID , 
                        'EXTRACT_NAME': data[0][i].EXTRACT_NAME,
                        'CAPTURE_NAME':data[0][i].CAPTURE_NAME,
                        'STATUS': data[0][i].STATUS,
                        'STATE': data[0][i].STATE,
                        'CAPTURE_LAG': data[0][i].CAPTURE_LAG,
                        'CAPTURE_TYPE':data[0][i].CAPTURE_TYPE,
                        'CAPTURE_USER' : data[0][i].CAPTURE_USER ,
                        'LOGMINER_ID': data[0][i].LOGMINER_ID,
                        'REAL_TIME_MINE': data[0][i].REAL_TIME_MINE, 
                        'VERSION': data[0][i].VERSION, 
                        'REQUIRED_CHECKPOINT_SCN': data[0][i].REQUIRED_CHECKPOINT_SCN, 
                        'PROTOCOL': data[0][i].PROTOCOL, 
                        'REGISTERED': data[0][i].REGISTERED,
                        'MINED_MB': parseFloat(data[0][i].MINED_MB).toFixed(2), 
                        'SENT_MB': parseFloat(data[0][i].SENT_MB).toFixed(2), 
                        'STARTUP_TIME': data[0][i].STARTUP_TIME, 
                        'LAST_DDL_TIME': data[0][i].LAST_DDL_TIME });
                    }
                    self.IEStats.valueHasMutated();
                    for (var i = 0; i < data[2].length; i++) {
                        self.IEMem.push({'AVAILABLE_TXN': data[2][i].AVAILABLE_TXN,
                            'BUILDER_WORK_SIZE': data[2][i].BUILDER_WORK_SIZE,
                            'DELIVERED_TXN':  data[2][i].DELIVERED_TXN,
                            'DIFFERENCE':  data[2][i].DIFFERENCE,
                            'MAX_MEMORY_SIZE':  data[2][i].MAX_MEMORY_SIZE,
                            'PREPARED_WORK_SIZE':  data[2][i].PREPARED_WORK_SIZE,
                            'SESSION_NAME':  data[2][i].SESSION_NAME,
                            'USED_MEMORY_SIZE':  data[2][i].USED_MEMORY_SIZE,
                            'USED_MEM_PCT':  parseFloat(data[2][i].USED_MEM_PCT).toFixed(2)});
                    }
                    self.IEMem.valueHasMutated();
                    for (var i = 0; i < data[1].length; i++) {
                    self.IEParams.push({'CAPTURE_NAME': data[1][i].CAPTURE_NAME,
                                        'CHECKPOINT_FREQUENCY': data[1][i].CHECKPOINT_FREQUENCY,
                                        'EXCLUDETAG': data[1][i].EXCLUDETAG,
                                        'EXCLUDEUSER': data[1][i].EXCLUDEUSER,
                                        'EXTRACT_NAME': data[1][i].EXTRACT_NAME,
                                        'GETAPPLOPS': data[1][i].GETAPPLOPS,
                                        'GETREPLICATES': data[1][i].GETREPLICATES,
                                        'MAX_SGA_SIZE': data[1][i].MAX_SGA_SIZE,
                                        'PARALLELISM': data[1][i].PARALLELISM});
                    }
                    self.IEParams.valueHasMutated();
                    for (var i = 0; i < data[3].length; i++) {
                        self.IEStreams.push({'INST_ID': data[3][i].INST_ID,
                                                'MAX_MB': parseFloat(data[3][i].MAX_MB).toFixed(2),
                                                'PCT_STREAMS_POOL': parseFloat(data[3][i].PCT_STREAMS_POOL).toFixed(2),
                                                'USED_MB': parseFloat(data[3][i].USED_MB).toFixed(2)
                                                                    });
                                                                }
                    self.IEStreams.valueHasMutated();
                    for (var i = 0; i < data[4].length; i++) {
                        self.IEStreamsStats.push({
                                                'ALLOCED': parseFloat(data[4][i].ALLOCED).toFixed(2),
                                                'CAPTURE_NAME': data[4][i].CAPTURE_NAME,
                                                'MSGS_CAPTURED': data[4][i].MSGS_CAPTURED,
                                                'MSGS_ENQUEUED': data[4][i].MSGS_ENQUEUED,
                                                'PCT': parseFloat(data[4][i].PCT).toFixed(2),
                                                'USED': parseFloat(data[4][i].USED).toFixed(2)
                    });
                }
                self.IEStreamsStats.valueHasMutated();


                    for (var i = 0; i < data[5].length; i++) {
                        self.IELogmnrMem.push({
                                            'MAX_MB': data[5][i].MAX_MB,
                                            'PCT_LOGMINER_MEM_USED': parseFloat(data[5][i].PCT_LOGMINER_MEM_USED).toFixed(2),
                                            'STREAMS_POOL_SIZE' : parseFloat(data[5][i].STREAMS_SIZE),
                                            'PCT_STREAMS_POOL': Math.round(data[5][i].PCT_STREAMS_POOL) + ' %',
                                            'SESSION_NAME': data[5][i].SESSION_NAME,
                                            'USED_MB': parseFloat(data[5][i].USED_MB).toFixed(2)
                                                });
                }     
                self.IELogmnrMem.valueHasMutated();

                for (var i = 0; i < data[6].length; i++) {
                self.IELongRun.push({'INST_ID' : data[6][i].INST_ID,
                                      'SID' : data[6][i].SID,
                                      'XID': data[6][i].XID,
                                      'RUNLENGTH' :  parseFloat(data[6][i].RUNLENGTH).toFixed(2),
                                     'START_SCN' : data[6][i].START_SCN,
                                      'TERMINAL' :  data[6][i].TERMINAL,
                                      'PROGRAM' : data[6][i].PROGRAM});
                                    }
                                    self.IELongRun.valueHasMutated();

                                    for (var i = 0; i < data[7].length; i++) {
                                        self.IEReader.push({
                                            'LOGMINER_READER_NAME': data[7][i].LOGMINER_READER_NAME,
                                            'SID':data[7][i].SID,
                                            'SPID': data[7][i].SPID,
                                            'THREAD' : data[7][i].P2TEXT + ' ' + data[7][i].P2,
                                            'ARCHIVELOG' :  data[7][i].P3TEXT + ' ' + data[7][i].P3,
                                             'EVENT': data[7][i].EVENT,
                                            'LATCHSPIN': data[7][i].LATCHSPIN,
                                            'LATCHWAIT': data[7][i].LATCHWAIT,
                                            'SERIAL': data[7][i].SERIAL});                                        
                                    }

                                    self.IEReader.valueHasMutated();
                                    for (var i = 0; i < data[8].length; i++) {
                                        self.IEBuilder.push({
                                            'LOGMINER_BUILDER_NAME': data[8][i].LOGMINER_BUILDER_NAME,
                                            'SID':data[8][i].SID,
                                            'SPID': data[8][i].SPID,
                                             'EVENT': data[8][i].EVENT,
                                            'LATCHSPIN': data[8][i].LATCHSPIN,
                                            'LATCHWAIT': data[8][i].LATCHWAIT,
                                            'SERIAL': data[8][i].SERIAL});                                        
                                    }
                                    self.IEBuilder.valueHasMutated();
                                    for (var i = 0; i < data[9].length; i++) {
                                        self.IEPreparer.push({
                                            'LOGMINER_PREPARER_NAME': data[9][i].LOGMINER_PREPARER_NAME,
                                            'SID':data[9][i].SID,
                                            'SPID': data[9][i].SPID,
                                             'EVENT': data[9][i].EVENT,
                                            'LATCHSPIN': data[9][i].LATCHSPIN,
                                            'LATCHWAIT': data[9][i].LATCHWAIT,
                                            'SERIAL': data[9][i].SERIAL});                                        
                                    }
                                    self.IEPreparer.valueHasMutated();

                                    for (var i = 0; i < data[12].length; i++) {
                                        self.IEDBDet.push({
                                        'CURRENT_SCN': data[12][i].CURRENT_SCN,
                                        'DATABASE_ROLE': data[12][i].DATABASE_ROLE,
                                        'DBID': data[12][i].DBID,
                                        'DB_EDITION': data[12][i].DB_EDITION,
                                        'HOST': data[12][i].HOST,
                                        'INSTANCE': data[12][i].INSTANCE,
                                        'MIN_REQUIRED_CAPTURE_CHANGE': data[12][i].MIN_REQUIRED_CAPTURE_CHANGE,
                                        'NAME' : data[12][i].NAME,
                                        'PLATFORM_NAME': data[12][i].PLATFORM_NAME,
                                        'VERSION': data[12][i].VERSION
                                    });
                                }
                                self.IEDBDet.valueHasMutated();

                                for (var i = 0; i < data[13].length; i++) {
                                    self.LogmnrStats.push({
                                    'capture_name': data[13][i].CAPTURE_NAME,
                                    'name': data[13][i].NAME,
                                    'value': data[13][i].VALUE
                                });
                            }
                            self.LogmnrStats.valueHasMutated();

                            for (var i = 0; i < data[14].length; i++) {
                                self.IEMerger.push({
                                    'LOGMINER_MERGER_NAME': data[14][i].LOGMINER_MERGER_NAME,
                                    'SID':data[14][i].SID,
                                    'SPID': data[14][i].SPID,
                                     'EVENT': data[14][i].EVENT,
                                    'LATCHSPIN': data[14][i].LATCHSPIN,
                                    'LATCHWAIT': data[14][i].LATCHWAIT,
                                    'SERIAL': data[14][i].SERIAL});                                        
                            }
                            self.IEMerger.valueHasMutated();

                            for (var i = 0; i < data[15].length; i++) {
                                self.IEReaderASH.push({
                                    'LOGMINER_READER_NAME': data[15][i].LOGMINER_READER_NAME,
                                    'INST_ID':data[15][i].INST_ID,
                                    'EVENT_COUNT':data[15][i].EVENT_COUNT,
                                    'TOTAL_COUNT': data[15][i].TOTAL_COUNT,
                                     'PERCENTAGE': data[15][i].PERCENTAGE,
                                    'BUSY': data[15][i].BUSY,
                                    'EVENT': data[15][i].EVENT});                                        
                            }
                            self.IEReaderASH.valueHasMutated();
                            
                                document.querySelector('#getExtractTshoot').close();
                    //console.log(self);
                    return self;
                }
            }

            })

        }

        self.IEStatsDP = new ArrayDataProvider(self.IEStats, {keyAttributes: 'EXTRACT_NAME'});
        self.IEMemDP = new ArrayDataProvider(self.IEMem, {keyAttributes: 'SESSION_NAME'});
        self.IEParamsDP = new ArrayDataProvider(self.IEParams, {keyAttributes: 'CAPTURE_NAME'});
        self.IEStreamsDP = new ArrayDataProvider(self.IEStreams, {keyAttributes: 'INST_ID'});
        self.IEStreamsStatsDP = new ArrayDataProvider(self.IEStreamsStats,{keyAttributes: 'CAPTURE_NAME'});
        self.IELogmnrMemDP = new ArrayDataProvider(self.IELogmnrMem,{keyAttributes: 'SESSION_NAME'});
        self.IELongRunDP = new ArrayDataProvider(self.IELongRun,{keyAttributes: 'XID'});
        self.IEReaderDP = new ArrayDataProvider(self.IEReader,{keyAttributes: 'LOGMINER_READER_NAME'});
        self.IEMergerDP = new ArrayDataProvider(self.IEMerger,{keyAttributes: 'LOGMINER_MERGER_NAME'});
        self.IEBuilderDP = new ArrayDataProvider(self.IEBuilder,{keyAttributes: 'LOGMINER_BUILDER_NAME'});
        self.IEPreparerDP = new ArrayDataProvider(self.IEPreparer,{keyAttributes: 'LOGMINER_PREPARER_NAME'});
        self.IEDBDetDP = new ArrayDataProvider(self.IEDBDet,{keyAttributes: 'DBID'});
        self.LogmnrStatsDP = new ArrayDataProvider(self.LogmnrStats,{keyAttributes: 'capture_name'});
        self.IEReaderASHDP = new ArrayDataProvider(self.IEReaderASH,{keyAttributes: 'LOGMINER_READER_NAME'});

        self.IEStatcolumnArray = [
            {
                "headerText": "Action",
                "headerStyle": "text-align: center;",
                "style":"text-align: center; padding-top: 0px; padding-bottom: 0px;",
                "template": "actionTemplate"
            },
            {headerText: 'Current Time',
                                    field: 'CURRENT_TIME'},
                                    {headerText: 'Inst ID',
                                    field: 'INST_ID'},
                                    {headerText: 'Extract Name',
                                    field: 'EXTRACT_NAME'},
                                    {headerText: 'Status',
                                    field: 'STATUS'},
                                    {headerText: 'State',
                                    field: 'STATE'},
                                    {headerText: 'Capture Lag',
                                    field: 'CAPTURE_LAG'},
                                    {headerText: 'Mined MB',
                                    field: 'MINED_MB'},
                                    {headerText: 'Sent MB',
                                    field: 'SENT_MB'},
                                    {headerText: 'Protocol',
                                    field: 'PROTOCOL'},
                                    {headerText: 'Real Time Mine',
                                    field: 'REAL_TIME_MINE'},
                                    {headerText: 'Version',
                                    field: 'VERSION'},
                                    {headerText: 'Required Checkpoint SCN',
                                    field: 'REQUIRED_CHECKPOINT_SCN'},
                                    {headerText: 'Registered',
                                    field: 'REGISTERED'},
                                    {headerText: 'Capture Name',
                                    field: 'CAPTURE_NAME'},
                                    {headerText: 'Capture Type',
                                    field: 'CAPTURE_TYPE'},
                                    {headerText: 'Capture User',
                                    field: 'CAPTURE_USER'},
                                    {headerText: 'Logminer ID',
                                    field: 'LOGMINER_ID'},
                                    {headerText: 'Last DDL Time',
                                    field: 'LAST_DDL_TIME'}
];

self.IEMemcolumnArray = [{headerText: 'Session Name',
                            field: 'SESSION_NAME'},
                            {headerText: 'Available Chunks',
                            field: 'AVAILABLE_TXN'},
                            {headerText: 'Delivered Chunks',
                            field: 'DELIVERED_TXN'},
                            {headerText: 'Ready to Send Chunks',
                            field: 'DIFFERENCE'},
                            {headerText: 'Builder Work Size',
                            field: 'BUILDER_WORK_SIZE'},
                            {headerText: 'Prepared Work Size',
                            field: 'PREPARED_WORK_SIZE'},
                            {headerText: 'Used Memory',
                            field: 'USED_MEMORY_SIZE'},
                            {headerText: 'Max Memory',
                            field: 'MAX_MEMORY_SIZE'},
                            {headerText: 'Used Memory Percent',
                            field: 'USED_MEM_PCT'},

];


self.IEParamscolumnArray = [{headerText: 'Extract Name',
                            field: 'EXTRACT_NAME'},
                            {headerText: 'Capture Name',
                            field: 'CAPTURE_NAME'},
                            {headerText: 'Checkpoint Frequency',
                            field: 'CHECKPOINT_FREQUENCY'},
                            {headerText: 'EXCLUDETAG',
                            field: 'EXCLUDETAG'},
                            {headerText: 'EXCLUDEUSER',
                            field: 'EXCLUDEUSER'},
                            {headerText: 'GETAPPLOPS',
                            field: 'GETAPPLOPS'},
                            {headerText: 'GETREPLICATES',
                            field: 'GETREPLICATES'},
                            {headerText: 'MAX_SGA_SIZE',
                            field: 'MAX_SGA_SIZE'},
                            {headerText: 'PARALLELISM',
                            field: 'PARALLELISM'}
];


self.IEStreamscolumnArray = [{headerText: 'Instance ID',
                                field: 'INST_ID'},
                                {headerText: 'Max Streams Pool in MB',
                                field: 'MAX_MB'},
                                {headerText: 'Used Streams Pool in MB',
                                field: 'USED_MB'},
                                {headerText: '% Streams Pool Usage',
                                field: 'PCT_STREAMS_POOL'}
];

self.IEStreamsStatscolumnArray = [{headerText: 'Capture Name',
                                    field: 'CAPTURE_NAME'},
                                    {headerText: 'Allocated(MB)',
                                    field: 'ALLOCED'},
                                    {headerText: 'Used (MB)',
                                    field: 'USED'},
                                    {headerText: 'Captured LCRs',
                                    field: 'MSGS_CAPTURED'},
                                    {headerText: 'Enqueued LCRs',
                                    field: 'MSGS_ENQUEUED'},
                                    {headerText: 'Percent of Memory Used %',
                                    field: 'PCT'}

];


self.IELogmnrMemcolumnArray = [{headerText: 'Logminer Session',
                                field: 'SESSION_NAME'},
                                {headerText: 'Total Memory|Allocated(MB)',
                                field: 'MAX_MB'},
                                {headerText: 'Total Memory|Used (MB)',
                                field: 'USED_MB'},
                                {headerText: 'Percent of Allocated|Memory Used',
                                field: 'PCT_LOGMINER_MEM_USED'},
                                {headerText: 'Current Streams Pool Size(MB)',
                                field: 'STREAMS_POOL_SIZE'},
                                {headerText: 'Percent of Streams Pool',
                                field: 'PCT_STREAMS_POOL'}


];

self.IELongRuncolumnArray = [{headerText: 'Instance ID',
                            field: 'INST_ID'},
                            {headerText: 'Sid,Serial#',
                            field: 'SID'},
                            {headerText: 'Transaction ID',
                            field: 'XID'},
                            {headerText: 'Run Time',
                            field: 'RUNLENGTH'},
                            {headerText: 'Start SCN',
                            field: 'START_SCN'},
                            {headerText: 'Terminal',
                            field: 'TERMINAL'},
                            {headerText: 'Program',
                            field: 'PROGRAM'}
                            ];     


self.IEReadercolumnArray = [{headerText: 'Reader Name',
                            field: 'LOGMINER_READER_NAME'},
                            {headerText: 'SID',
                            field: 'SID'},
                            {headerText: 'Serial#',
                            field: 'SERIAL'},
                            {headerText: 'SPID',
                            field: 'SPID'},
                            {headerText: 'Database Wait Event',
                            field: 'EVENT'},
                            {headerText: 'Thread',
                            field: 'THREAD'},
                            {headerText: 'Archivelog',
                            field: 'ARCHIVELOG'},
                            {headerText: 'Latch Wait',
                            field: 'LATCHWAIT'},
                            {headerText: 'Latch Spin',
                            field: 'LATCHSPIN'}
                            ];                            
    
self.IEMergercolumnArray = [{headerText: 'Merger Name',
                            field: 'LOGMINER_MERGER_NAME'},
                            {headerText: 'SID',
                            field: 'SID'},
                            {headerText: 'Serial#',
                            field: 'SERIAL'},
                            {headerText: 'SPID',
                            field: 'SPID'},
                            {headerText: 'Database Wait Event',
                            field: 'EVENT'},
                            {headerText: 'Latch Wait',
                            field: 'LATCHWAIT'},
                            {headerText: 'Latch Spin',
                            field: 'LATCHSPIN'}
                            ];     

self.IEBuildercolumnArray = [{headerText: 'Builder Name',
                            field: 'LOGMINER_BUILDER_NAME'},
                            {headerText: 'SID',
                            field: 'SID'},
                            {headerText: 'Serial#',
                            field: 'SERIAL'},
                            {headerText: 'SPID',
                            field: 'SPID'},
                            {headerText: 'Database Wait Event',
                            field: 'EVENT'},
                            {headerText: 'Latch Wait',
                            field: 'LATCHWAIT'},
                            {headerText: 'Latch Spin',
                            field: 'LATCHSPIN'}
                            ];     
self.IEPreparercolumnArray = [{headerText: 'Preparer Name',
                            field: 'LOGMINER_PREPARER_NAME'},
                            {headerText: 'SID',
                            field: 'SID'},
                            {headerText: 'Serial#',
                            field: 'SERIAL'},
                            {headerText: 'SPID',
                            field: 'SPID'},
                            {headerText: 'Database Wait Event',
                            field: 'EVENT'},
                            {headerText: 'Latch Wait',
                            field: 'LATCHWAIT'},
                            {headerText: 'Latch Spin',
                            field: 'LATCHSPIN'}
                            ];    
self.IEDBDetcolumnArray = [{headerText: 'Database Name',
                            field: 'NAME'},
                            {headerText: 'DBID',
                            field: 'DBID'},
                            {headerText: 'Instance ID',
                            field: 'INSTANCE'},
                            {headerText: 'Database|Edition',
                            field: 'DB_EDITION'},
                            {headerText: 'Host',
                            field: 'HOST'},
                            {headerText: 'Database|Role',
                            field: 'DATABASE_ROLE'},
                            {headerText: 'Version',
                            field: 'VERSION'},
                            {headerText: 'Current SCN',
                            field: 'CURRENT_SCN'},
                            {headerText: 'Minimum Required Capture SCN',
                            field: 'MIN_REQUIRED_CAPTURE_CHANGE'},
                            ];    


                            self.LogmnrStatscolumnArray = [{headerText: 'Capture Name',
                            field: 'capture_name'},
                            {headerText: 'Statistics Name',
                            field: 'name'},
                            {headerText: 'Statictics Value',
                            field: 'value'} ]

                            self.IEReaderASHcolumnArray = [{
                                headerText: 'Instance ID', field: 'INST_ID'}, { headerText: 'Logminer Reader Name', field: 'LOGMINER_READER_NAME' }, 
                                { headerText: 'Total Count', field: 'TOTAL_COUNT' },{ headerText: 'Event Count', field: 'EVENT_COUNT' }, 
                                { headerText: 'Percentage %', field: 'PERCENTAGE' }, { headerText: 'Event', field: 'EVENT' }
                            ];


                            self.valueChangedHandler = (event) => {
                                self.ButtonVal(false);
                            };

                            self.CancelBehaviorOpt = ko.observable('icon');


                            self.popUpResizeSM = (value) => {
                                document.getElementById(value).style.width="500px";
                                document.getElementById(value).style.height="45vh";
                            }

                            self.ReqArchLog = ko.observableArray([]);
                            self.REQUIRED_CHECKPOINT_SCN = ko.observable();
                            self.EXTRACT_NAME = ko.observable();
                            self.DBLoginTitle = ko.observable();
                            self.menuItem = ko.observable();
                            self.ExtRpt = ko.observableArray([]);
                            self.delTitle = ko.observable();
                    
                            this.menuListener = (event, context) => {
                                self.REQUIRED_CHECKPOINT_SCN(context.row.REQUIRED_CHECKPOINT_SCN);
                                self.EXTRACT_NAME(context.row.EXTRACT_NAME);
                                self.menuItem('');
                                if (event.target.value === "archlog") {
                                    self.ReqArchLog([]);
                                    $.ajax({
                                        url: self.DepName() + "/reqarchlog",
                                        data: JSON.stringify({
                                            dbname: self.currentDB(),
                                            req_scn: self.REQUIRED_CHECKPOINT_SCN()
                                        }),
                                        type: 'POST',
                                        dataType: 'json',
                                        TimeoutManage: 60000,
                                        context: self,
                                        error: function (xhr, textStatus, errorThrown) {
                                            if(textStatus == 'TimeoutManage'){
                                                document.querySelector('#TimeoutManageManage').open();
                                            }
                                        },
                                        success: function (data) {
                                            document.querySelector('#ViewReqArchLog').open();
                                            self.ReqArchLog(data[0]);
                                            return self;
                                        }
                                    })
                                   }
                                  else if (event.target.value === "extunreg") {
                                    self.DBLoginTitle('DBLogin for Extract '+ self.EXTRACT_NAME());
                                    getDomains();
                                    self.menuItem('extunreg')
                                    document.querySelector('#ExtLoginDialog').open();
                                }
                            }
                                self.ReqArchLogDP = new ArrayDataProvider(self.ReqArchLog, {keyAttributes: 'NAME'});

                                self.ReqArchLogcolumnArray = [{
                                    headerText: 'Archivelog', field: 'NAME'}, { headerText: 'Thread#', field: 'THREAD#' }, 
                                    { headerText: 'FIRST_TIME', field: 'FIRST_TIME' },{ headerText: 'NEXT_TIME', field: 'NEXT_TIME' }, 
                                    { headerText: 'FIRST_CHANGE#', field: 'FIRST_CHANGE#' }, { headerText: 'NEXT_CHANGE#', field: 'NEXT_CHANGE#' },
                                    { headerText: 'DELETED', field: 'DELETED' }
                                ];

                                self.unregisterExtract = function (event) {
                                    document.querySelector('#ExtLoginDialog').close();
                                    document.querySelector('#Progress').open();
                                    self.ExtRpt([]);
                                    self.delTitle('');
                                    $.ajax({
                                        url: self.DepName() + "/ggextops",
                                        data: JSON.stringify({
                                            extname: self.EXTRACT_NAME(),
                                            domain: self.selectedDomCategory(),
                                            alias: self.selectedAliascategory(),
                                            extops : self.menuItem()
                                        }),
                                        type: 'POST',
                                        dataType: 'json',
                                        timeout: sessionStorage.getItem("timeInetrval"),
                                            context: self,
                                            error: function (xhr, textStatus, errorThrown) {
                                                if(textStatus == 'TimeoutManage' || textStatus == 'error'){
                                                    document.querySelector('#Progress').close();
                                                    document.querySelector('#TimeoutManage').open();
                                                }
                                            },
                                        success: function (data) {
                                            document.querySelector('#Progress').close();
                                            self.delTitle('Unregister  Extract ' +self.EXTRACT_NAME());
                                            self.popUpResizeSM("ViewExtractRptDialog");
                                            document.querySelector('#ViewExtractRptDialog').open();
                                            self.ExtRpt(data[0]);
                                            return self;
                                        }
                                    })
                                };


            self.ViewExtractRptOKClose = function (event) {
                document.querySelector('#ViewExtractRptDialog').close();
            };

                                self.CancelBehaviorOpt = ko.observable('icon');
                                self.isFormReadonly = ko.observable(false);

                                self.username1 = ko.observableArray([]);
                                self.aliasname1 = ko.observableArray([]);
                                self.domname1 = ko.observableArray([]);
                                self.othdom = ko.observableArray([]);
                                self.aliascategories = ko.observableArray([]);
                                self.unamecategories = ko.observable();
                                self.selectedDomCategory = ko.observable();
                                self.selectedAliascategory = ko.observable();
                                self.selectedUsercategory = ko.observable();
                    
                                function getDomains() {
                                    self.username1([]);
                                    self.othdom([]);
                                    self.aliasname1([]);
                                    self.domname1([]);
                                    self.selectedAliascategory('');
                                    self.selectedUsercategory('');
                                    $.ajax({
                                        url: self.DepName() + "/ggcredstore",
                                        type: 'GET',
                                        dataType: 'json',
                                        TimeoutManage: 20000,
                                        error: function (xhr, textStatus, errorThrown) {
                                            if(textStatus == 'TimeoutManage' || textStatus == 'error'){
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
                    

                            self.connected = function () { 
                                if (sessionStorage.getItem("userName")==null) {
                                  oj.Router.rootInstance.go('signin');
                              }
                              else
                              {                                        
                                   app.onAppSuccess();            
                                     getDB();
                              }
                            };
    

    }



}
    return  ietshootViewModel;
}
)