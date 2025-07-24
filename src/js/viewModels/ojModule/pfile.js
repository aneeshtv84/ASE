
define(['knockout', 'jquery','appController' ,"ojs/ojarraydataprovider",'ojs/ojknockout-keyset', 'ojs/ojknockout', 'ojs/ojlistview', 'ojs/ojlistitemlayout', 'ojs/ojinputtext', 'ojs/ojlabel', 'ojs/ojformlayout','ojs/ojswitch', "ojs/ojinputsearch", 'ojs/ojjsontreedatasource', 'ojs/ojcollectiontabledatasource'],
function (ko, $, app,ArrayDataProvider, keySet) {

    class pfileViewModel {
        constructor(context){
        var self = this;
        self.DepName = context.DepName;
        self.paramFileList = ko.observableArray([]);
        self.paramFileList1 = ko.observableArray([]);
        self.value = ko.observable();

        function paramfile() {
            self.paramFileList([]);
            $.ajax({
                url: self.DepName() + "/listprm",
                type: 'GET',
                dataType: 'json',
                context: self,
                error: function (e) {
                    //console.log(e);
                },
                success: function (data) {
                   
                    var pfileChild = []; 

                    for(var i=0;i<data[0].length;i++){
                        pfileChild.push( {"attr": {"id": data[0][i],"name": data[0][i]
                    }

                    });
                    }


                    var pfile=[];

                    pfile.push({"attr": {"id": ""},
                    "children": pfileChild
                    });
                    
                    self.data(pfile);
                    // console.log(self.data)
                    self.contactDataSource = new oj.JsonTreeDataSource(pfile);
                    self.dataSource(self.contactDataSource);

                    for (var i = 0; i < data[0].length; i++) {

                        self.paramFileList.push({'Paramfile': data[0][i]});
                    }

                    // let search = "RM";
                    // for (var i = 0; i < data[0].length; i++) {
                    //     if(data[0][i].search(search)  != -1){
                    //         self.paramFileList1.push({value: data[0][i], label: data[0][i]});
                    //     }
                    // }

                    for (var i = 0; i < data[0].length; i++) {
                            self.paramFileList1.push({value: data[0][i], label: data[0][i]});
                    }
                   
                    
                    //console.log(self.paramFileList1());
                    return self;
                }

            })

        }

       
        self.suggestionsDP = new ArrayDataProvider(self.paramFileList1, {
            keyAttributes: "value",
        });
        self.paramfileDP = new ArrayDataProvider(self.paramFileList, {keyAttributes: 'Paramfile'});

        self.selectedItems = new keySet.ObservableKeySet(); // observable bound to selection option to monitor current selections
        self.selectedSelectionRequired = ko.observable(true);
        self.firstSelectedItem = ko.observable();
        self.selectedPrmFile = ko.observableArray([]);

        //start search
        function flattenJSON(data)
        {
            var collection = new oj.Collection();

            for (var i=0;i<data.length;i++)
            {
                var children = data[i].children;
                if (children != null && children.length > 0)
                {
                    for (var j=0;j<children.length;j++)
                    {
                        collection.add(children[j].attr);
                    }
                }
            }

            return collection;
        }
      
self.data = ko.observable();

self.filter = ko.observable('');
self.dataSource = ko.observable();

self.nameFilter = function(model, attr, value)
{
    var name = model.get("name");

    return (name.toLowerCase().indexOf(value.toLowerCase()) > -1);
};
self.handleRawValueChanged = function(event) 
{
    var filter = event.detail.value;
    if (filter.length == 0)
    {
        if (self.dataSource() == self.filteredDataSource)
            self.dataSource(self.contactDataSource);
    }
    else
    {
        if (self.filteredDataSource == undefined)
        {
            self.collection = flattenJSON(self.data());
            self.filteredCollection = self.collection.clone();
            self.filteredDataSource = new oj.CollectionTableDataSource(self.filteredCollection);
        }

        var ret = self.collection.where({name:{value:filter,comparator:self.nameFilter}});
        self.filteredCollection.reset(ret);

        if (self.dataSource() == self.contactDataSource)
            self.dataSource(self.filteredDataSource);
    }
   // self.viewPrm();
};

self.itemOnly = function(context)
{
    if (context['leaf']  == undefined)
    {
        return true;
    }
    return context['leaf'];
};

self.renderer = function(context)
{
    var leaf = context.leaf == undefined ? true : context.leaf;
    var renderer = oj.KnockoutTemplateUtils.getRenderer(leaf ? 'item_template' : 'group_template', true);
    return renderer.call(this, context);
};

        //end


        self.getDisplayValue = function (set) {
            var arr = [];
            set.values().forEach(function (key) {
                arr.push(key);
            });
            return JSON.stringify(arr);
        };




        self.prmFileContent = ko.observable();



        self.viewPrm = function (data, event) {
            self.prmFileContent('');
            $.ajax({
                url: self.DepName() + "/viewprm",
                type: 'POST',
                data: JSON.stringify({
                    prmFile: self.getDisplayValue(self.selectedItems())
                }),
                dataType: 'json',
                context: self,
                error: function (e) {
                    //console.log(e);
                },
                success: function (data) {
                    self.prmFileContent(data[0]);
                    return self;
                }

            })
        }

        self.viewPrmSearch = function (data, event) {
            //console.log("www")
            //console.log(self.value())
            self.prmFileContent('');
            $.ajax({
                url: self.DepName() + "/viewprm",
                type: 'POST',
                data: JSON.stringify({
                    prmFile: self.value()
                }),
                dataType: 'json',
                context: self,
                error: function (e) {
                    //console.log(e);
                },
                success: function (data) {
                    //console.log(data)
                    self.prmFileContent(data[0]);
                    return self;
                }

            })
        }

        self.textstateValue = ko.observable(true);
        self.edBtnstateValue = ko.observable();
        self.saveBtnStateValue = ko.observable(true);

        self.selectedButton = ko.observable();

        self.cancel = function () {
            var disabledState = self.textstateValue();
            self.textstateValue(true);
            self.edBtnstateValue(false);
            self.saveBtnStateValue(true);
            self.viewPrm();
        };


        self.editListener = function (event)
        {
            // toggle the componentDisable knockout binding
            var disabledState = self.textstateValue();
            self.textstateValue(!disabledState);
            self.edBtnstateValue(disabledState);
            self.saveBtnStateValue(!disabledState);

        }.bind(this);


        self.savePrmMsg = ko.observable();

        self.saveListener = function (data, event) {
            $.ajax({
                url: self.DepName() + "/saveprmtmp",
                type: 'POST',
                data: JSON.stringify({
                    prmFile: self.getDisplayValue(self.selectedItems()),
                    prmContent : self.prmFileContent()
                }),
                dataType: 'json',
                context: self,
                error: function (e) {
                    //console.log(e);
                },
                success: function (data) {
                    self.savePrmMsg(data[0]);
                    document.querySelector('#savePrmDialog').open();
                    return self;
                }

            })
        }

        self.savePrmOKClose = function (event) {
            document.querySelector('#savePrmDialog').close();
                   var disabledState = self.textstateValue();
            self.textstateValue(!disabledState);
            self.edBtnstateValue(disabledState);
            self.saveBtnStateValue(!disabledState);
        };

        //console.log(self);
        self.connected = function () { 
            app.onAppSuccess();
            // Implement if needed
            self.paramFileList([]);
            paramfile();

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

}
    /*
     * Returns a constructor for the ViewModel so that the ViewModel is constructed
     * each time the view is displayed.  Return an instance of the ViewModel if
     * only one instance of the ViewModel is needed.
     */
    return  pfileViewModel;
}
);
