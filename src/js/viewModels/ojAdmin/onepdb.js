
define([ 'knockout', 'jquery','appController' ,'ojs/ojarraydataprovider','ojs/ojknockout', 'ojs/ojinputtext', 'ojs/ojlabel', 'ojs/ojformlayout','ojs/ojbutton', 'ojs/ojlabelvalue','ojs/ojdialog', 'ojs/ojprogress-bar','ojs/ojselectsingle'],
function (ko, $, app,ArrayDataProvider) {

    function onepViewModel() {
        var self = this;

        self.uname = ko.observable();
        self.upasswd = ko.observable();
        self.role = ko.observable();
        self.AddUserMsg = ko.observable();
      
        self.isFormReadonly = ko.observable(false); 
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
        
        self.currentRole = ko.observable();
        var onepRoles = [{ label  : "Admin" , value : 'admin' },
                            {label: "Data Operator", value : "dataoper"},
                            {label: "Viewer", value : "viewer"},
                            {label: "Troubleshooter", value : "tshoot"}];
        self.OneRoleDP = new ArrayDataProvider(onepRoles, {keyAttributes: 'value'});


        self.addUser = function (data, event) {
            self.AddUserMsg('');
            document.querySelector('#addUserDialog').open();
            $.ajax({
                url: self.DepName() + "/onepconn",
                type: 'POST',
                data: JSON.stringify({
                    user: self.uname(),
                    passwd : self.upasswd(),
                    onep_role : self.currentRole()
                }),
                dataType: 'json',
                context: self,
                error: function (e) {
                    //console.log(e);
                },
                success: function (data) {
                    document.querySelector('#addUserDialog').close();
                    document.querySelector('#OnePDialog').open();
                    self.AddUserMsg(data[0]);
                    return self;
                }

            })
        }

        self.AddUserMsgOKClose = function (event) {
            document.querySelector('#OnePDialog').close();
        };


        //console.log(self);
        self.connected = function () { 
            if (sessionStorage.getItem("userName")==null) {
                oj.Router.rootInstance.go('signin');
            }
            else
            {
              app.onAppSuccess();
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
            // Implement if needed

        };
    }

    /*
     * Returns a constructor for the ViewModel so that the ViewModel is constructed
     * each time the view is displayed.  Return an instance of the ViewModel if
     * only one instance of the ViewModel is needed.
     */
    return  onepViewModel;
}
);
