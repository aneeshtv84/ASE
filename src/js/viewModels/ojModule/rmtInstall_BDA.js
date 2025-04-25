define(['ojs/ojcore', 'knockout', 'jquery','appController','ojs/ojarraydataprovider', 'ojs/ojknockout-keyset', 'ojs/ojasyncvalidator-regexp', 'ojs/ojknockout', 
        'ojs/ojtrain', 'ojs/ojradioset', 'ojs/ojvalidationgroup', 'ojs/ojbutton', 'ojs/ojlabelvalue', 'ojs/ojfilepicker', 'ojs/ojlabel', 
        'ojs/ojformlayout', 'ojs/ojinputtext', 'ojs/ojselectsingle', 'ojs/ojinputnumber', 'ojs/ojlistview', 'ojs/ojselectcombobox', 
        'ojs/ojdialog', 'ojs/ojlistitemlayout', 'ojs/ojcheckboxset', 'ojs/ojprogress-bar', 'ojs/ojswitch', 'ojs/ojavatar','ojs/ojvalidationgroup'],
    function (oj, ko, $,app, ArrayDataProvider, keySet, AsyncRegExpValidator) {
        class AddDeployViewModel {
            constructor(context) {
                var self = this;
                self.DepName = context.DepName;
                self.currentExtType = ko.observable('CA');
                self.startExtChk = ko.observable(true);

                self.ggDephName = ko.observable();
                self.ggDepOSPlat = ko.observable();
                self.ggDepDBClientVer = ko.observable();
                self.ggDepGGVer = ko.observable();
                self.ggDepGGPlat = ko.observable();           
                self.ggDepJavaVer = ko.observable();
                self.ggDepJavaHome = ko.observable();
                self.ggDepGGHome = ko.observable();
                self.uploadState = ko.observable(true);
                self.groupValid = ko.observable();
                self.CancelBehaviorOpt = ko.observable('icon');

                self.onepDepName = ko.observable("");
                self.selectedStepValue = ko.observable('stp1');
                self.selectedStepLabel = ko.observable('Select Deployment');
                self.selectedStepFormLabel = ko.observable('Select Deployment');

                self.stepArray =
                    ko.observableArray([
                        { label: 'Select Deployment', id: 'stp1' },
                        { label: 'Software Install', id: 'stp2' }
                    ]);

                self.onepDepUrl = ko.observable(context.DepName);
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

                self.onepDepList = ko.observableArray([]);

                function getOnepDep() {
                    $.ajax({
                        url: self.DepName() + "/onepdep",
                        type: 'GET',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#TimeoutRM').open();
                            }
                        },
                        success: function (data) {
                            self.onepDepList([]);
                            for (var i = 0; i < data[0].length; i++) {
                                self.onepDepList.push({ 'label': data[0][i].dep, value: data[0][i].dep });
                            }
                            self.onepDepList.valueHasMutated();
                            self.onepDepUrl(self.DepName())
                            return self;
                        }

                    })
                }

                self.onepDepListDP = new ArrayDataProvider(self.onepDepList, { keyAttributes: 'value' });



                self.SelectDeployment = (event,data) =>{
                    if(self.onepDepName != ""){
                    self.onepDepUrl('');
                    $.ajax({
                      url: self.DepName() + "/onepdepurl",
                      type: 'POST',
                      data: JSON.stringify({
                        dep: self.onepDepName()
                    }),
                      dataType: 'json',
                      timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#TimeoutRM').open();
                            }
                        },
                      success: function (data) {
                          self.onepDepUrl(data[0]);
                          getDepDet();
                          return self;
                      }
                  })
                }
                 };

                 
        function getDepDet(){
            if (self.onepDepUrl().length > 0) {
                self.ggDephName('');
                self.ggDepOSPlat('');
                self.ggDepGGVer('');
                self.ggDepGGPlat('');                
                self.ggDepJavaVer('');
                self.ggDepGGHome('');
                self.ggDepJavaHome('');
             $.ajax({
               url: self.onepDepUrl() + "/depdet",
               type: 'GET',
               dataType: 'json',
               timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#TimeoutRM').open();
                            }
                        },
               success: function (data) {
                 self.ggDephName(data[0]);
                 self.ggDepOSPlat(data[1] + '_' + data[2]);
                 self.ggDepGGVer(data[3]);
                 self.ggDepGGPlat(data[4]);                
                 self.ggDepJavaVer(data[5]);
                 self.ggDepGGHome(data[6]);
                 self.ggDepJavaHome(data[7]);
                 self.uploadState(false);
                 return self;
               }
       
           })
        }
        };
 





                // self.imgNameArray = ko.observableArray([]);

                // function getImagesfromServer() {
                //     self.imgNameArray([]);
                //     $.ajax({
                //         url: self.onepDepName() + "/images",
                //         type: 'GET',
                //         dataType: 'json',
                //         error: function (e) {
                //             //console.log(e);
                //         },
                //         success: function (data) {

                //             for (var i = 0; i < data[0].length; i++) {
                //                 self.imgNameArray.push({ label: data[0][i].IMGNAME, value: data[0][i].IMGPLAT });
                //             }

                //             //console.log(self)

                //             return self;
                //         }
                //     })
                // }

                // self.imgNameDP = new ArrayDataProvider(self.imgNameArray, { keyAttributes: 'value' });
                
                self.regExpValidator =
                    new AsyncRegExpValidator({
                        pattern: "[a-zA-Z ,.'-]{1,}",
                        hint: "1 or more letters",
                        messageDetail: "You must enter at least 1 letter"
                    });


                self.soft = ko.observable();

                self.previousStep = function () {
                    var train = document.getElementById('train');
                    var prev = train.getPreviousSelectableStep();
                    if (prev != null) {
                        self.selectedStepValue(prev);
                        self.selectedStepLabel(train.getStep(prev).label);
                        self.selectedStepFormLabel(train.getStep(prev).label);
                    }
                }.bind(this);

                self.nextStep = function (event) {
                    var train = document.getElementById('train');
                    var next = train.getNextSelectableStep();
                    let valid = self._checkValidationGroup("tracker");
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
                        tracker.showMessages();
                        tracker.focusOn("@firstInvalidShown");
                        return;
                    }

                };

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

                //The method updates the label text to show what step the user is on
                self.updateLabelText = function (event) {
                    if (self.selectedStepValue == 'stp2') {
                        self.selectedStepFormLabel('Software Install');
                    } else if (self.selectedStepValue == 'stp1') {
                        self.selectedStepFormLabel('Select Deployment');
                    } 
                };
                
                this.validate = (event) => {
                    var next = train.getNextSelectableStep();
                    var valid = self._checkValidationGroup("tracker");
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

                self.disabled = ko.observable(true);
                self.isDisabled = ko.pureComputed(
                    function () {
                        return self.disabled() == "disable" ? true : false;
                    }
                );

                self.invalidMessage = ko.observable("");
                self.invalidListener = function (event) {
                    self.fileNames([]);
                    self.invalidMessage(
                        "{severity: '" +
                        event.detail.messages[0].severity +
                        "', summary: '" +
                        event.detail.messages[0].summary +
                        "'}"
                    );
                    var promise = event.detail.until;
                    if (promise) {
                        promise.then(
                            function () {
                                self.invalidMessage("");
                            }.bind(this)
                        );
                    }
                }

                self.acceptStr = ko.observable("application/zip");
                self.acceptArr = ko.pureComputed(
                    function () {
                        var accept = self.acceptStr();
                        return accept ? accept.split(",") : [];
                    }
                );


                self.UploadSoftMsg = ko.observable();

                self.progressValue = ko.observable(0);
                self.fileNames = ko.observable([]);



                self.selectListener =  (event) => {
                    var files = event.detail.files;
                    self.fileNames(
                        Array.prototype.map.call(files, function (file) {
                            var formData = new FormData();
                            formData.append("file", file);
                            //console.log(file)
                            $.ajax({
                                url:   self.onepDepUrl() + "/rhpuploadimg",
                                xhr: function () {
                                    var xhr = new window.XMLHttpRequest();
                                    xhr.upload.addEventListener('progress', function (e) {
                                        if (e.lengthComputable) {
                                            //console.log('Bytes Uploaded : ' + e.loaded);
                                            //console.log('Total Size : ' + e.total);
                                            //console.log('Percentage Uploaded : ' + e.loaded / e.total)
                                            self.progressValue.subscribe(function (loaded) {
                                                if (e.loaded !== 100) {
                                                    var loadingRegion = document.getElementById('loadingRegion');
                                                }
                                            });
                                            self.progressValue(Math.ceil((e.loaded / e.total) * 100));
                                        }
                                    });
                                    return xhr;
                                },  
                                type: "POST",
                                data: formData,
                                cache: false,
                                contentType: false,
                                processData: false,
                                error: function (jqXHR, textStatus, errorThrown) {
                                    //console.log(jqXHR);
                                    //console.log(textStatus);
                                    //console.log(errorThrown);
                                },
                                success: (data) => {
                                    //console.log("Success!");
                                    document.querySelector('#UploadSoftDialog').open();
                                    self.UploadSoftMsg(data[0]);
                                    listSoftFiles();
                                    return self
                                }
                            });
                            //console.log(file.name)
                            return file.name;
                        })
                    );
                };


                self.softList = ko.observableArray([]);


                 function listSoftFiles() {
                    self.softList([]);
                    $.ajax({
                        url:  self.onepDepUrl() + "/listsoftfiles",
                        type: 'GET',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#TimeoutRM').open();
                            }
                        },
                        success: function (data) {

                            for (var i = 0; i < data[0].length; i++) {
                                if (data[0][i].filetype == 'patch') {
                                    self.softList.push({ 'id': data[0][i].filename, 'title': data[0][i].filetype, 'image': 'js/ojAvatars/patch.ico' });
                                }
                                else if (data[0][i].filetype == 'software') {
                                    self.softList.push({ 'id': data[0][i].filename, 'title': data[0][i].filetype, 'image': 'js/ojAvatars/software.ico' });
                                }
                            }
                            //console.log(self);
                            return self;
                        }

                    })
                }




                self.listSoftDP = new ArrayDataProvider(self.softList, { keyAttributes: 'id' });

                self.selectedItems = new keySet.ObservableKeySet(); // observable bound to selection option to monitor current selections
                self.selectedSelectionRequired = ko.observable(false);
                self.firstSelectedItem = ko.observable();
                self.selectedIds = ko.observableArray([]);

                self.getDisplayValue = function (set) {
                    var arr = [];
                    set.values().forEach(function (key) {
                        arr.push(key);
                    });
                    return JSON.stringify(arr);
                };

                // Current selection is already monitored through this.selectedItems observable.
                // To perform custom selection logic on selected elements and/or on current item, an option change callback can be used:


                self.runInsLogFile = ko.observableArray([]);
                self.insButton = ko.observable(false);
                self.insProgress = ko.observable(0);

                self.handleSelectedChanged = function () {
                    self.insButton(false);
                    self.insProgress(0);
                    self.runInsLogFile([]);
                };

                self.installSoftware = function (data, event) {
                    self.insProgress(-1);
                    self.insButton(true);
                    self.runInsLogFile([]);
                    $.ajax({
                        url: self.onepDepUrl() + "/viewrunins",
                        type: 'POST',
                        data: JSON.stringify({
                            filename: self.getDisplayValue(self.selectedItems())
                        }),
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#TimeoutRM').open();
                            }
                        },
                        success: function (data) {
                            self.insProgress(0);
                            for (var i = 0; i < data[0].length; i++) {
                                self.runInsLogFile.push(data[0][i]);
                            }
                            return self;
                        }

                    })
                }


                self.imgName = ko.observable();
                self.imgDesc = ko.observable();

                self.saveImgLogFile = ko.observable();
                self.saveButton = ko.observable(false);
                self.saveProgress = ko.observable(0);

                self.createGoldImg = function (data, event) {
                    self.saveProgress(-1);
                    self.saveButton(true);
                    self.saveImgLogFile([]);
                    $.ajax({
                        url: self.DepName() + "/savegoldimg",
                        type: 'POST',
                        data: JSON.stringify({
                            imgUrl: self.DepName() + "/creategoldimg",
                            imgName: self.imgName()
                        }),
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.querySelector('#TimeoutRM').open();
                            }
                        },
                        success: function (data) {
                            self.saveProgress(0);
                            self.saveButton(false);
                            document.querySelector('#saveImgDialog').open();
                            self.saveImgLogFile(data[0]);

                            return self;
                        }
                    })
                }
  
                self.UploadSoftOKClose = function (event) {
                    document.querySelector('#UploadSoftDialog').close();
                };

                self.SaveImgOKClose = function (event) {
                    document.querySelector('#saveImgDialog').close();
                };


                self.cancel = function () {
                    oj.Router.rootInstance.go('incidents');

                }


                self.editListener = function (event) {
                    // toggle the componentDisable knockout binding
                    var disabledState = self.textstateValue();
                    self.edBtnstateValue(disabledState);
                    self.saveBtnStateValue(!disabledState);

                };


                self.connected = function () { 
                    if (sessionStorage.getItem("userName")==null) {
                        oj.Router.rootInstance.go('signin');
                    }
                    else
                    {
                      app.onAppSuccess();
                      getOnepDep();
                      self.selectedStepValue('stp1');
                      self.selectedStepLabel('Select Deployment');
                      self.selectedStepFormLabel('Select Deployment');
                    }
                  };

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
        return AddDeployViewModel;
    }
);
