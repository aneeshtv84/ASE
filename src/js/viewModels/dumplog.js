define(['knockout','ojs/ojmoduleanimations','ojs/ojmodule-element-utils', 'ojs/ojmodule-element', 'ojs/ojbutton','ojs/ojinputtext'],
        function ( ko,ModuleAnimations,moduleUtils) {

          class DumpLogViewModel {
                constructor(context){

 function resolveVVM(name, moduleConfig) {
        var viewPath = name !== 'oj:blank' ? 'views/ojLogdump/' + name + '.html' : null;
        var modelPath = name !== 'oj:blank' ? 'viewModels/ojLogdump/' + name : null;
        var masterPromise = Promise.all([
          moduleUtils.createView({'viewPath':viewPath}),
          moduleUtils.createViewModel({'viewModelPath':modelPath,params: { DepName : context.routerState.detail.dep_url }})
        ]);
        masterPromise.then(
          function(values){
            moduleConfig({'view':values[0],'viewModel':values[1]});
          },
          function(reason){}
        );
      };
      
      var self = this;
      self.DepName = context.routerState.detail.dep_url;
      self.currentModule = ko.observable("logdump");
      self.moduleConfig = ko.observable({'view':[],'viewModel':null});
      
      resolveVVM(self.currentModule(), self.moduleConfig);
      self.currentModule.subscribe(function(name) {
        resolveVVM(name, self.moduleConfig);
      });
    
                self.disconnected = function () {
                    // Implement if needed
                };

                self.transitionCompleted = function () {
                    // Implement if needed
                };
                self.currentAnimation = "coverUp";
                self.moduleAnimation = ko.pureComputed(() => {
                  if (self.currentModule()) {
                      return ModuleAnimations[self.currentAnimation];
                  }
                  return null;
              });

            }
          }
            return  DumpLogViewModel;

        });
