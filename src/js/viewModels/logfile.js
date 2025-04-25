define(['knockout','ojs/ojmoduleanimations','ojs/ojmodule-element-utils', 'ojs/ojmodule-element', 'ojs/ojbutton', 'ojs/ojinputtext'],
        function ( ko,ModuleAnimations,moduleUtils) {

            class LogFileViewModel {
              constructor(context){

 function resolveVVM(name, moduleConfig) {
        var viewPath = name !== 'oj:blank' ? 'views/ojLogView/' + name + '.html' : null;
        var modelPath = name !== 'oj:blank' ? 'viewModels/ojLogView/' + name : null;
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

      self.router = context.parentRouter;

      //console.log(context)
      self.connected = function () { 
        if (sessionStorage.getItem("userName")==null) {
            self.router.go({path : 'signin'});
        }
        else {
          self.currentModule = ko.observable("reportfs");
          if (context.params.module){
            self.currentModule(context.params.module)
          }
          self.moduleConfig = ko.observable({'view':[],'viewModel':null});
          resolveVVM(self.currentModule(), self.moduleConfig);
          self.currentModule.subscribe(function(name) {
            resolveVVM(name, self.moduleConfig);
          });
        }
      }



                self.disconnected = function () {
                    // Implement if needed
                };

                self.transitionCompleted = function () {
                    // Implement if needed
                };

                self.currentAnimation = "fade";
                self.moduleAnimation = ko.pureComputed(() => {
                  if (self.currentModule()) {
                      return ModuleAnimations[self.currentAnimation];
                  }
                  return null;
              });

            }
          }
            return  LogFileViewModel;

        });
