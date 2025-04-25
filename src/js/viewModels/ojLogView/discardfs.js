define(['ojs/ojcore', 'knockout', 'jquery','appController', 'ojs/ojknockout-keyset','ojs/ojarraydataprovider', 'ojs/ojknockout', 'ojs/ojlistview', 'ojs/ojlistitemlayout', 'ojs/ojinputtext', 'ojs/ojlabel', 'ojs/ojformlayout','ojs/ojswitch', "ojs/ojinputsearch", 'ojs/ojjsontreedatasource', 'ojs/ojcollectiontabledatasource'],
function (oj, ko, $, app, keySet , ArrayDataProvider) {

    class discardfsViewModel {
        constructor(context){
            var self = this;
            self.DepName = context.DepName;
        self.dscFileList = ko.observableArray([]);

        function dscfile() {
            self.dscFileList([]);
            $.ajax({
                url: self.DepName() + "/listdsc",
                type: 'GET',
                dataType: 'json',
                context: self,
                error: function (e) {
                    //console.log(e);
                },
                success: function (data) {

                    var dfileChild = []; 
                    for(var i=0;i<data[0].length;i++){
                        dfileChild.push( {"attr": {"id": data[0][i],"name": data[0][i]
                    }

                    });
                    }

                    var dfile=[];

                    dfile.push({"attr": {"id": ""},
                    "children": dfileChild
                    });
                    
                    self.data(dfile);
                    self.contactDataSource = new oj.JsonTreeDataSource(dfile);
                    self.dataSource(self.contactDataSource);

                    for (var i = 0; i < data[0].length; i++) {
                        self.dscFileList.push({'dscfile': data[0][i]});
                    }
                    //console.log(self);
                    return self;
                }
            })
        };

        self.dscfileDP = new ArrayDataProvider(self.dscFileList, {keyAttributes: 'dscfile'});

        self.selectedItems = new keySet.ObservableKeySet(); // observable bound to selection option to monitor current selections
        self.selectedSelectionRequired = ko.observable(true);
        self.firstSelectedItem = ko.observable();
        self.selectedDscFile = ko.observableArray([]);

        self.getDisplayValue = function (set) {
            var arr = [];
            set.values().forEach(function (key) {
                arr.push(key);
            });
            return JSON.stringify(arr);
        };




        self.dscFileContent = ko.observable();



        self.viewDsc = function (data, event) {
            self.dscFileContent('');
            $.ajax({
                url: self.DepName() + "/viewdsc",
                type: 'POST',
                data: JSON.stringify({
                    dscFile: self.getDisplayValue(self.selectedItems())
                }),
                dataType: 'json',
                context: self,
                error: function (e) {
                    //console.log(e);
                },
                success: function (data) {
                    self.dscFileContent(data[0]);
                    return self;
                }

            })
        }

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
        self.connected = function () { 
            if (sessionStorage.getItem("userName")==null) {
                oj.Router.rootInstance.go('signin');
            }
            else
            {
              app.onAppSuccess();
              self.dscFileList([]);
              dscfile();
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
    }
    /*
     * Returns a constructor for the ViewModel so that the ViewModel is constructed
     * each time the view is displayed.  Return an instance of the ViewModel if
     * only one instance of the ViewModel is needed.
     */
    return  discardfsViewModel;
}
);
