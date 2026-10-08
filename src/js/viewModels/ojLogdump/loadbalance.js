define([
  "knockout",
  "jquery",
  "appController",
  "ojs/ojconverter-number",
  "ojs/ojarraydataprovider",
  "ojs/ojknockout-keyset",
  "ojs/ojknockout",
  "ojs/ojfilepicker",
  "ojs/ojinputtext",
  "ojs/ojtable",
  "ojs/ojradioset",
  "ojs/ojlabel",
  "ojs/ojlistview",
  "ojs/ojlistitemlayout",
  "ojs/ojcheckboxset",
  "ojs/ojformlayout",
  "ojs/ojdialog",
  "ojs/ojprogress-bar",
  "ojs/ojchart",
], function (ko, $, app, ojconverter_number_1, ArrayDataProvider, keySet) {
  class LoadBalanceViewModel {
    constructor(context) {
      var self = this;
      self.DepName = context.DepName;
      self.trailfile = ko.observable();
      self.OSPlat = ko.observable();
      self.NodeName = ko.observable();
      self.OSKern = ko.observable();
      self.DBName = ko.observable();
      self.DBVer = ko.observable();
      self.DBClientVer = ko.observable();
      self.ExtName = ko.observable();
      self.GGVer = ko.observable();
      self.FirstCSN = ko.observable();
      self.LastCSN = ko.observable();
      self.LogBSN = ko.observable();
      self.TrailCount = ko.observableArray([]);
      self.TranDet = ko.observable();
      self.RBA = ko.observable();
      self.TrailDet1 = ko.observableArray([]);
      self.TrailDet2 = ko.observableArray([]);

      self.trailFiles = ko.observableArray([]);
      self.ProcessName = ko.observableArray([]);
      self.processVal = ko.observableArray([]);
      self.CancelBehaviorOpt = ko.observable("icon");

      self.gettraildet = ko.observable(true);

      self.loadtrail = ko.computed({
        read: function () {
          if (self.processVal().length > 0) {
            return false;
          } else {
            self.processVal([]);
            return true;
          }
        },
      });

      function getProcessNames() {
        self.ProcessName([]);
        $.ajax({
          url: self.DepName() + "/api/v2/cdcGetProcess",
          type: "GET",
          dataType: "json",
          contentType: "application/json",
          context: self,
          progressMessage: "Fetching process list",
          error: function (xhr, textStatus, errorThrown) {
            app.showGlobalError(
              app.extractErrorMessage(xhr),
              "Process List Error",
            );
          },
          success: function (data) {
            for (var i = 0; i < data[0].length; i++) {
              self.ProcessName.push({
                label: data[0][i].id,
                value: data[0][i].category,
              });
            }
            self.ProcessName.valueHasMutated();
            return self;
          },
        });
      }

      self.getTrailFiles = function (data, event) {
        self.trailFiles([]);
        $.ajax({
          url: self.DepName() + "/api/v2/cdcGetAllTrails",
          data: JSON.stringify({
            trailname: self.processVal(),
          }),
          type: "POST",
          dataType: "json",
          contentType: "application/json",
          context: self,
          progressMessage: "Fetching trail files",
          error: function (xhr, textStatus, errorThrown) {
            app.showGlobalError(
              app.extractErrorMessage(xhr),
              "Trail File Error",
            );
          },
          success: function (data) {
            for (var i = 0; i < data[0].length; i++) {
              self.trailFiles.push({
                trail: data[0][i].file,
                size: data[0][i].size,
                mtime: data[0][i].mtime,
              });
            }
            self.trailFiles.valueHasMutated();
            return self;
          },
        });
      };

      self.trailfileDP = new ArrayDataProvider(self.trailFiles, {
        idAttribute: "trail",
      });
      self.processDP = new ArrayDataProvider(self.ProcessName, {
        keyAttributes: "value",
      });

      self.selectedItems = new keySet.ObservableKeySet(); // observable bound to selection option to monitor current selections
      self.selectedSelectionRequired = ko.observable(true);
      self.firstSelectedItem = ko.observable();
      self.selectedTrailFile = ko.observableArray([]);

      self.handleSelectedChanged = function (event) {
        self.gettraildet(false);
        self.selectedTrailFile(self.getDisplayValue(event.detail.value)); // show selected list item elements' ids
      };

      self.clickGetDet = function (data, event) {
        self.TrailCount([]);
        $.ajax({
          url: self.DepName() + "/api/v2/cdcDataDumpCount",
          data: JSON.stringify({
            trailfile: self.getDisplayValue(self.selectedItems()),
          }),
          type: "POST",
          dataType: "json",
          contentType: "application/json",
          context: self,
          progressMessage: "Fetching trail data details",
          error: function (xhr, textStatus, errorThrown) {
            app.showGlobalError(
              app.extractErrorMessage(xhr),
              "Trail Data Error",
            );
          },
          success: function (data) {
            let i = 0;
            for (var key in data[0]) {
              self.TrailCount.push({
                id: i,
                tabname: key,
                trancount: parseInt(data[0][key]),
                group: "Table",
              });
              i = i + 1;
            }
            self.TrailCount.valueHasMutated();
            self.TranDet(data[12]);
            self.RBA(data[13]);
            return self;
          },
        });
      };

      self.CountDataProvider = new ArrayDataProvider(self.TrailCount, {
        idAttribute: "id",
      });

      self.CountDetailcolumnArray = [
        { headerText: "Table Name", field: "tabname" },
        { headerText: "Count  ", field: "trancount" },
      ];

      self.connected = function () {
        getProcessNames();
      };
    }
    getDisplayValue(set) {
      let text;
      const arr = [];
      set.values().forEach((key) => {
        arr.push(key);
      });
      return arr;
    }
  }

  /*
   * Returns an instance of the ViewModel providing one instance of the ViewModel. If needed,
   * return a constructor for the ViewModel so that the ViewModel is constructed
   * each time the view is displayed.
   */
  return LoadBalanceViewModel;
});
