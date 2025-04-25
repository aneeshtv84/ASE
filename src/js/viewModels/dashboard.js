define(['knockout', 'jquery', 'appController', 'ojs/ojarraydataprovider', "ojs/ojhtmlutils", "ojs/ojknockout", "ojs/ojchart", "ojs/ojtoolbar",
  "ojs/ojbinddom", "ojs/ojformlayout", "ojs/ojmessages","ojs/ojgauge"],
    function (ko, $, app, ArrayDataProvider) {

        class DashboardViewModel {
            constructor(context){
            var self = this;
            self.ProcessLag = ko.observableArray([]);
            self.ProcessLagChk = ko.observableArray([]);
            self.Total_Process_Memory = ko.observable();
            self.Total_System_Memory_Usage = ko.observable();
            self.CpuUser = ko.observable(0);
            self.CpuSystem = ko.observable(0);
            self.LoadAvg = ko.observable(0);
            let counter = 0;
            let flag = 0;

            this.lineTypeValue = ko.observable("curved");
            self.stackValue = ko.observable("off");
            self.orientationValue = ko.observable("vertical");
            var monAll;
            var memMon;
            
            self.DepName = context.routerState.detail.dep_url;

            function monitorAll() {
                $.ajax({
                    url: self.DepName() + "/ggmonitorall",
                    type: 'GET',
                    dataType: 'json',
                    context: self,
                    error: function (e) {
                        //console.log(e);
                    },
                    success: function (data) {
                        counter = counter + 1;
                        for (var i = 0; i < data[0].length; i++) {
                            if (data[0][i].extstat) {
                                self.ProcessLag.push({ series: data[0][i].extname, lag : data[0][i].extlag, lagchk : data[0][i].extchklag, quarter : (data[0][i].extIncTime).split(" ")[1]});
                            }
                            else if (data[0][i].pmpstat) {
                                self.ProcessLag.push({ series: data[0][i].pmpname, lag : data[0][i].pmplag, lagchk : data[0][i].pmpchklag,  quarter : (data[0][i].pmpIncTime).split(" ")[1]});
                            }
                            else if (data[0][i].repstat) {
                                self.ProcessLag.push({ series: data[0][i].repname, vaue : data[0][i].replag,lagchk : data[0][i].repchklag, quarter : (data[0][i].repIncTime).split(" ")[1]});
                            }
                            }
                        if(counter >= 10){
                            for(i=0 ; i<(data[0].length-1); i++){
                                self.ProcessLag.shift();
                            }
                       
                        }

                        return self;

                    }

                })
            }

            self.LagDP = new ArrayDataProvider(self.ProcessLag, {
                keyAttributes: "series",
            });

            self.ProcessMetrics = ko.observableArray([]);
            self.CPUProcessMetrics = ko.observableArray([]);
            self.IOProcessMetrics = ko.observableArray([]);

            this.xTitle = ko.observable();
            this.yTitle = ko.observable();

            this.xTitle = ko.observable("Time");
            this.size = ko.observable();
            this.maxsize = ko.observable();
            this.xStyle = ko.observable({ fontStyle: "bold", color: "#6070C7" });
            this.xAxisLineColor = ko.observable("#9E9E9E");
            this.xAxisLineWidth = ko.observable(1);
            this.yTitle = ko.observable("Memory Usage Bytes");
            this.yTitleCPU = ko.observable("CPU Usage %");
            this.yTitleDisk = ko.observable("Disk Usage Bytes");
            this.yTitleDiskCount = ko.observable("Disk Usage Count");
            this.yTitleLag = ko.observable("Lag in Seconds");
            this.yStyle = ko.observable({ fontStyle: "bold", color: "#6070C7" });
            this.yMajorTickColor = ko.observable("#C4CED7");
            this.yMajorTickWidth = ko.observable(1);
            this.yMajorTickStyle = ko.observable("solid");
            this.yTickLabelPosition = ko.observable("outside");
            this.xAxisMem = ko.pureComputed(() => {
                return {
                    title: this.xTitle(),
                    titleStyle: this.xStyle(),
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


            this.yAxisLag = ko.pureComputed(() => {
                return {
                    title: this.yTitleLag(),
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
                    url: self.DepName() + "/memusage",
                    type: 'GET',
                    dataType: 'json',
                    context: self,
                    error: function (e) {
                        //console.log(e);
                    },
                    success: function (data) {
                        flag = flag + 1;
                        for (var i = 0; i < data[0].length; i++) {
                            self.ProcessMetrics.push({ series: data[0][i].group, value: data[0][i].uss, quarter: (data[0][i].inctime).split(" ")[1] });
                        } 
                        for (var i = 0; i < data[2].length; i++) {
                            self.CPUProcessMetrics.push({ series : data[2][i].group, value: data[2][i].cpu , group : (data[2][i].inctime).split(" ")[1] });
                        }
                        for (var i = 0; i < data[3].length; i++) {
                            self.IOProcessMetrics.push({ series : data[3][i].group , diskbytes: data[3][i].diskbytes, diskcount : data[3][i].diskcount, group : (data[2][i].inctime).split(" ")[1] });
                        }
                        self.LoadAvg('');
                        self.CpuUser('');
                        self.CpuSystem('');
                        self.Total_System_Memory_Usage('');
                        self.LoadAvg(data[1].loadavg[1]);
                        self.CpuUser(data[1].cpuUser);
                        self.CpuSystem(data[1].cpuSystem);
                        self.Total_System_Memory_Usage(data[1].percent);
                        //console.log(self.Total_System_Memory_Usage());

                        self.Total_Process_Memory('');
                        self.Total_Process_Memory(data[4]);
                           if(flag >= 10){
                            for(var j=0 ; j<data[0].length; j++){
                                self.ProcessMetrics.shift();
                            }
                            for(var j=0 ; j<data[3].length; j++){
                                self.IOProcessMetrics.shift();
                                
                            }
                            for(var j=0 ; j<data[2].length; j++){
                                self.CPUProcessMetrics.shift();   
                            }
                        }
                        //console.log(self);
                        return self;
                    }
                })
            };


            self.MemoryDP = new ArrayDataProvider(self.ProcessMetrics, {
                keyAttributes: "series",
            });


            self.CPUDP = new ArrayDataProvider(self.CPUProcessMetrics, {
                keyAttributes: "series",
            });


            self.IODP = new ArrayDataProvider(self.IOProcessMetrics, {
                keyAttributes: "series",
            });

            this.hiddenCategories = ko.observableArray([]);
              this.categoryInfo = ko.pureComputed(() => {
                  const categories = this.hiddenCategories();
                  return categories.length > 0 ? categories.join(", ") : "none";
              });

              this.thresholdValues = [{ max: 10 }, { max: 20 }, {}];

              this.referenceLines = [
                { value: 10, color: "green" },
                { value: 30, color: "orange" },
                { value: 67, color: "red" },
            ];


            self.connected = function () {
               if (sessionStorage.getItem("userName") == null) {                    
                   router.go('signin');                }
              else {
                   app.onAppSuccess(); 
                   counter = 0;
                   flag=0
                   self.LoadAvg(0);
                   self.CpuUser(0);
                   self.CpuSystem(0);
                   self.Total_System_Memory_Usage(0);
                    self.ProcessLag([]);
                    self.CPUProcessMetrics([]);
                    self.ProcessMetrics([]);
                    self.IOProcessMetrics([]);
                    getMemUsage();
                    monitorAll();
                    monAll = setInterval(monitorAll, 10000);
                    memMon = setInterval(getMemUsage, 10000);
           }
                
            };



            /**
             * Optional ViewModel method invoked after the View is disconnected from the DOM.
             */
            self.disconnected = function () {
                clearInterval(monAll);
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
        return DashboardViewModel;
    }
);
