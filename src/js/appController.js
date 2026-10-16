define([ 'ojs/ojoffcanvas' , 'knockout', 'ojs/ojmodule-element-utils', 'ojs/ojresponsiveutils', 'ojs/ojresponsiveknockoututils', 
         'ojs/ojcorerouter', 'ojs/ojmodulerouter-adapter', 'ojs/ojknockoutrouteradapter', 'ojs/ojurlparamadapter', 
         'ojs/ojarraydataprovider', "ojs/ojarraytreedataprovider", 'ojs/ojknockouttemplateutils', 'ojs/ojmodule-element','ojs/ojmodule-element-utils','ojs/ojknockout' ,'ojs/ojbutton',
         'ojs/ojdialog','ojs/ojselectsingle'],
  function( OffcanvasUtils , ko , moduleUtils, ResponsiveUtils, ResponsiveKnockoutUtils, CoreRouter, ModuleRouterAdapter,
    KnockoutRouterAdapter, UrlParamAdapter, ArrayDataProvider, ArrayTreeDataProvider, KnockoutTemplateUtils  ) {
     function ControllerViewModel() {
        var self = this;
        self.sessionExpiredShown = ko.observable(false);
        self.globalErrorMessage = ko.observable("");
        self.globalErrorTitle = ko.observable("Error");

        self.globalBusy = ko.observable(false);
        self.globalProgressMessage = ko.observable("Loading..."); 
        self.activeRequestCount = 0;

        $.ajaxSetup({
          timeout: 30000,
          beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("Content-Type", "application/json");
            var hasCustomAuth = settings.headers && settings.headers.Authorization;
            if (settings.url.indexOf('/api/v2/onep/login') === -1 && !hasCustomAuth) {
                var token = sessionStorage.getItem('AccessToken');
                if (token) {
                    xhr.setRequestHeader('Authorization', 'Bearer ' + token);
                }
            }
          }
        });

        self.showGlobalError =(message, title) => {
          self.globalErrorMessage(message);
          self.globalErrorTitle(title || "Error");
          document.querySelector('#GlobalErrorDialog').open();
        }

        $(document).ajaxSend(function (event, xhr, settings) {
          if (settings.showProgress === false) return;
          self.activeRequestCount++;
          self.globalProgressMessage(settings.progressMessage || "Loading...");
          if (self.activeRequestCount === 1) {
            self.globalBusy(true);
            var dlg = document.querySelector('#GlobalProgressDialog');
            if (dlg) dlg.open();
          }
        });

        $(document).ajaxComplete(function (event, xhr, settings) {
          if (settings.showProgress === false) {
            return;
          }
          self.activeRequestCount = Math.max(0, self.activeRequestCount - 1);
          if (self.activeRequestCount === 0) {
            self.globalBusy(false);
            var dlg = document.querySelector('#GlobalProgressDialog');
            if (dlg) dlg.close();
          }
        });

        function callWhenReady(selector, method) {
          var el = document.querySelector(selector);
          if (!el) return;

          if (typeof el[method] === 'function' && el.matches(':defined')) {
            el[method]();
            return;
          }

          customElements.whenDefined(el.localName).then(function () {
            requestAnimationFrame(function () {
              var target = document.querySelector(selector);
              if (target && typeof target[method] === 'function') {
                target[method]();
              }
            });
          });
        }
        self.callWhenReady = callWhenReady;  // NEW — expose it

        self.handleSessionExpired = function() {
          if (self.sessionExpiredShown()) return;
          self.sessionExpiredShown(true);
          sessionStorage.clear();
          localStorage.removeItem('login');
          document.querySelector('#SessionExpiredDialog').open();
        };

        $(document).ajaxError(function (event, xhr, settings, thrownError) { 
          
          if (xhr.status === 401 && !settings.isTargetCall && !self.sessionExpiredShown()) {
            self.handleSessionExpired();
            return;
          }
                   
          if (settings.suppressGlobalError || settings.isTargetCall) {
            return;  
          }
          
          

          if (xhr.statusText === 'timeout' || (xhr.status === 0 && thrownError === undefined && settings.timeout)) {
            self.showGlobalError("Request timed out. Please try again.", "Request Timeout");
            return;
          }

          if (xhr.status === 0) {
            self.showGlobalError(self.deploymentUnreachableMessage(), "Connection Error");
            return;
          }

          self.showGlobalError(self.extractErrorMessage(xhr), "Error");
        });

        self.deploymentUnreachableMessage = (depName) => {
          var name = depName || self.onepDepName() || 'the deployment';
          return `Could not reach MigDB Agent. Please check the MigDB Agent is UP and Running.`;
        };

        self.extractErrorMessage = (xhr)=> {
          var fallback = "Something went wrong. Please try again.";

          if (!xhr) return fallback;

          try {
            var body = xhr.responseJSON || JSON.parse(xhr.responseText);

            if (typeof body.detail === 'string') {
              return body.detail;
            }

            if (Array.isArray(body.detail)) {
              return body.detail.map(function (e) {
                return (e.loc ? e.loc.join('.') + ': ' : '') + e.msg;
              }).join('; ');
            }

            if (body.detail && body.raw_body) {
              return Array.isArray(body.detail)
                ? body.detail.map(function (e) { return e.msg; }).join('; ')
                : String(body.detail);
            }
          } catch (e) {
            // response wasn't JSON at all
          }

          return fallback;
        }

        self.depCtxCache = {};

        self.depTokenKey = function (depName) {
          return "Tgt_" + depName + "_AccessToken";
        };

        self.resolveDep = function (depName, callback) {
          var cached = self.depCtxCache[depName];
          if (cached) { callback(cached); return; }

          $.ajax({
            url: sessionStorage.getItem("Dep_Url") + "/api/v2/onep/depurl",
            type: "POST",
            data: JSON.stringify({ dep: depName }),
            dataType: "json",
            contentType: "application/json",
            showProgress: false,
            suppressGlobalError: true,
            error: function (xhr) {
              if (xhr.status === 401) { self.handleSessionExpired(); return; }
              callback(null, self.extractErrorMessage(xhr));
            },
            success: function (data) {
              var key = self.depTokenKey(depName);
              if (data[3]) sessionStorage.setItem(key, data[3]);
              else sessionStorage.removeItem(key);
              var ctx = {
                dep: depName,
                url: data[0],
                dbtype: (data[2] || "").toLowerCase(),
                remote: !!data[3],
              };
              self.depCtxCache[depName] = ctx;
              callback(ctx);
            },
          });
        };

        self.refreshDepToken = function (depName, callback) {
          $.ajax({
            url: sessionStorage.getItem("Dep_Url") + "/api/v2/onep/deptoken",
            type: "POST",
            data: JSON.stringify({ dep: depName, force: true }),
            dataType: "json",
            contentType: "application/json",
            showProgress: false,
            suppressGlobalError: true,
            error: function (xhr) {
              if (xhr.status === 401 && !xhr.responseJSON) { self.handleSessionExpired(); return; }
              callback(false, self.extractErrorMessage(xhr));
            },
            success: function (data) {
              sessionStorage.setItem(self.depTokenKey(depName), data.access_token);
              callback(true);
            },
          });
        };

        var DB_LABEL = { sqlserver: "SQL Server", mongodb: "MongoDB", postgresql: "PostgreSQL",
                         oracle: "Oracle", sybase: "Sybase" };

        self.depAjax = function (depName, ajaxOpts) {
          var originalError = ajaxOpts.error;
          var retried = false;

          function send() {
            var token = sessionStorage.getItem(self.depTokenKey(depName));
            ajaxOpts.headers = token ? { Authorization: "Bearer " + token } : undefined;
            ajaxOpts.isTargetCall = !!token;      // local deployment -> normal source handling
            ajaxOpts.suppressGlobalError = true;
            $.ajax(ajaxOpts);
          }

          ajaxOpts.error = function (xhr, textStatus, errorThrown) {
            var isRemote = !!sessionStorage.getItem(self.depTokenKey(depName));

            if (textStatus !== "abort" && isRemote && xhr.status === 401 && !retried) {
              retried = true;
              self.refreshDepToken(depName, function (ok, msg) {
                if (ok) { send(); return; }
                self.showGlobalError(`Login to deployment "${depName}" failed. ${msg || ""}`,
                                     "Target Auth Error");
              });
              return;
            }
            if (isRemote && xhr.status === 401) {
              self.showGlobalError(`Not authorized on deployment "${depName}".`, "Target Auth Error");
              return;
            }
            if (xhr.status === 503) {
              var ctx = self.depCtxCache[depName] || {};
              var label = DB_LABEL[ctx.dbtype] || "MigDB";
              self.showGlobalError(
                `${label} Service Manager is not started on deployment "${depName}". ` +
                `Please start the Service Manager and try again.`,
                "Service Manager Not Started");
              return;
            }
            if (originalError) originalError(xhr, textStatus, errorThrown);
          };

          send();
        };

        self.sessionExpiredOkClose = function () {
          document.querySelector('#SessionExpiredDialog').close();
          self.goToSignIn();
        };

        self.globalErrorOkClose = function () {
          document.querySelector('#GlobalErrorDialog').close();
          document.body.classList.remove('oj-dialog-open');
        };

      self.KnockoutTemplateUtils = KnockoutTemplateUtils;
      self.onepDeployList = ko.observableArray([]);
      self.DepName = ko.observable();
      self.onepDepName = ko.observable();
      self.onepDepUrl = ko.observable();
      self.CancelBehaviorOpt = ko.observable('icon');
      self.footerLinks = ko.observableArray([]);
      self.onepDepType = ko.observable();
        
        self.drawer = {
          displayMode: 'push',
          selector: '#drawer',
          content: '#main'
        };
  

        self.toggleDrawer = function () {
          return OffcanvasUtils.toggle(self.drawer);
        };
      
        self.username = ko.observable();
        // Handle announcements sent when pages change, for Accessibility.
        self.manner = ko.observable('polite');
        self.message = ko.observable();
        document.getElementById('globalBody').addEventListener('announce', announcementHandler, false);

        function announcementHandler(event) {
          setTimeout(function() {
            self.message(event.detail.message);
            self.manner(event.detail.manner);
          }, 200);
        };

      // Media queries for repsonsive layouts
      var smQuery = ResponsiveUtils.getFrameworkQuery(ResponsiveUtils.FRAMEWORK_QUERY_KEY.SM_ONLY);
      self.smScreen = ResponsiveKnockoutUtils.createMediaQueryObservable(smQuery);

      self.count = ko.observable(3);
      // Navigation setup
      var navData = [
       { path:"" ,redirect : 'signin'},
       { path: 'signin', detail : {label: 'SignIn',iconClass: 'oj-navigationlist-item-icon demo-icon-font-24 demo-chart-icon-24',dep_url : self.onepDepUrl } },
       { path: 'processMon', detail : {label: 'processMon',iconClass: 'oj-navigationlist-item-icon demo-icon-font-24 demo-chart-icon-24',dep_url : self.onepDepUrl} },
       { path: 'dashboard', detail : {label: 'Dashboard',iconClass: 'fa fa-tachometer oj-navigationlist-item-icon',dep_url : self.onepDepUrl}},
       { path: 'dataflow', detail : {label: 'Dataflow',iconClass: 'oj-navigationlist-item-icon fa fa-random',dep_url : self.onepDepUrl} },
       { path: 'manage', detail : {label: 'Manage',iconClass: 'oj-navigationlist-item-icon fa fa-wrench',dep_url : self.onepDepUrl} },
       { path: 'monitor', detail : {label: 'Monitor',iconClass: 'oj-navigationlist-item-icon fa fa-area-chart',dep_url : self.onepDepUrl} },
       { path: 'Designer', detail : {label: 'Designer',iconClass: 'oj-navigationlist-item-icon fas fa-paint-brush',dep_url : self.onepDepUrl} },
       { path: 'initial', detail : {label: 'Hetrogeneous Initial Load',iconClass: 'oj-navigationlist-item-icon fa fa-cloud-upload',dep_url : self.onepDepUrl} },
       { path: 'initmon', detail : {label: 'Hetro Initial Load Monitor',iconClass: 'oj-navigationlist-item-icon fas fa-sync-alt',dep_url : self.onepDepUrl} }, 
       { path: 'expdp', detail : {label: 'Homogeneous Initial Load',iconClass: 'oj-navigationlist-item-icon fa fa-cloud-upload',dep_url : self.onepDepUrl} },
       { path: 'expinitmon', detail : {label: 'Homo Initial Load Monitor',iconClass: 'oj-navigationlist-item-icon fas fa-sync-alt',dep_url : self.onepDepUrl} }, 
       { path: 'cdr', detail : {label: 'Conflict Resolution',iconClass: 'oj-navigationlist-item-icon fas fa-sync-alt',dep_url : self.onepDepUrl} }, 
       { path: 'migrate', detail : {label: 'Analyze Objects',iconClass: 'oj-navigationlist-item-icon demo-icon-font-24 demo-chart-icon-24 font15',dep_url : self.onepDepUrl} }, 
       { path: 'dumplog', detail : {label: 'Analyze Trails',iconClass: 'oj-navigationlist-item-icon demo-icon-font-24 demo-chart-icon-24 font15',dep_url : self.onepDepUrl} }, 
       { path: 'ggadmin', detail : {label: 'Setup',iconClass: 'oj-navigationlist-item-icon fa fa-cogs',dep_url : self.onepDepUrl} }, 
       { path: 'agent', detail : {label: 'Agent',iconClass: 'oj-navigationlist-item-icon fa fa-file-code-o',dep_url : self.onepDepUrl} },
       { path: 'comparePadMonitor', detail : {label: 'Compare Pad Monitor',iconClass: 'oj-navigationlist-item-icon fa fa-file-code-o',dep_url : self.onepDepUrl} },
       { path: 'tshoot', detail : {label: 'Troubleshoot',iconClass: 'oj-navigationlist-item-icon fa-solid fa-code-compare',dep_url : self.onepDepUrl} }, 
       { path: 'logfile', detail : {label: 'LogFile',iconClass: 'oj-navigationlist-item-icon fas fa-file-alt',dep_url : self.onepDepUrl} },
       { path: 'DBAssessment', detail : {label: 'Migration Assessment',iconClass: 'oj-navigationlist-item-icon fas fa-file-alt',dep_url : self.onepDepUrl} },
       { path: 'DBAssessMon', detail : {label: 'Migration Assessment Monitor',iconClass: 'oj-navigationlist-item-icon fas fa-file-alt',dep_url : self.onepDepUrl} }
      ];

      var navMenu = [
        // { name: "processMon", id: "processMon", icons: "oj-navigationlist-item-icon demo-icon-font-24 demo-chart-icon-24", path: "processMon", dep_url: self.onepDepUrl },

        { name: "Dashboard", id: "dashboard", icons: "fa fa-tachometer oj-navigationlist-item-icon", path: "dashboard", dep_url: self.onepDepUrl },
        { name: "Dataflow", id: "dataflow", icons: "oj-navigationlist-item-icon fa fa-random", path: "dataflow", dep_url: self.onepDepUrl },
        { name: "Manage", id: "manage", icons: "oj-navigationlist-item-icon fa fa-wrench", path: "manage", dep_url: self.onepDepUrl },
        { name: "Monitor", id: "monitor", icons: "oj-navigationlist-item-icon fa fa-area-chart", path: "monitor", dep_url: self.onepDepUrl },
        { name: "Designer", id: "Designer", icons: "oj-navigationlist-item-icon fas fa-paint-brush", path: "Designer", dep_url: self.onepDepUrl },

        { name: "Hetrogeneous Initial Load", id: "initial", icons: "oj-navigationlist-item-icon fa fa-cloud-upload", path: "initial", dep_url: self.onepDepUrl },
        { name: "Hetro Initial Load Monitor", id: "initmon", icons: "oj-navigationlist-item-icon fas fa-sync-alt", path: "initmon", dep_url: self.onepDepUrl },
        { name: "Homogeneous Initial Load", id: "expdp", icons: "oj-navigationlist-item-icon fa fa-cloud-upload", path: "expdp", dep_url: self.onepDepUrl },
        { name: "Homo Initial Load Monitor", id: "expinitmon", icons: "oj-navigationlist-item-icon fas fa-sync-alt", path: "expinitmon", dep_url: self.onepDepUrl },
        // { name: "Conflict Resolution", id: "cdr", icons: "oj-navigationlist-item-icon fas fa-sync-alt", path: "cdr", dep_url: self.onepDepUrl },

        // { name: "Analyze Objects", id: "migrate", icons: "oj-navigationlist-item-icon demo-icon-font-24 demo-chart-icon-24 font15", path: "migrate", dep_url: self.onepDepUrl },
        { name: "Analyze Trails", id: "dumplog", icons: "oj-navigationlist-item-icon demo-icon-font-24 demo-chart-icon-24 font15", path: "dumplog", dep_url: self.onepDepUrl },

        { name: "Setup", id: "ggadmin", icons: "oj-navigationlist-item-icon fa fa-cogs", path: "ggadmin", dep_url: self.onepDepUrl },
        { name: "Troubleshoot", id: "tshoot", icons: "oj-navigationlist-item-icon fa fa-search", path: "tshoot", dep_url: self.onepDepUrl },
        { name: "LogFile", id: "logfile", icons: "oj-navigationlist-item-icon fas fa-file-alt", path: "logfile", dep_url: self.onepDepUrl },

        // { name: "Assessment", id: "Assessment", icons: "oj-navigationlist-item-icon fa-solid fa-code-compare",
        //   children: [
        //     { name: "Create Job", id: "DBAssessment", icons: "fa-solid fa-landmark", path: "DBAssessment", dep_url: self.onepDepUrl },
        //     { name: "Monitor Job", id: "DBAssessMon", icons: "fa-solid fa-landmark", path: "DBAssessMon", dep_url: self.onepDepUrl }
        //   ]
        // },        
        // { name: "Compare Pad", id: "comparePad", icons: "oj-navigationlist-item-icon fa-solid fa-code-compare",
        //   children: [
        //     { name: "Configure", id: "agent", icons: "fa-solid fa-landmark", path: "agent", dep_url: self.onepDepUrl },
        //     { name: "Monitor", id: "comparePadMonitor", icons: "fa-solid fa-landmark", path: "comparePadMonitor", dep_url: self.onepDepUrl }
        //   ]
        // }
      ];

      
      // Router setup
      self.menuDataProvider = new ArrayTreeDataProvider(navMenu, {
        keyAttributes: 'id'
      });
      let router = new CoreRouter(navData, {
        urlAdapter: new UrlParamAdapter()
      });
      router.sync();

      window.appRouter = router;
     

      self.selectedItem = ko.observable('ggadmin');
      self.goToPage = (e)=>{
        if(e.currentTarget.id!=""){
          router.go({path : e.currentTarget.id});
        }
      }

      self.moduleAdapter = new ModuleRouterAdapter(router);

      self.selection = new KnockoutRouterAdapter(router);

      self.navDataProvider = new ArrayDataProvider(navData.slice(3), {keyAttributes: "path"});

      // Header
      // Application Name used in Branding Area
      self.appName = ko.observable();


// User Info used in Global Navigation area


      // Footer
      function footerLink(name, id, linkTarget) {
        this.name = name;
        this.linkId = id;
        this.linkTarget = linkTarget;
      }


      self.footerLinks = ko.observableArray([
        new footerLink('About SkyliftAI', 'about', 'https://skyliftai.com/'),
        new footerLink('Contact Us', 'contactUs', 'https://skyliftai.com/contact'),
        new footerLink('Your Privacy Rights', 'yourPrivacyRights', 'https://skyliftai.com/privacy-policy')
      ]);

      // self.footerLinks.push({'name' : 'name','linkId' :'linkId','linkTarget' :'sayooj'});
      // self.footerLinks.push({'name' : 'name1','linkId' :'linkId1','linkTarget' :'sayooj'});
       self.footerLinksDP = new ArrayDataProvider(self.footerLinks,{keyAttributes: 'name'});

     self.SignIn = ko.observable('N');

     self.goToSignIn = function() {
      router.go({path : 'signin'});
      self.SignIn('N');
    };
  
    ControllerViewModel.prototype.signIn = function() {
      if (!self.localFlow) {
        self.goToSignIn();
        return;
      }
    }


    ControllerViewModel.prototype.onAppSuccess = function() {
      self.username(sessionStorage.getItem("userName"));
      self.onepDepName(sessionStorage.getItem("Dep_Name"));
      self.onepDepUrl(sessionStorage.getItem("Dep_Url"));
      self.onepDepType(sessionStorage.getItem("Dep_Type"));
      self.SignIn('Y');
      if (self.onepDepType() == 'bda'){
        self.appName('SkyliftAI MigDB For BigData Targets')
      }
      else if(self.onepDepType() == 'sybase'){
        self.appName('SkyliftAI MigDB For Sybase')
      }
    };

    ControllerViewModel.prototype.onLoginSuccess = function() {
      router.go({path : 'ggadmin'});
      self.SignIn('Y');
    };

    self.selectedMenuItem = ko.observable('');
  
    self.menuItemAction = function (event,vm) {
      self.selectedMenuItem(event.target.value);
        //User menu Options
      if (self.selectedMenuItem() == 'out')
      {
        self.username('');
        sessionStorage.clear();
      event.preventDefault();
      self.goToSignIn();
      }
      else if (self.selectedMenuItem() == 'seldep'){
        document.querySelector('#RemoteDeploymentDialog').open();
        self.onepDeployList([]);
        $.ajax({
          url: "http://46.137.45.173:9030/api/v2/onep/dep",
          type: 'GET',
          dataType: 'json',
          context: self,
          error: function (e) {
          },
          success: function (data) {
             console.log(data);
            
              for (var i = 0; i < data[0].length; i++) {
              self.onepDeployList.push({'label' : data[0][i].dep , value :  data[0][i].dep} );
              }
              self.onepDeployList.valueHasMutated();
              return self;
          }
      })
      }else if (self.selectedMenuItem() == 'about'){
        document.querySelector('#abtDialog').open();
      }
      else if (self.selectedMenuItem() == 'help'){
        document.querySelector('#helpDialog').open();
      }
    }

    self.onepDepListDP = new ArrayDataProvider(self.onepDeployList, {keyAttributes: 'value'});

    self.SwitchDeployment = (event) =>{
      self.onepDepUrl('');
      $.ajax({
        url: "http://46.137.45.173:9030/api/v2/onep/depurl",
        type: 'POST',
        data: JSON.stringify({
          dep: self.DepName()
      }),
        dataType: 'json',
        context: self,
        error: function (e) {
        },
        success: function (data) {        
          console.log(data);  
            self.onepDepUrl(data[0]);
            self.onepDepName(self.DepName());
            self.onepDepType(data[2]);
            sessionStorage.setItem("Dep_Name", self.onepDepName());
            sessionStorage.setItem("Dep_Url", self.onepDepUrl());
            sessionStorage.setItem("Dep_Type", self.onepDepType());
            location.reload();
            return self;
        }

    })
   };

  }

     return new ControllerViewModel();
  }
);
