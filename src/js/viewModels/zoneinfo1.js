define(['knockout', 'jquery','appController',  'ojs/ojasyncvalidator-regexp', 'ojs/ojconverterutils-i18n', 'ojs/ojconverter-datetime', 
'ojs/ojconverter-number',"ojs/ojpagingdataproviderview",'ojs/ojarraydataprovider', "ojs/ojattributegrouphandler","ojs/ojlistdataproviderview","ojs/ojkeyset", 
'ojs/ojknockout', 'ojs/ojtrain', 'ojs/ojradioset', 'ojs/ojbutton', 'ojs/ojlabelvalue', 'ojs/ojdatetimepicker', 'ojs/ojlabel',"ojs/ojlistview", "ojs/ojlistitemlayout",
 'ojs/ojformlayout', 'ojs/ojinputtext', 'ojs/ojselectsingle', 'ojs/ojinputnumber', 'ojs/ojvalidationgroup', 'ojs/ojselectcombobox', 
 'ojs/ojdialog', 'ojs/ojswitch','ojs/ojcheckboxset','ojs/ojprogress-bar','ojs/ojtable','ojs/ojhighlighttext',"ojs/ojpagingcontrol","ojs/ojgauge","ojs/ojchart", "ojs/ojtoolbar"],
        function (ko, $,app,AsyncRegExpValidator, ConverterUtilsI18n, DateTimeConverter, NumberConverter, PagingDataProviderView,ArrayDataProvider,ojattributegrouphandler_1,ListDataProviderView,ojkeyset_1) {

            class InitialLoadViewModel {
 
                constructor(args) {
                var self = this;
                self.DepName = args.routerState.detail.dep_url;
                self.isFormReadonly = ko.observable(false); 
                self.CancelBehaviorOpt = ko.observable('icon');
                self.currentZone = ko.observable()
                self.currentObject = ko.observable()
                self.zoneDetDP = ko.observableArray([])
                self.zoneDet = ko.observableArray([])
                self.objectDet = ko.observableArray([])
                self.objectDetDP = ko.observableArray([])
                self.zoneFunctions = ko.observable('');
                self.viewText = ko.observable();
                self.TgtOnePDepName = ko.observable();
                self.onepDepList = ko.observableArray([]);
                self.TGTonepDepUrl = ko.observable()
                self.zoneName = ko.observable()
                self.saveViewMsg = ko.observable();

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

                            self.objectDet([]);
                            self.objectDet.push({'value' : "View", 'label' : 'View'},{'value' : 'Procedure', 'label' : 'Procedure'},{'value' : 'Triggers', 'label' : 'Triggers'});
                            
                            self.onepDepList.valueHasMutated();
                            return self;
                        }
        
                    })
                }
        
                self.onepDepListDP = new ArrayDataProvider(self.onepDepList, {keyAttributes: 'value'});
                self.objectDetDP = new ArrayDataProvider(self.objectDet, {keyAttributes: 'value'});

                self.SelectTGTDeployment = (event,data) =>{
                    if (self.TgtOnePDepName()){
                      //   document.querySelector('#SelectSchemaProcessDialog').open();
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
                          self.TGTonepDepUrl(data[0]);
                        //   getZoneList();
                          return self;
                      }
                  })
                }
            
            };


            self.getZoneList = (event,data) =>{
                document.querySelector('#LampDialog').open();
                $.ajax({
                    url: self.TGTonepDepUrl() + "/getZoneList1",
                    data: JSON.stringify({
                        key : "zone",
                        objectType : self.currentObject(),
                    }),
                    type: 'POST',
                    dataType: 'json',
                    context: self,
                    error: function (e) {
                        document.querySelector('#LampDialog').close();
                    },
                    success: function (data) {
                        // console.log(data)
                        self.zoneDet([]);
                        if(data != "No File") {
                            for (var i = 0; i < data.length; i++) {
                                self.zoneDet.push({'value' : data[i], 'label' : data[i]});
                            }
                        }
                        document.querySelector('#LampDialog').close();
                        return self;
                    }
                })
            };

                self.zoneDetDP = new ArrayDataProvider(self.zoneDet, {keyAttributes: 'value'});

                self.zoneInfoChange = (event,data) =>{
                    document.querySelector('#LampDialog').open();
                    if (self.currentZone()) {
                        $.ajax({
                            url: self.TGTonepDepUrl()  + "/getZoneDetails1",
                            data: JSON.stringify({
                                currentZone : self.currentZone(),
                                objectType : self.currentObject(),
                            }),
                            type: 'POST',
                            dataType: 'json',
                            context: self,
                            error: function (e) {
                                document.querySelector('#LampDialog').close();
                            },
                            success: function (data) {
                                // console.log(data)
                                document.querySelector('#LampDialog').close();
                                self.zoneFunctions('');
                                if(data != "No File") {
                                    self.zoneFunctions(data);
                                }
                                return self;
                            }
                        })
                    }
                };

                self.updateZone = (event,data) =>{
                // console.log(self.zoneFunctions())
                document.querySelector('#LampDialog').open();
                self.saveViewMsg('');  
                    $.ajax({
                        url: self.TGTonepDepUrl()  + "/updateZoneDetails1",
                        data: JSON.stringify({
                            currentZone : self.currentZone(),
                            zoneFunctions : self.zoneFunctions(),
                            objectType : self.currentObject(),
                        }),
                        type: 'POST',
                        dataType: 'json',
                        context: self,
                        error: function (e) {
                            document.querySelector('#LampDialog').close();
                        },
                        success: function (data) {
                            // console.log(data)
                            document.querySelector('#LampDialog').close();
                            document.querySelector('#openDialog').open();
                            if(data == "Success") {
                                self.saveViewMsg("Updated");
                            }
                            return self;
                        }
                    })  
                    
                };

                self.saveOKView = function (data, event) {
                    document.querySelector('#openDialog').close();
                }

                self.addZoneModalClose =  function(data, event) {
                    document.querySelector('#addZoneDlg').close();
                }

                self.addZoneModal = (event,data) =>{
                    document.querySelector('#addZoneDlg ').open();
                };

                self.addZone = (event,data) =>{
                    // console.log(self.currentObject())
                    document.querySelector('#LampDialog').open();
                        $.ajax({
                            url: self.TGTonepDepUrl()  + "/addZone1",
                            data: JSON.stringify({
                                zoneName : self.zoneName(),
                                objectType : self.currentObject(),
                            }),
                            type: 'POST',
                            dataType: 'json',
                            context: self,
                            error: function (e) {
                                document.querySelector('#LampDialog').close();
                            },
                            success: function (data) {
                                document.querySelector('#LampDialog').close();
                                document.querySelector('#openDialog').open();
                                self.saveViewMsg(data);
                                return self;
                            }
                        })  
                        
                    };

              

                  self.connected = function () { 
                    if (sessionStorage.getItem("userName")==null) {
                        self.router.go({path : 'signin'});
                    }
                    else{
                        app.onAppSuccess();
                        getOnepDep();
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
