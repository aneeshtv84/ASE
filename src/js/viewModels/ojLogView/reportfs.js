define(['ojs/ojcore', 'knockout', 'jquery','appController', 'ojs/ojknockout-keyset','ojs/ojarraydataprovider', 'ojs/ojknockout', 'ojs/ojlistview', 'ojs/ojlistitemlayout', 'ojs/ojinputtext', 'ojs/ojlabel', 'ojs/ojformlayout','ojs/ojswitch', "ojs/ojinputsearch", 'ojs/ojjsontreedatasource', 'ojs/ojcollectiontabledatasource'],
function (oj, ko, $, app, keySet , ArrayDataProvider) {

    class reportfsViewModel {
        constructor(context){
            var self = this;
            self.DepName = context.DepName;
        self.rptFileList = ko.observableArray([]);

        function rptfile() {
            self.rptFileList([]);
            $.ajax({
                url: self.DepName() + "/listrpt",
                type: 'GET',
                dataType: 'json',
                context: self,
                error: function (e) {
                    //console.log(e);
                },
                success: function (data) {
                    for (var i = 0; i < data[0].length; i++) {
                        self.rptFileList.push({'rptfile': data[0][i]});
                    }
                     var rpfileChild = []; 

                    for(var i=0;i<data[0].length;i++){
                        rpfileChild.push( {"attr": {"id": data[0][i],"name": data[0][i]
                    }

                    });
                    }


                    var rpfile=[];

                    rpfile.push({"attr": {"id": ""},
                    "children": rpfileChild
                    });
                    
                    self.data(rpfile);
                    self.contactDataSource = new oj.JsonTreeDataSource(rpfile);
                    self.dataSource(self.contactDataSource);
                    //console.log(self);
                    return self;
                }
            })
        };

        self.rptfileDP = new ArrayDataProvider(self.rptFileList, {keyAttributes: 'rptfile'});

        self.selectedItems = new keySet.ObservableKeySet(); // observable bound to selection option to monitor current selections
        self.selectedSelectionRequired = ko.observable(true);
        self.firstSelectedItem = ko.observable();
        self.selectedPrmFile = ko.observableArray([]);

        self.getDisplayValue = function (set) {
            var arr = [];
            set.values().forEach(function (key) {
                arr.push(key);
            });
            return JSON.stringify(arr);
        };




        self.rptFileContent = ko.observable();



        self.viewRpt = function (data, event) {
            self.rptFileContent('');
            $.ajax({
                url: self.DepName() + "/viewrpt",
                type: 'POST',
                data: JSON.stringify({
                    rptFile: self.getDisplayValue(self.selectedItems())
                }),
                dataType: 'json',
                context: self,
                error: function (e) {
                    //console.log(e);
                },
                success: function (data) {
                    self.rptFileContent(data[0]);
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

        self.cancel = function () {
            oj.Router.rootInstance.go('incidents');

        }


        self.connected = function () { 
            app.onAppSuccess();
            // Implement if needed
            self.rptFileList([]);
            rptfile();

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
    return  reportfsViewModel;
}
);
