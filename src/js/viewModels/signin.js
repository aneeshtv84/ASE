'use strict';
define(['ojs/ojcore', 'knockout', 'appController', 'appUtils',
        'ojs/ojknockout',
        'ojs/ojcheckboxset',
        'ojs/ojinputtext',
        'ojs/ojbutton',
        'ojs/ojvalidationgroup',
        'ojs/ojanimation','ojs/ojformlayout','ojs/ojdialog'], function(oj, ko, app, appUtils) {
  class signin {
      constructor() {
    var self = this;

    self.transitionCompleted = function () {
        appUtils.setFocusAfterModuleLoad("signInBtn");
        var animateOptions = {
          delay: 0,
          duration: "1s",
          timingFunction: "ease-out",
        };
        var bgEl = document.getElementsByClassName("container")[0];
        if (bgEl) {
          oj.AnimationUtils["fadeIn"](bgEl, animateOptions);
        }
      };

    self.groupValid = ko.observable();
    self.SignIn = ko.observable();
    self.LoginErr = ko.observableArray([]);
    self.OnePlaceuserName = ko.observable();
    self.OnePlacepassWord = ko.observable();
    self.CancelBehaviorOpt = ko.observable('icon');
    self.signIn = function(data, event) {
        var valid = self._checkValidationGroup("tracker");
        if (valid){
    sessionStorage.setItem("timeInetrval",0);
    // //console.log(timeout: sessionStorage.getItem("timeInetrval"));
      //  document.querySelector('#signInProgress').open();
           self.SignIn('');
           self.LoginErr([]);

                        //key generation
                        const characters ='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
                        function generateString(length) {
                            let result = '';
                            const charactersLength = characters.length;
                            for ( let i = 0; i < length; i++ ) {
                                result += characters.charAt(Math.floor(Math.random() * charactersLength));
                            }
                        
                            return result;
                        }
                        var key = "."+generateString(8);
           $.ajax({
                url: "http://46.137.45.173:9030/api/v2/onep/login",
                // url: "/oneplogin",
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                   user: self.OnePlaceuserName(),
                   passwd : self.OnePlacepassWord(),
                   onepsuid :  key
                }),
                dataType: 'json',
                timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        global: false, 
            beforeSend: function () {
                app.globalProgressMessage("Authenticating...");
                app.globalBusy(true);
                app.callWhenReady('#GlobalProgressDialog', 'open');
            },
            complete: function () {
                app.globalBusy(false);
                app.callWhenReady('#GlobalProgressDialog', 'close');
            },
            error: function (xhr, textStatus, errorThrown) {
                if (textStatus === 'timeout' || xhr.status === 0) {
                    app.showGlobalError(app.deploymentUnreachableMessage(), "Connection Error");
                } else {
                    app.showGlobalError(app.extractErrorMessage(xhr), "Connection Failed");
                }
            },
                success: function (data) {
                   if (data[1]== 'Y') {
                       sessionStorage.setItem("userRole", data[2]);
                       sessionStorage.setItem("onepsuid", key);
                       sessionStorage.setItem("Dep_Url", data[3]);
                       sessionStorage.setItem("Dep_Name", data[4]);
                       sessionStorage.setItem("Dep_Type", data[5]);
                       sessionStorage.setItem("AccessToken", data[6]);
                       var login = localStorage.getItem('login');
                       self.SignIn('Y');
                       if(login == "yes"){
                        // document.querySelector('#signInProgress').close();
                        app.onLoginSuccess();
                       }else{
                        setTimeout(function(){
                            // document.querySelector('#signInProgress').close();
                            app.onLoginSuccess();
                            }, 1000);
                       }
                       
                       localStorage.setItem('login', 'yes');
                       sessionStorage.setItem("userName", self.OnePlaceuserName());
                   }
                   else {
                       self.SignIn('N');
                       document.querySelector('#LoginErrDialog').open();
                       self.LoginErr(data[0]);
                    }
                   return self;
               }

           })
        }
    };

    self.features = ko.observableArray([
        {
          iconClass: "fas fa-shield-alt fa-2x",
          title: "Enterprise-grade security",
          desc: "Bank-level encryption and compliance",
        },
        {
          iconClass: "fas fa-database fa-2x",
          title: "Integrated Native Database Tools",
          desc: "Seamless integration with your existing workflow",
        },
        {
          iconClass: "fas fa-sync-alt fa-2x",
          title: "Zero Downtime with Enterprise-grade Change Data Capture",
          desc: "Change Data Capture without interruption",
        },
        {
          iconClass: "fas fa-network-wired fa-2x",
          title: "Latency-Optimized Cross Region Replication",
          desc: "Change Data Capture without interruption",
        },
        {
          iconClass: "fas fa-globe fa-2x",
          title: "Multi-Region Multi-Cloud  Deployment",
          desc: "Deploy workloads across regions with built-in failover and resilience",
        },
      ]);



    self._checkValidationGroup = (value) => {
        ////console.log(value)
        var tracker = document.getElementById(value);
        ////console.log(tracker.valid)
        if (tracker.valid === "valid") {
            return true;
        }
        else {

            tracker.showMessages();
            tracker.focusOn("@firstInvalidShown");
            return false;
        }
    };

    self.LoginMsgOKClose = function () {
    document.querySelector('#TimeoutSign').close();
    document.querySelector('#LoginErrDialog').close();
    document.querySelector('#signInProgress').close();
    }
   }
  }
  return signin;
});
