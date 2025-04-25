define(['knockout', 'ojs/ojmodule-element-utils', 'ojs/ojmodule-element', 'ojs/ojbutton', 'ojs/ojmoduleanimations','ojs/ojinputtext'],
        function (ko, moduleUtils) {

            class TShootViewModel {
              constructor(context){

 function resolveVVM(name, moduleConfig) {
        var viewPath = name !== 'oj:blank' ? 'views/ojTShoot/' + name + '.html' : null;
        var modelPath = name !== 'oj:blank' ? 'viewModels/ojTShoot/' + name : null;
        var masterPromise = Promise.all([
          moduleUtils.createView({'viewPath':viewPath}),
          moduleUtils.createViewModel({'viewModelPath':modelPath,params: { DepName : context.routerState.detail.dep_url}})
        ]);
        masterPromise.then(
          function(values){
            moduleConfig({'view':values[0],'viewModel':values[1]});
          },
          function(reason){}
        );
      };
      
      var self = this;
      self.currentModule = ko.observable("ie");
      self.moduleConfig = ko.observable({'view':[],'viewModel':null});
      
      resolveVVM(self.currentModule(), self.moduleConfig);
      self.currentModule.subscribe(function(name) {
        resolveVVM(name, self.moduleConfig);
      });
    
                

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
            return  TShootViewModel;

        });
