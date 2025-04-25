define(['ojs/ojcore', 'knockout', 'jquery','appController','ojs/ojpagingdataproviderview','ojs/ojarraydataprovider','ojs/ojknockout', 'ojs/ojtable', 'ojs/ojpagingcontrol', 'ojs/ojgauge','ojs/ojdialog', 'ojs/ojprogress-bar'],
      function (oj, ko, $, app ,PagingDataProviderView, ArrayDataProvider) {
        class AllLogViewModel {
          constructor(context){
            var self = this;
            self.DepName = context.DepName;
            self.AllData = ko.observableArray([]);
            
          self.lineNum = ko.observable(0); 
          self.eofMsg = ko.observable();

         self.handleOpen  = function (data,event) {
                document.querySelector("#dialog1").open();
                 $.ajax({
                        url: self.DepName() + "/ggerrlog",
                        type: 'POST',
                        data: JSON.stringify({
                            lineNum : self.lineNum()
                        }),
                        dataType: 'json',
                        context: self,
                        error: function (e) {
                            //console.log(e);
                        },
                        success: function (data) {
                            for (var i = 0; i < data[0].length; i++) {
                                self.AllData.push({ AllTime :data[0][i].AllVal[0],AllSev : data[0][i].AllVal[1] ,AllCode : data[0][i].AllVal[2],AllDesc : data[0][i].AllVal[3] });   
                            }
                            self.lineNum(data[1]);
                            self.eofMsg(data[2]);
                                document.querySelector("#dialog1").close();
                            return self;

                             
                                 } 
                              })
                            }  
 
             
     self.allcolumnArray = [{ headerText: 'Time ',
        field: 'AllTime' },
      { headerText: 'Severity ',
        field: 'AllSev' },
      { headerText: 'Code ',
        field: 'AllCode' },
      { headerText: 'Message ',
        field: 'AllDesc' }];
          
            //console.log(self);
            self.allDataProvider = new PagingDataProviderView(new ArrayDataProvider(self.AllData, { idAttribute: 'AllTime' }));
    

            self.connected = function () { 
              if (sessionStorage.getItem("userName")==null) {
                  oj.Router.rootInstance.go('signin');
              }
              else
              {
                app.onAppSuccess();
              }
  
          };
      
      
            }
          }
                    return AllLogViewModel;
        });

  
