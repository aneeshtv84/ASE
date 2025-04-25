define(['knockout', 'jquery', 'appController', 'ojs/ojarraydataprovider', "ojs/ojhtmlutils", "ojs/ojknockout", "ojs/ojchart", "ojs/ojtoolbar",
  "ojs/ojbinddom", "ojs/ojformlayout", "ojs/ojmessages","ojs/ojgauge","ojs/ojinputtext"],
    function (ko, $, app, ArrayDataProvider) {

        class ProcessViewModel {
            constructor(args) {
            var self = this;
            self.DepName = args.routerState.detail.dep_url;
            self.ExtData1 = ko.observableArray([]);
            let counter = 0;
            let flag = 0;
            let CPUThreadMerticsArraylength = 0;

            self.rss = ko.observable();
            self.uss = ko.observable();
            self.mem = ko.observable();
            self.lib = ko.observable();
            self.swap = ko.observable() ;
            self.vms = ko.observable() ;
            self.Max_Thread_CPU = ko.observable();
            self.processName = ko.observable();
            self.cpu_user = ko.observable();
            self.cpu_kernel = ko.observable();
            self.cpu_iowait = ko.observable();
            self.read_bytes = ko.observable(0);
            self.delta_read_bytes = ko.observable(0);
            self.write_bytes = ko.observable(0);
            self.delta_write_bytes = ko.observable(0);
            self.read_count = ko.observable(0);
            self.delta_read_count = ko.observable(0);
            self.write_count = ko.observable(0);
            self.delta_write_count = ko.observable(0);
            self.cpuSysResult = ko.observable();
            self.cpuUserResult = ko.observable();

            self.isFormReadonly = ko.observable(true);

            this.lineTypeValue = ko.observable("curved");
            self.stackValue = ko.observable("off");
            self.orientationValue = ko.observable("vertical");
            var memMon;

            self.Total_Process_Memory = ko.observable(0);
            self.MemProcessMetrics = ko.observableArray([]);
            self.CPUProcessMetrics = ko.observableArray([]);
            self.CPUThreadMetrics = ko.observableArray([]);
            self.CPUThreadMetricsSub = ko.observableArray([]);
            self.IOProcessMetrics = ko.observableArray([]);
            self.IOProcessCountMetrics = ko.observableArray([]);

            this.xTitle = ko.observable("Time");
            this.size = ko.observable();
            this.maxsize = ko.observable();
            this.xStyle = ko.observable({ fontStyle: "bold", color: "#6070C7" });
            this.xAxisLineColor = ko.observable("#9E9E9E");
            this.xAxisLineWidth = ko.observable(1);
            this.yTitle = ko.observable("Memory Usage %");
            this.yTitleCPU = ko.observable("CPU Usage %");
            this.yTitleDisk = ko.observable("Disk Usage Bytes");
            this.yTitleDiskCount = ko.observable("Disk Usage Count");
            this.yStyle = ko.observable({ fontStyle: "bold", color: "#6070C7" });
            this.yMajorTickColor = ko.observable("#C4CED7");
            this.yMajorTickWidth = ko.observable(1);
            this.yMajorTickStyle = ko.observable("solid");
            this.yTickLabelPosition = ko.observable("outside");
            this.xAxisMem = ko.pureComputed(() => {
                return {
                    title: this.xTitle(),
                    titleStyle: this.xStyle(),
                    size : this.size(),
                    maxsize : this.maxsize(),
                    axisLine: {
                        lineColor: this.xAxisLineColor(),
                        lineWidth: this.xAxisLineWidth(),
                    },
                };
            });
            this.yAxisMem = ko.pureComputed(() => {
                return {
                    title: this.yTitle(),
                    titleStyle: this.yStyle(),
                    size : this.size(),
                    maxsize : this.maxsize(),
                    majorTick: {
                        lineColor: this.yMajorTickColor(),
                        lineWidth: this.yMajorTickWidth(),
                        lineStyle: this.yMajorTickStyle(),
                    },
                    tickLabel: {
                        position: this.yTickLabelPosition(),
                    },
                };
            });

            this.yAxisCPU = ko.pureComputed(() => {
                return {
                    title: this.yTitleCPU(),
                    titleStyle: this.yStyle(),
                    size : this.size(),
                    maxsize : this.maxsize(),
                    majorTick: {
                        lineColor: this.yMajorTickColor(),
                        lineWidth: this.yMajorTickWidth(),
                        lineStyle: this.yMajorTickStyle(),
                    },
                    tickLabel: {
                        position: this.yTickLabelPosition(),
                    },
                };
            });


            this.yAxisDisk = ko.pureComputed(() => {
                return {
                    title: this.yTitleDisk(),
                    titleStyle: this.yStyle(),
                    size : this.size(),
                    maxsize : this.maxsize(),
                    majorTick: {
                        lineColor: this.yMajorTickColor(),
                        lineWidth: this.yMajorTickWidth(),
                        lineStyle: this.yMajorTickStyle(),
                    },
                    tickLabel: {
                        position: this.yTickLabelPosition(),
                    },
                };
            });
            this.yAxisDiskCount = ko.pureComputed(() => {
                return {
                    title: this.yTitleDiskCount(),
                    titleStyle: this.yStyle(),
                    size : this.size(),
                    maxsize : this.maxsize(),
                    majorTick: {
                        lineColor: this.yMajorTickColor(),
                        lineWidth: this.yMajorTickWidth(),
                        lineStyle: this.yMajorTickStyle(),
                    },
                    tickLabel: {
                        position: this.yTickLabelPosition(),
                    },
                };
            });

            function getMemUsage() {
                $.ajax({
                    url: self.DepName() + "/memusagebyprocess",
                    type: 'POST',
                    dataType: 'json',
                    data: JSON.stringify({
                        processName : self.processName(),
                        read_bytes :  self.read_bytes(),
                        write_bytes :  self.write_bytes(),
                        read_count :  self.read_count(),
                        write_count :  self.write_count()
                    }),
                    context: self,
                    error: function (e) {
                        //console.log(e);
                    },
                    success: function (data) {
                        flag = flag + 1;
                            self.MemProcessMetrics.push({ series: 'uss', value: data[0].ussper , quarter: (data[0].inctime).split(" ")[1] });
                            self.MemProcessMetrics.push({ series: 'rss', value: data[0].rssper, quarter: (data[0].inctime).split(" ")[1]});
                            self.MemProcessMetrics.push({ series: 'vms', value: data[0].vmsper, quarter: (data[0].inctime).split(" ")[1]});
                            self.rss('');
                            self.uss('');
                            self.mem('');
                            self.lib('');
                            self.swap('');
                            self.vms('');
                            self.vms(data[0].vms);
                            self.rss(data[0].rss);
                            self.uss(data[0].uss);
                            self.mem(data[0].mem);
                            self.lib(data[0].lib);
                            self.swap(data[0].swap);
                            self.cpu_user('');
                            self.cpu_kernel('');
                            self.cpu_iowait('');
                            self.cpu_user(data[1].user);
                            self.cpu_kernel(data[1].kernel);
                            self.cpu_iowait(data[1].iowait);

                            for (var i = 0; i < data[2].length; i++) {
                                self.CPUThreadMetrics.push({ series : data[2][i].thread + ' ' + data[2][i].group, value: data[2][i].cpu , 
                                                              group : (data[2][i].inctime).split(" ")[1] , cpuuser : data[2][i].cpuuser , cpusys : data[2][i].cpusys });
                            }
    
    
                            var CPUThreadMerticsArraylength = self.CPUThreadMetrics().length - 1;
                            self.CPUThreadMetricsSub([]);

                      
                        for (var i = 0; i < CPUThreadMerticsArraylength; i++) {
                            if(self.CPUThreadMetrics._latestValue[i].group == self.CPUThreadMetrics._latestValue[CPUThreadMerticsArraylength].group){
                                self.CPUThreadMetricsSub.push(self.CPUThreadMetrics()[i]);
                                
                            }
                        }
                        //console.log(self.CPUThreadMetricsSub())
                        var result = ko.utils.arrayFirst(self.CPUThreadMetricsSub(),function(o){
                            return o.value === Math.max.apply(null,ko.utils.arrayMap(self.CPUThreadMetricsSub(),function(e){
                            return e.value;
                            }));
                        });
                        self.CPUThreadMetrics.valueHasMutated;

                            self.cpuSysResult(0);
                            self.cpuSysResult(result['value']);

                            self.IOProcessMetrics.push({series: 'read' , value: data[3].read_bytes , group : (data[3].inctime).split(" ")[1] });
                            self.IOProcessMetrics.push({series: 'write' , value: data[3].write_bytes , group : (data[3].inctime).split(" ")[1] });

                        self.read_bytes('');
                        self.delta_read_bytes('');
                        self.write_bytes('');
                        self.delta_write_bytes('');
                        self.read_count('');
                        self.delta_read_count('');
                        self.write_count('');
                        self.delta_write_count('');
                        self.read_bytes(data[3].read_bytes);
                        self.delta_read_bytes(data[3].delta_read_bytes);
                        self.write_bytes(data[3].write_bytes);
                        self.delta_write_bytes(data[3].delta_write_bytes);
                        self.read_count(data[3].read_count);
                        self.delta_read_count(data[3].delta_read_count);
                        self.write_count(data[3].write_count);
                        self.delta_write_count(data[3].delta_write_count);

                        self.IOProcessCountMetrics.push({series: 'read' , value: data[3].read_count , group : (data[3].inctime).split(" ")[1] });
                        self.IOProcessCountMetrics.push({series: 'write' , value: data[3].write_count , group : (data[3].inctime).split(" ")[1] });
                        //console.log(flag)
                        if(flag >= 5){
                            for(var j=0 ; j<3; j++){
                                self.MemProcessMetrics.shift();   
                                
                            }
                            for(var j=0 ; j<2; j++){
                                self.IOProcessMetrics.shift();
                            }

                            for(var j=0 ; j<2; j++){
                                self.IOProcessCountMetrics.shift();
                            }
                     
                                for(var j=0 ; j<data[2].length; j++){
                                self.CPUThreadMetrics.shift();
                                
                            }
                        }
                            
                        //console.log(self);
                        return self;
                    }
                })
            };


            self.MemoryDP = new ArrayDataProvider(self.MemProcessMetrics, {
                keyAttributes: "series",
            });


            self.CPUDP = new ArrayDataProvider(self.CPUThreadMetrics, {
                keyAttributes: "series",
            });


            self.IODP = new ArrayDataProvider(self.IOProcessMetrics, {
                keyAttributes: "series",
            });

            self.IOCountDP = new ArrayDataProvider(self.IOProcessCountMetrics, {
                keyAttributes: "series",
            });

            this.hiddenCategories = ko.observableArray([]);
              this.categoryInfo = ko.pureComputed(() => {
                  const categories = this.hiddenCategories();
                  return categories.length > 0 ? categories.join(", ") : "none";
              });

              this.thresholdValues = [{ max: 10 }, { max: 20 }, {}];
              this.gaugeValue = ko.observable(10);

              this.referenceLines = [
                { value: 10, color: "green" },
                { value: 30, color: "orange" },
                { value: 67, color: "red" },
            ];


            self.connected = function () {
               if (sessionStorage.getItem("userName") == null) {                    router.go('signin');                }
              else {
                    app.onAppSuccess();
                    self.processName('');
                    self.ExtData1([]);
                    self.CPUProcessMetrics([]);
                    self.CPUThreadMetrics([]);
                    self.MemProcessMetrics([]);
                    self.IOProcessMetrics([]);
                    self.router = args.router;
                    self.processName(args.params.process);
                    getMemUsage();
                    memMon = setInterval(getMemUsage, 10000);
           }
                
            };



            /**
             * Optional ViewModel method invoked after the View is disconnected from the DOM.
             */
            self.disconnected = function () {
                clearInterval(memMon);
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
        return ProcessViewModel;
    }
);
