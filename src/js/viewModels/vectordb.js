define(['knockout','ojs/ojmoduleanimations','ojs/ojmodule-element-utils', 'ojs/ojmodule-element', 'ojs/ojbutton', 'ojs/ojinputtext'],
function ( ko,ModuleAnimations,moduleUtils) {
    class AdminViewModel {
        constructor(context){
            
            function resolveVVM(name, moduleConfig) {
                var viewPath = name !== 'oj:blank' ? 'views/ojVector/' + name + '.html' : null;
                var modelPath = name !== 'oj:blank' ? 'viewModels/ojVector/' + name : null;
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
                    
            self.onepDepType = ko.observable();

            self.router = context.parentRouter;

            //console.log(context)
            self.connected = function () { 
                self.onepDepType(sessionStorage.getItem("Dep_Type"));
                if (sessionStorage.getItem("userName")==null) {
                    self.router.go({path : 'signin'});
                }
                else {
                    if (self.onepDepType() == 'sybase') {
                        self.currentModule = ko.observable("documentEdit");
                    }
                    else if (self.onepDepType() == 'bda') {
                        self.currentModule = ko.observable("rmtInstall_BDA");
                    }
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

            self.disconnected = function () {// Implement if needed
            };

            self.transitionCompleted = function () {// Implement if needed
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
    
    return  AdminViewModel;

});
