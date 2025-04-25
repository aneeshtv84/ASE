
define(['knockout', 'jquery', 'appController', 'ojs/ojarraydataprovider', "ojs/ojflattenedtreedataproviderview", "ojs/ojarraytreedataprovider", 'ojs/ojknockouttemplateutils',"ojs/ojcollapsible", 'ojs/ojbutton', 'ojs/ojtable', 'ojs/ojdialog', 'ojs/ojinputtext', 'ojs/ojselectsingle', 'ojs/ojformlayout', "ojs/ojrowexpander", "ojs/ojtagcloud", "ojs/ojchart"],
    function (ko, $, app, ArrayDataProvider, FlattenedTreeDataProviderView, ArrayTreeDataProvider, KnockoutTemplateUtils) {

        class irtshootViewModel {
            constructor(context){
            var self = this;
            self.DepName = context.DepName;
            self.CancelBehaviorOpt = ko.observable('icon');
            this.KnockoutTemplateUtils = KnockoutTemplateUtils;
            self.DBMainVer = ko.observable();
            self.DBMinorVer = ko.observable();
            self.IRInboundProgress = ko.observableArray([]);
            self.IRStats = ko.observableArray([]);
            self.IRParams = ko.observableArray([]);
            self.IROpen = ko.observableArray([]);
            self.IROpen10000 = ko.observableArray([]);
            self.IRReader = ko.observableArray([]);
            self.IRBuilder = ko.observableArray([]);
            self.IRPreparer = ko.observableArray([]);
            self.IRDBDet = ko.observableArray([]);
            self.DBDet = ko.observableArray([]);
            self.currentDB = ko.observable();
            self.ButtonVal= ko.observable(true);
            self.ApplyReaderLCRDep = ko.observableArray([]);

            self.ApplyReciever = ko.observableArray([]);
            self.ApplyRecieverASH = ko.observableArray([]);
            self.ApplyReader = ko.observableArray([]);
            self.ApplyReaderInfo = ko.observableArray([]);
            self.ApplyReaderASH = ko.observableArray([]);
            self.ApplyCoordinatorInfo = ko.observableArray([]);
            self.ApplyCoordinator = ko.observableArray([]);
            self.ApplyServerInfo = ko.observableArray([]);
            self.ApplyServerASH = ko.observableArray([]);
            self.ApplyServerFTS = ko.observableArray([]);
            self.ApplyServerTxn = ko.observableArray([]);
            self.ApplyFlow = ko.observableArray([]);
            self.ApplyAggStats = ko.observableArray([]);
            self.ApplyWaits = ko.observableArray([]);


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
                $.ajax({
                    url: self.DepName() + "/dbdet",
                    type: 'GET',
                    dataType: 'json',
                    context: self,
                    error: function (e) {
                        //console.log(e);
                    },
                    success: function (data) {
                        self.DBDet([]);
                        for (var i = 0; i < data[0].length; i++) {
                            self.DBDet.push({'value' : data[0][i].dbname, 'label' : data[0][i].dbname});
                        }
                        self.ButtonVal(true);
                    }
                })
            }

            self.DBDetDP = new ArrayDataProvider(self.DBDet, { keyAttributes: 'value' });
            self.OPError = ko.observableArray([]);

            self.IRTShoot = function (data, event) {
                document.querySelector('#getExtractTshoot').open();
                self.IRStats([]);
                self.IRParams([]);
                self.IROpen([]);
                self.IROpen10000([]);
                self.IRDBDet([]);
                self.IRInboundProgress([]);
                self.ApplyReciever([]);
                self.ApplyRecieverASH([]);
                self.ApplyReader([]);
                self.ApplyReaderASH([]);
                self.ApplyReaderInfo([]);
                self.ApplyCoordinatorInfo([]);
                self.ApplyCoordinator([]);
                self.ApplyServerInfo([]);
                self.ApplyServerASH([]);
                self.ApplyServerFTS([]);
                self.ApplyServerTxn([]);
                self.ApplyFlow([]);
                self.ApplyAggStats([]);
                self.ApplyWaits([]);
                self.ApplyReaderLCRDep([]);
                $.ajax({
                    url: self.DepName() + "/irtshoot",
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
                            self.OPError(data[0]);
                        }
                        else{
                          for (var i = 0; i < data[0].length; i++) {
                            self.IRStats.push({
                                'CURRENT_TIME': data[0][i].CURRENT_TIME,
                                'SERVER_NAME': data[0][i].SERVER_NAME,
                                'INST_ID': data[0][i].INST_ID,
                                'REPLICAT_NAME': data[0][i].REPLICAT_NAME,
                                'SOURCETSRANGE': data[0][i].SOURCETSRANGE,
                                'STATUS': data[0][i].STATUS,
                                'STATE': data[0][i].STATE,
                                'RCVSTATE': data[0][i].RECEIVERSTATE,
                                'LWM': data[0][i].LWM,
                                'UNASSIGNED_COMPLETE_TXNS': data[0][i].UNASSIGNED_COMPLETE_TXNS,
                                'APPLY_TAG': data[0][i].APPLY_TAG,
                                'VERSION': data[0][i].VERSION,
                                'ACTIVE_SERVER_COUNT': data[0][i].ACTIVE_SERVER_COUNT,
                                'REGISTERED': data[0][i].REGISTERED,
                                'APPLY_USER': data[0][i].APPLY_USER,
                                'APPLYTSRANGE': data[0][i].APPLYTSRANGE,
                                'STARTUP_TIME': data[0][i].STARTUP_TIME,
                                'LAST_DDL_TIME': data[0][i].LAST_DDL_TIME,
                                'APPLIED_TIME': data[0][i].APPLY_TIME
                            });
                        }
                        self.IRStats.valueHasMutated();

                        for (var i = 0; i < data[1].length; i++) {
                            self.IRParams.push({
                                'APPLY_NAME': data[1][i].APPLY_NAME,
                                'BATCHSQL': data[1][i].BATCHSQL,
                                'BATCHSQL_MODE': data[1][i].BATCHSQL_MODE,
                                'BATCHTRANSOPS': data[1][i].BATCHTRANSOPS,
                                'COMMIT_SERIALIZATION': data[1][i].COMMIT_SERIALIZATION,
                                'EAGER_SIZE': data[1][i].EAGER_SIZE,
                                'MAX_PARALLELISM': data[1][i].MAX_PARALLELISM,
                                'MAX_SGA_SIZE': data[1][i].MAX_SGA_SIZE,
                                'OPTIMIZE_PROGRESS_TABLE': data[1][i].OPTIMIZE_PROGRESS_TABLE,
                                'PARALLELISM': data[1][i].PARALLELISM,
                                'REPLICAT_NAME': data[1][i].REPLICAT_NAME
                            });
                        }
                        self.IRParams.valueHasMutated();
                        for (var i = 0; i < data[2].length; i++) {
                            self.IROpen.push({
                                'component_name': data[2][i].COMPONENT_NAME,
                                'Open_Transactions': data[2][i].OPEN_TRANSACTIONS,
                                'Total_LCRs': data[2][i].TOTAL_LCRS
                            });
                        }
                        self.IROpen.valueHasMutated();
                        for (var i = 0; i < data[3].length; i++) {
                            self.IROpen10000.push({
                                'component_name': data[3][i].COMPONENT_NAME,
                                'Open_Transactions': data[3][i].OPEN_TRANSACTIONS,
                                'Total_LCRs': data[3][i].TOTAL_LCRS
                            });
                        }
                        self.IROpen10000.valueHasMutated();
                        for (var i = 0; i < data[4].length; i++) {
                            self.IRDBDet.push({
                                'DATABASE_ROLE': data[4][i].DATABASE_ROLE,
                                'DBID': data[4][i].DBID,
                                'DB_EDITION': data[4][i].DB_EDITION,
                                'HOST': data[4][i].HOST,
                                'INSTANCE': data[4][i].INSTANCE,
                                'NAME': data[4][i].NAME,
                                'PLATFORM_NAME': data[4][i].PLATFORM_NAME,
                                'VERSION': data[4][i].VERSION
                            });
                        }
                        self.IRDBDet.valueHasMutated();

                        for (var i = 0; i < data[5].length; i++) {
                            self.IRInboundProgress.push({
                                'server_name': data[5][i].SERVER_NAME,
                                'processed_low_position': data[5][i].PROCESSED_LOW_POSITION,
                                'applied_low_position': data[5][i].APPLIED_LOW_POSITION,
                                'applied_high_position': data[5][i].APPLIED_HIGH_POSITION,
                                'oldest_position': data[5][i].OLDEST_POSITION,
                                'applied_low_scn': data[5][i].APPLIED_LOW_SCN,
                                'applied_time': data[5][i].APPLIED_TIME,
                                'applied_message_create_time': data[5][i].APPLIED_MESSAGE_CREATE_TIME,
                                'logbsn': data[5][i].LOGBSN
                            });
                        }
                        self.IRInboundProgress.valueHasMutated();


                        for (var i = 0; i < data[6].length; i++) {
                            self.ApplyReciever.push({
                                'inst_id': data[6][i].INST_ID,
                                'apply_name': data[6][i].APPLY_NAME,
                                'sid': data[6][i].SID,
                                'serial': data[6][i].SERIAL,
                                'startup_time': data[6][i].STARTUP_TIME,
                                'total_messages_received': data[6][i].TOTAL_MESSAGES_RECEIVED,
                                'total_available_messages': data[6][i].TOTAL_AVAILABLE_MESSAGES,
                                'state': data[6][i].STATE,
                                'last_received_msg_position': data[6][i].LAST_RECEIVED_MSG_POSITION,
                                'acknowledgement_position': data[6][i].ACKNOWLEDGEMENT_POSITION
                            });
                        }

                        self.ApplyReciever.valueHasMutated();

                        for (var i = 0; i < data[7].length; i++) {
                        self.ApplyRecieverASH.push({ 'APPLY_NAME': data[7][i].APPLY_NAME, 'INST_ID': data[7][i].INST_ID, 'TOTAL_COUNT': data[7][i].TOTAL_COUNT, 'EVENT': data[7][i].EVENT, 'PERCENTAGE': parseFloat(data[7][i].PERCENTAGE).toFixed(2), 'EVENT_COUNT': data[7][i].EVENT_COUNT  })
                                    }
                                
                        self.ApplyRecieverASH.valueHasMutated();

                        for (var i = 0; i < data[8].length; i++) {
                            self.ApplyReader.push({
                                'apply_name': data[8][i].APPLY_NAME,
                                'sid': data[8][i].SID,
                                'serial': data[8][i].SERIAL,
                                'process_name': data[8][i].PROCESS_NAME,
                                'elapsed_dequeue_time': data[8][i].ELAPSED_DEQUEUE_TIME,
                                'elapsed_schedule_time': data[8][i].ELAPSED_SCHEDULE_TIME,
                                'state': data[8][i].STATE,
                                'oldest_transaction_id': data[8][i].OLDEST_TRANSACTION_ID
                            });
                        }
                        self.ApplyReader.valueHasMutated();


                        for (var i = 0; i < data[9].length; i++) {
                            self.ApplyReaderASH.push({
                                'inst_id': data[9][i].INST_ID,
                                'apply_name': data[9][i].APPLY_NAME,
                                'event_count': data[9][i].EVENT_COUNT,
                                'total_count': data[9][i].TOTAL_COUNT,
                                'Percentage': parseFloat(data[9][i].PERCENTAGE).toFixed(2) + ' %',
                                'event': data[9][i].EVENT
                            });
                        }
                        self.ApplyReaderASH.valueHasMutated();


                        for (var i = 0; i < data[10].length; i++) {
                            self.ApplyReaderInfo.push({
                                'apply_name': data[10][i].APPLY_NAME,
                                'latency': data[10][i].LATENCY,
                                'dequeued_message_create_time': data[10][i].DEQUEUED_MESSAGE_CREATE_TIME,
                                'last_dequeue': data[10][i].LAST_DEQUEUE,
                                'dequeued_position': data[10][i].DEQUEUED_POSITION
                            });
                        }
                        self.ApplyReaderInfo.valueHasMutated();


                        for (var i = 0; i < data[20].length; i++) {
                            self.ApplyReaderLCRDep.push({
                                'apply_name': data[20][i].APPLY_NAME,
                                'total_messages_dequeued': data[20][i].TOTAL_MESSAGES_DEQUEUED,
                                'total_lcrs_with_dep': data[20][i].TOTAL_LCRS_WITH_DEP,
                                'total_lcrs_with_wmdep': data[20][i].TOTAL_LCRS_WITH_WMDEP,
                                'total_assigned': data[20][i].TOTAL_ASSIGNED,
                                'total_wait_deps': data[20][i].TOTAL_WAIT_DEPS,
                                'total_wait_commits': data[20][i].TOTAL_WAIT_COMMITS,
                                'waitdep_perc_msgs': Math.round(data[20][i].WaitDep_perc_msgs),
                                'wm_waitdep_perc_msgs': Math.round(data[20][i].WM_WaitDep_perc_msgs)

                            });
                        }

                        for (var i = 0; i < data[11].length; i++) {
                            self.ApplyCoordinatorInfo.push({
                                'apply_name': data[11][i].APPLY_NAME,
                                'total_applied': data[11][i].TOTAL_APPLIED,
                                'total_wait_commits': data[11][i].TOTAL_WAIT_COMMITS,
                                'total_wait_deps': data[11][i].TOTAL_WAIT_DEPS,
                                'waitdep': data[11][i].WAITDEP,
                                'commitdep': data[11][i].COMMITDEP
                            });
                        }
                        self.ApplyCoordinatorInfo.valueHasMutated();


                        for (var i = 0; i < data[12].length; i++) {
                            self.ApplyCoordinator.push({
                                'apply_name': data[12][i].APPLY_NAME,
                                'sid': data[12][i].SID,
                                'serial': data[12][i].SERIAL,
                                'process': data[12][i].PROCESS,
                                'startup_time': data[12][i].STARTUP_TIME,
                                'elapsed_schedule_time': data[12][i].ELAPSED_SCHEDULE_TIME,
                                'state': data[12][i].STATE,
                                'received': data[12][i].RECEIVED,
                                'assigned': data[12][i].ASSIGNED,
                                'unassigned': data[12][i].UNASSIGNED,
                                'applied': data[12][i].APPLIED,
                                'errors': data[12][i].ERRORS,
                                'total_ignored': data[12][i].TOTAL_IGNORED,
                                'total_rollbacks': data[12][i].TOTAL_ROLLBACKS
                            });
                        }
                        self.ApplyCoordinator.valueHasMutated();

                        for (var i = 0; i < data[13].length; i++) {
                            self.ApplyServerInfo.push({
                                'apply_name': data[13][i].APPLY_NAME,
                                'server_id': data[13][i].SERVER_ID,
                                'state': data[13][i].STATE,
                                'total_messages_applied': data[13][i].TOTAL_MESSAGES_APPLIED,
                                'sql_id': data[13][i].SQL_ID,
                                'sqltext': data[13][i].SQLTEXT,
                                'executions': data[13][i].EXECUTIONS,
                                'rows_processed': data[13][i].ROWS_PROCESSED,
                                'rows_per_exec': data[13][i].ROWS_PER_EXEC,
                                'optimizer_mode': data[13][i].OPTIMIZER_MODE,
                                'optimizer_cost': data[13][i].OPTIMIZER_COST
                            });
                        }
                        self.ApplyServerInfo.valueHasMutated();

                        for (var i = 0; i < data[14].length; i++) {
                            self.ApplyServerTxn.push({
                                'apply_name': data[14][i].APPLY_NAME,
                                'process_name': data[14][i].PROCESS_NAME,
                                'server_id': data[14][i].SERVER_ID,
                                'state': data[14][i].STATE,
                                'sid': data[14][i].SID,
                                'serial': data[14][i].SERIAL,
                                'assigned': data[14][i].ASSIGNED,
                                'msg_applied': data[14][i].MSG_APPLIED,
                                'current_txn': data[14][i].CURRENT_TXN,
                                'commit_position': data[14][i].COMMIT_POSITION,
                                'dependent_txn': data[14][i].DEPENDENT_TXN,
                                'dep_commit_position': data[14][i].DEP_COMMIT_POSITION,
                                'message_sequence': data[14][i].MESSAGE_SEQUENCE,
                                'apply_time': data[14][i].APPLY_TIME
                            });
                        }
                        self.ApplyServerTxn.valueHasMutated();

                        for (var i = 0; i < data[15].length; i++) {
                            self.ApplyServerFTS.push({
                                'table_name': data[15][i].TABLE_NAME
                            });
                        }
                        self.ApplyServerFTS.valueHasMutated();


                        for (var i = 0; i < data[16].length; i++) {
                            self.ApplyServerASH.push({ 'APPLY_NAME': data[16][i].APPLY_NAME, 'INST_ID': data[16][i].INST_ID, 
                            'TOTAL_COUNT': data[16][i].TOTAL_COUNT,  'EVENT': data[16][i].EVENT, 
                            'PERCENTAGE': Math.round(data[16][i].PERCENTAGE) + ' %', 'EVENT_COUNT': data[16][i].EVENT_COUNT});
                            }
                    

                        self.ApplyServerASH.valueHasMutated();

                        for (var i = 0; i < data[17].length; i++) {
                            self.ApplyFlow.push({ 'apply_name': data[17][i].APPLY_NAME, 'receiver_state': data[17][i].RECEIVER_STATE, 'reader_state': data[17][i].READER_STATE, 'sga_used': data[17][i].SGA_USED, 'sga_allocated': data[17][i].SGA_ALLOCATED, 'total_available_messages': data[17][i].TOTAL_AVAILABLE_MESSAGES, 'total_messages_received': data[17][i].TOTAL_MESSAGES_RECEIVED, 'total_messages_dequeued': data[17][i].TOTAL_MESSAGES_DEQUEUED, 'unassigned_complete_txns': data[17][i].UNASSIGNED_COMPLETE_TXNS, 'active_executing_count': data[17][i].ACTIVE_EXECUTING_COUNT });
                        }

                        self.ApplyFlow.valueHasMutated();

                        for (var i = 0; i < data[18].length; i++) {
                            self.ApplyAggStats.push({ 'apply_name': data[18][i].APPLY_NAME, 'server_id': data[18][i].SERVER_ID, 'process_name': data[18][i].PROCESS_NAME, 'sid': data[18][i].SID, 'serial': data[18][i].SERIAL, 'state': data[18][i].STATE, 'current_txn': data[18][i].CURRENT_TXN, 'assigned': data[18][i].ASSIGNED, 'msg_applied': data[18][i].MSG_APPLIED, 'message_sequence': data[18][i].MESSAGE_SEQUENCE, 'lcr_retry_iteration': data[18][i].LCR_RETRY_ITERATION, 'txn_retry_iteration': data[18][i].TXN_RETRY_ITERATION, 'total_lcrs_retried': data[18][i].TOTAL_LCRS_RETRIED, 'total_txns_retried': data[18][i].TOTAL_TXNS_RETRIED, 'total_txns_recorded': data[18][i].TOTAL_TXNS_RECORDED, 'elapsed_apply_time': data[18][i].ELAPSED_APPLY_TIME, 'apply_time': data[18][i].APPLY_TIME, 'logon_time': data[18][i].LOGON_TIME });
                        }

                        self.ApplyAggStats.valueHasMutated();


                        for (var i = 0; i < data[19].length; i++) {
                            self.ApplyWaits.push({ 'apply_name': data[19][i].APPLY_NAME, 'server_id': data[19][i].SERVER_ID, 'event': data[19][i].EVENT, 'secs': data[19][i].SECS });
                        }

                        self.ApplyWaits.valueHasMutated();

                        document.querySelector('#getExtractTshoot').close();
                    }
                        //console.log(self);
                        return self;
                    }

                })

            }

            
            self.IRStatsDP = new ArrayDataProvider(self.IRStats, { keyAttributes: 'SERVER_NAME' });
            self.IRParamsDP = new ArrayDataProvider(self.IRParams, { keyAttributes: 'APPLY_NAME' });
            self.IROpenDP = new ArrayDataProvider(self.IROpen, { keyAttributes: 'component_name' });
            self.IROpen10000DP = new ArrayDataProvider(self.IROpen10000, { keyAttributes: 'component_name' });
            self.IRDBDetDP = new ArrayDataProvider(self.IRDBDet, { keyAttributes: 'DBID' });
            self.IRIBProgressDP = new ArrayDataProvider(self.IRInboundProgress, { keyAttributes: 'SERVER_NAME' });
            self.ApplyRecieverDP = new ArrayDataProvider(self.ApplyReciever, { keyAttributes: 'APPLY_NAME' });

            self.ApplyRecieverASHTreeDP = new ArrayTreeDataProvider(self.ApplyRecieverASH, { keyAttributes: "APPLY_NAME" });
            self.ApplyRecieverASHDP = (new FlattenedTreeDataProviderView(self.ApplyRecieverASHTreeDP));

            self.ApplyReaderDP = new ArrayDataProvider(self.ApplyReader, { keyAttributes: 'APPLY_NAME' });
            self.ApplyReaderInfoDP = new ArrayDataProvider(self.ApplyReaderInfo, { keyAttributes: 'APPLY_NAME' });
            self.ApplyReaderASHDP = new ArrayDataProvider(self.ApplyReaderASH, { keyAttributes: 'APPLY_NAME' });
            self.ApplyCoordinatorInfoDP = new ArrayDataProvider(self.ApplyCoordinatorInfo, { keyAttributes: 'APPLY_NAME' });
            self.ApplyCoordinatorDP = new ArrayDataProvider(self.ApplyCoordinator, { keyAttributes: 'APPLY_NAME' });

            self.ApplyServerInfoDP = new ArrayDataProvider(self.ApplyServerInfo, { keyAttributes: 'APPLY_NAME' });
            self.ApplyServerASHDP = new ArrayDataProvider(self.ApplyServerASH, { keyAttributes: 'APPLY_NAME' });
            self.ApplyServerTxnDP = new ArrayDataProvider(self.ApplyServerTxn, { keyAttributes: 'APPLY_NAME' });
            self.ApplyServerFTSDP = new ArrayDataProvider(self.ApplyServerFTS, { keyAttributes: 'APPLY_NAME' });
            self.ApplyFlowDP = new ArrayDataProvider(self.ApplyFlow, { keyAttributes: 'APPLY_NAME' });
            self.ApplyAggStatsDP = new ArrayDataProvider(self.ApplyAggStats, { keyAttributes: 'APPLY_NAME' });
            self.ApplyWaitsDP = new ArrayDataProvider(self.ApplyWaits, { keyAttributes: 'APPLY_NAME' });
            self.ApplyReaderLCRDepDP = new ArrayDataProvider(self.ApplyReaderLCRDep, { keyAttributes: 'APPLY_NAME' });


            self.IRStatcolumnArray = [{ headerText: 'Current Time', field: 'CURRENT_TIME' }, { headerText: 'Instance ID', field: 'INST_ID' },
            { headerText: 'Server Name', field: 'SERVER_NAME' }, { headerText: 'Replicat Name', field: 'REPLICAT_NAME' },
            { headerText: 'Status', field: 'STATUS' }, { headerText: 'Current Coordinator State', field: 'STATE' }, { headerText: 'Apply User', field: 'APPLY_USER' },
            { headerText: 'Current Receiver State', field: 'RCVSTATE' }, { headerText: 'Active Server Count', field: 'ACTIVE_SERVER_COUNT' },
            { headerText: 'Apply Tag', field: 'APPLY_TAG' },
            { headerText: 'Source TS Range|HWM-LWM|(seconds)', field: 'SOURCETSRANGE' }, { headerText: 'Registered', field: 'REGISTERED' },
            { headerText: 'Process Startup Time', field: 'STARTUP_TIME' }, { headerText: 'Low Watermark Message Create Time', field: 'LWM' },
            { headerText: 'Apply_Time Range|HWM-LWM|(seconds)', field: 'APPLYTSRANGE' }, { headerText: 'Unassigned Complete Txns', field: 'UNASSIGNED_COMPLETE_TXNS' },
            { headerText: 'Last DDL Time', field: 'LAST_DDL_TIME' }, { headerText: 'LWM Apply|Time', field: 'APPLIED_TIME' }
            ];

            self.IRParamscolumnArray = [{ headerText: 'Replicat Name', field: 'REPLICAT_NAME' }, { headerText: 'Apply Name', field: 'APPLY_NAME' },
            { headerText: 'PARALLELISM', field: 'PARALLELISM' }, { headerText: 'MAX_PARALLELISM', field: 'MAX_PARALLELISM' },
            { headerText: 'MAX_SGA_SIZE', field: 'MAX_SGA_SIZE' }, { headerText: 'EAGER_SIZE', field: 'EAGER_SIZE' },
            { headerText: 'COMMIT_SERIALIZATION', field: 'COMMIT_SERIALIZATION' }, { headerText: 'BATCHSQL', field: 'BATCHSQL' },
            { headerText: 'BATCHSQL_MODE', field: 'BATCHSQL_MODE' }, { headerText: 'BATCHTRANSOPS', field: 'BATCHTRANSOPS' }, { headerText: 'OPTIMIZE_PROGRESS_TABLE', field: 'OPTIMIZE_PROGRESS_TABLE' }
            ];

            self.IROpencolumnArray = [{
                headerText: 'Component Name',
                field: 'component_name'
            },
            {
                headerText: 'Open Transactions',
                field: 'Open_Transactions'
            },
            {
                headerText: 'Total LCRs',
                field: 'Total_LCRs'
            }
            ];

            self.IROpen10000columnArray = [{
                headerText: 'Component Name',
                field: 'component_name'
            },
            {
                headerText: 'Open Transactions',
                field: 'Open_Transactions'
            },
            {
                headerText: 'Total LCRs',
                field: 'Total_LCRs'
            }
            ];



            self.IRDBDetcolumnArray = [{ headerText: 'Database Name', field: 'NAME' }, { headerText: 'DBID', field: 'DBID' }, { headerText: 'Instance ID', field: 'INSTANCE' },
            { headerText: 'Database|Edition', field: 'DB_EDITION' }, { headerText: 'Host', field: 'HOST' }, { headerText: 'Database|Role', field: 'DATABASE_ROLE' },
            { headerText: 'Version', field: 'VERSION' }];

            self.IRStreamsStatscolumnArray = [{ headerText: 'Capture Name', field: 'CAPTURE_NAME' },
            { headerText: 'Total Memory|Allocated(MB)', field: 'ALLOCED' }, { headerText: 'Total Memory|Used (MB)', field: 'USED' },
            { headerText: 'Total LCRs|Captured', field: 'MSGS_CAPTURED' }, {
                headerText: 'Total LCRs|Enqueued',
                field: 'MSGS_ENQUEUED'
            }, { headerText: 'Percent of Allocated|Memory Used ', field: 'PCT' }

            ];


            self.IRLogmnrMemcolumnArray = [{ headerText: 'Logminer Session', field: 'SESSION_NAME' }, { headerText: 'Total Memory|Allocated(MB)', field: 'MAX_MB' },
            { headerText: 'Total Memory|Used (MB)', field: 'USED_MB' }, { headerText: 'Percent of Allocated|Memory Used', field: 'PCT_LOGMINER_MEM_USED' },
            { headerText: 'Percent of Streams Pool', field: 'PCT_STREAMS_POOL' }
            ];

            self.IRLongRuncolumnArray = [{ headerText: 'Instance ID', field: 'INST_ID' }, { headerText: 'Sid,Serial#', field: 'SID' },
            { headerText: 'Transaction ID', field: 'XID' },
            { headerText: 'Run Time', field: 'RUNLENGTH' }, { headerText: 'Start SCN', field: 'START_SCN' },
            { headerText: 'Terminal', field: 'TERMINAL' },
            { headerText: 'Program', field: 'PROGRAM' }];


            self.IRReadercolumnArray = [{ headerText: 'Reader Name', field: 'LOGMINER_READER_NAME' }, { headerText: 'SID', field: 'SID' },
            { headerText: 'Serial#', field: 'SERIAL' }, { headerText: 'SPID', field: 'SPID' }, { headerText: 'Database Wait Event', field: 'EVENT' },
            { headerText: 'Latch Wait', field: 'LATCHWAIT' }, { headerText: 'Latch Spin', field: 'LATCHSPIN' }];



            self.IEBuildercolumnArray = [{ headerText: 'Builder Name', field: 'LOGMINER_BUILDER_NAME' },
            { headerText: 'SID', field: 'SID' }, { headerText: 'Serial#', field: 'SERIAL' }, { headerText: 'SPID', field: 'SPID' },
            { headerText: 'Database Wait Event', field: 'EVENT' }, { headerText: 'Latch Wait', field: 'LATCHWAIT' },
            { headerText: 'Latch Spin', field: 'LATCHSPIN' }];

            self.IRPreparercolumnArray = [{ headerText: 'Preparer Name', field: 'LOGMINER_PREPARER_NAME' },
            { headerText: 'SID', field: 'SID' }, { headerText: 'Serial#', field: 'SERIAL' }, { headerText: 'SPID', field: 'SPID' },
            { headerText: 'Database Wait Event', field: 'EVENT' }, { headerText: 'Latch Wait', field: 'LATCHWAIT' },
            { headerText: 'Latch Spin', field: 'LATCHSPIN' }
            ];


            self.IRInboundcolumnArray = [{ headerText: 'Server Name', field: 'server_name' }, { headerText: 'Processed Low Position', field: 'processed_low_position' },
            { headerText: 'Applied Low Position', field: 'applied_low_position' }, { headerText: 'Applied  High Position', field: 'applied_high_position' },
            { headerText: 'Oldest Position', field: 'oldest_position' }, { headerText: 'Applied Low SCN', field: 'applied_low_scn' },
            { headerText: 'Applied Time', field: 'applied_time' }, { headerText: 'Applied Message Create Time', field: 'applied_message_create_time' },
            { headerText: 'Uncommited SCN', field: 'logbsn' }
            ];

            self.ApplyRecievercolumnArray = [{ headerText: 'Instance ID', field: 'inst_id' }, { headerText: 'Apply Name', field: 'apply_name' },
            { headerText: 'Session ID', field: 'sid' }, { headerText: 'Serial #', field: 'serial' },
            { headerText: 'Startup Time', field: 'startup_time' }, { headerText: 'Total Messages Recieved', field: 'total_messages_received' },
            { headerText: 'Total Available Messages', field: 'total_available_messages' },
            { headerText: 'State', field: 'state' }, { headerText: 'Last Recieved Message Position', field: 'last_received_msg_position' },
            { headerText: 'Acknowledgement Position', field: 'acknowledgement_position' }
            ];

            self.ApplyRecieverASHcolumnArray = [{
                headerText: 'Instance ID', field: 'INST_ID'
            }, { headerText: 'Apply Name', field: 'APPLY_NAME' }, { headerText: 'Total Count', field: 'TOTAL_COUNT' },
            { headerText: 'Database Wait Event', field: 'EVENT' },
            { headerText: '% of Waits', field: 'PERCENTAGE' },
            { headerText: 'Event Count', field: 'EVENT_COUNT' }
        ]


            self.ApplyReadercolumnArray = [{ headerText: 'Apply Name', field: 'apply_name' },{ headerText: 'State', field: 'state' },
            { headerText: 'Session ID', field: 'sid' }, { headerText: 'Serial #', field: 'serial' },
            { headerText: 'Process Name', field: 'process_name' }, { headerText: 'Elapsed Dequeque Time', field: 'elapsed_dequeue_time' },
            { headerText: 'Elapsed Schedule Time', field: 'elapsed_schedule_time' },
            { headerText: 'Oldest Transaction ID', field: 'oldest_transaction_id' }]


            self.ApplyReaderASHcolumnArray = [{
                headerText: 'Instance ID', field: 'inst_id'
            }, { headerText: 'Apply Name', field: 'apply_name' }, { headerText: 'Total Count', field: 'total_count' }, { headerText: 'Event Count', field: 'event_count' }, { headerText: 'Percentage', field: 'Percentage' }, { headerText: 'Event', field: 'event' }
            ];

            self.ApplyReaderInfocolumnArray = [
                { headerText: 'Apply Name', field: 'apply_name' }, { headerText: 'Latency in Seconds', field: 'latency' }, { headerText: 'Dequeued Message Create Time', field: 'dequeued_message_create_time' }, { headerText: 'Last Dequeue', field: 'last_dequeue' }, { headerText: 'Dequeued Position', field: 'dequeued_position' }
            ];

            self.ApplyReaderLCRDepcolumnArray = [{ headerText: 'Apply Name', field: 'apply_name' }, 
            { headerText: 'Total Messages Dequeued', field: 'total_messages_dequeued' }, 
            { headerText: 'Total LCRs with Dependency', field: 'total_lcrs_with_dep' },
             { headerText: 'Total LCRs with WaterMark Dependency', field: 'total_lcrs_with_wmdep' }, 
             { headerText: 'Total LCRs Assigned', field: 'total_assigned' },
             { headerText: 'Total Wait Dependencies', field: 'total_wait_deps' },
             { headerText: 'Total Wait Commits', field: 'total_wait_commits' },
             { headerText: 'Row Level Wait Dependency %', field: 'waitdep_perc_msgs' },
             { headerText: 'Water Mark Wait Dependency % ', field: 'wm_waitdep_perc_msgs' },
        ];

            self.ApplyCoordinatorInfocolumnArray = [
                { headerText: 'Apply Name', field: 'apply_name' }, { headerText: 'Total Applied', field: 'total_applied' }, { headerText: 'Total Wait Dependencies', field: 'total_wait_deps' }, { headerText: 'Total Wait Commits', field: 'total_wait_commits' }, { headerText: 'Wait Dependency %', field: 'waitdep' }, { headerText: 'Commit Dependency %', field: 'commitdep' }
            ];

            self.ApplyCoordinatorcolumnArray = [
                { headerText: 'Apply Name', field: 'apply_name' }, { headerText: 'Session ID', field: 'sid' }, { headerText: 'Serial #', field: 'serial' }, { headerText: 'Process', field: 'process' }, { headerText: 'Startup Time', field: 'startup_time' },
                { headerText: 'Elapsed Schedule Time', field: 'elapsed_schedule_time' }, { headerText: 'State', field: 'state' },
                { headerText: 'Total Received', field: 'received' }, { headerText: 'Total Assigned', field: 'assigned' },
                { headerText: 'Total Unassigned', field: 'unassigned' }, { headerText: 'Total Applied', field: 'applied' },
                { headerText: 'Total Errors', field: 'errors' }, { headerText: 'Total Ignored', field: 'total_ignored' }, { headerText: 'Total Rollbacks', field: 'total_rollbacks' }
            ];

            self.ApplyServerASHcolumnArray = [{
                headerText: 'Instance ID', field: 'INST_ID'}, { headerText: 'Apply Name - Server ID', field: 'APPLY_NAME' }, 
                { headerText: 'Total Count', field: 'TOTAL_COUNT' },{ headerText: 'Event Count', field: 'EVENT_COUNT' }, 
                { headerText: 'Percentage %', field: 'PERCENTAGE' }, { headerText: 'Event', field: 'EVENT' }
            ];

            self.ApplyServerInfocolumnArray = [
                { headerText: 'Apply Name', field: 'apply_name' }, { headerText: 'Server ID', field: 'server_id' },
                { headerText: 'State', field: 'state' }, { headerText: 'Total Messages Applied', field: 'total_messages_applied' },
                { headerText: 'SQL ID', field: 'sql_id' }, { headerText: 'SQL Text', field: 'sqltext' },
                { headerText: 'Executions', field: 'executions' }, { headerText: 'Rows Processed', field: 'rows_processed' },
                { headerText: 'Rows Per Exec', field: 'rows_per_exec' },
                { headerText: 'Optimizer Mode', field: 'optimizer_mode' }, { headerText: 'Optimizer Cost', field: 'optimizer_cost' }
            ];

            self.ApplyServerTxncolumnArray = [
                { headerText: 'Apply Name', field: 'apply_name' }, { headerText: 'process Name', field: 'process_name' },
                { headerText: 'Server ID', field: 'server_id' }, { headerText: 'State', field: 'state' },
                { headerText: 'Session id', field: 'sid' }, { headerText: 'Serial#', field: 'serial' },
                { headerText: 'Assigned', field: 'assigned' }, { headerText: 'Message Applied', field: 'msg_applied' },
                { headerText: 'Current Transaction', field: 'current_txn' },
                { headerText: 'Commit SCN', field: 'commit_position' }, { headerText: 'Dependent Transaction', field: 'dependent_txn' },
                { headerText: 'Dependent Commit SCN', field: 'dep_commit_position' }, { headerText: 'Message Sequence', field: 'message_sequence' },
                { headerText: 'Apply Time', field: 'apply_time' },
            ];

            self.ApplyServerFTScolumnArray = [
                { headerText: 'Table Name', field: 'table_name' }]


            self.ApplyFlowcolumnArray = [{
                headerText: 'Apply Name',
                field: 'apply_name'
            },
            {
                headerText: 'Receiver State',
                field: 'receiver_state'
            },
            {
                headerText: 'Reader State',
                field: 'reader_state'
            },
            {
                headerText: 'SGA Used(MB)',
                field: 'sga_used'
            },
            {
                headerText: 'SGA Allocated(MB)',
                field: 'sga_allocated'
            },
            {
                headerText: 'Total Available Messages',
                field: 'total_available_messages'
            },
            {
                headerText: 'Total Messages Received',
                field: 'total_messages_received'
            },
            {
                headerText: 'Total Messages Dequeued',
                field: 'total_messages_dequeued'
            },
            {
                headerText: 'Unassigned Completed Transactions',
                field: 'unassigned_complete_txns'
            },
            {
                headerText: 'Active Executing Count',
                field: 'active_executing_count'
            }
            ];



            self.ApplyAggStatscolumnArray = [{
                headerText: 'Apply Name',
                field: 'apply_name'
            },
            {
                headerText: 'Server ID',
                field: 'server_id'
            },
            {
                headerText: 'Process Name',
                field: 'process_name'
            },
            {
                headerText: 'Session ID',
                field: 'sid'
            },
            {
                headerText: 'Serial#',
                field: 'serial'
            },
            {
                headerText: 'State',
                field: 'state'
            },
            {
                headerText: 'Current Transaction',
                field: 'current_txn'
            },
            {
                headerText: 'Total Messages Assigned',
                field: 'assigned'
            },
            {
                headerText: 'Total Messages Applied',
                field: 'msg_applied'
            },
            {
                headerText: 'Message Sequence',
                field: 'message_sequence'
            },
            {
                headerText: 'LCR Retry Iteration',
                field: 'lcr_retry_iteration'
            },
            {
                headerText: 'Transaction Retry Iteration',
                field: 'txn_retry_iteration'
            },
            {
                headerText: 'Total LCRs Retried',
                field: 'total_lcrs_retried'
            },
            {
                headerText: 'Total Transactions Retried',
                field: 'total_txns_retried'
            },
            {
                headerText: 'Total Transactions Recorded',
                field: 'total_txns_recorded'
            },
            {
                headerText: 'Elapsed Apply Time',
                field: 'elapsed_apply_time'
            },
            {
                headerText: 'Apply Time',
                field: 'apply_time'
            },
            {
                headerText: 'Logon Time',
                field: 'logon_time'
            },
            ];


            self.ApplyWaitscolumnArray = [
                { headerText: 'Apply Name', field: 'apply_name' },
                { headerText: 'Server ID', field: 'server_id' },
                { headerText: 'Event', field: 'event' },
                { headerText: 'Seconds in Wait', field: 'secs' },
            ]


            self.valueChangedHandler = (event) => {
                self.ButtonVal(false);
            };

            self.CancelBehaviorOpt = ko.observable('icon');

            self.connected = function () {
                if (sessionStorage.getItem("userName") == null) {
                    oj.Router.rootInstance.go('signin');
                }
                else {
                    app.onAppSuccess();
                    getDB();
                    self.IRInboundProgress([]);
                    self.IRStats([]);
                    self.IRParams([]);
                    self.IROpen([]);
                    self.IROpen10000([]);
                    self.IRReader([]);
                    self.IRBuilder([]);
                    self.IRPreparer([]);
                    self.IRDBDet([]);
                    self.DBDet([]);
                }
            };


        }
    }
        return irtshootViewModel;
    }
)