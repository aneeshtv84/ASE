define([ 'ojs/ojoffcanvas' , 'knockout', 'ojs/ojmodule-element-utils', 'ojs/ojresponsiveutils', 'ojs/ojresponsiveknockoututils', 
         'ojs/ojcorerouter', 'ojs/ojmodulerouter-adapter', 'ojs/ojknockoutrouteradapter', 'ojs/ojurlparamadapter', 
         'ojs/ojarraydataprovider', 'ojs/ojknockouttemplateutils', 'ojs/ojmodule-element','ojs/ojmodule-element-utils','ojs/ojknockout' ,'ojs/ojbutton',
         'ojs/ojdialog','ojs/ojselectsingle'],
  function( OffcanvasUtils , ko , moduleUtils, ResponsiveUtils, ResponsiveKnockoutUtils, CoreRouter, ModuleRouterAdapter,
    KnockoutRouterAdapter, UrlParamAdapter, ArrayDataProvider, KnockoutTemplateUtils  ) {
     function ControllerViewModel() {
        var self = this;

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
       { path: 'Designer', detail : {label: 'Designer',iconClass: 'oj-navigationlist-item-icon fa fa-pencil',dep_url : self.onepDepUrl} },
       { path: 'initial', detail : {label: 'Hetrogeneous Initial Load',iconClass: 'oj-navigationlist-item-icon fa fa-cloud-upload',dep_url : self.onepDepUrl} },
       { path: 'initmon', detail : {label: 'Hetro Initial Load Monitor',iconClass: 'oj-navigationlist-item-icon fa fa-file-code-o',dep_url : self.onepDepUrl} }, 
       { path: 'expdp', detail : {label: 'Homogeneous Initial Load',iconClass: 'oj-navigationlist-item-icon fa fa-cloud-upload',dep_url : self.onepDepUrl} },
       { path: 'expinitmon', detail : {label: 'Homo Initial Load Monitor',iconClass: 'oj-navigationlist-item-icon fa fa-file-code-o',dep_url : self.onepDepUrl} }, 
       { path: 'migrate', detail : {label: 'Analyze Objects',iconClass: 'oj-navigationlist-item-icon demo-icon-font-24 demo-chart-icon-24 font15',dep_url : self.onepDepUrl} }, 
        { path: 'dumplog', detail : {label: 'LogDump',iconClass: 'oj-navigationlist-item-icon demo-icon-font-24 demo-chart-icon-24 font15',dep_url : self.onepDepUrl} }, 
       { path: 'vectordb', detail : {label: 'Vector DB',iconClass: 'oj-navigationlist-item-icon fa fa-database',dep_url : self.onepDepUrl} }, 
        // { path: 'zoneinfo', detail : {label: 'Zone Info',iconClass: 'oj-navigationlist-item-icon demo-icon-font-24 demo-chart-icon-24 font15',dep_url : self.onepDepUrl} }, 
	  //  { path: 'zoneinfo1', detail : {label: 'Zone Info1',iconClass: 'oj-navigationlist-item-icon demo-icon-font-24 demo-chart-icon-24 font15',dep_url : self.onepDepUrl} }, 
	   { path: 'ggadmin', detail : {label: 'Setup',iconClass: 'oj-navigationlist-item-icon fa fa-cogs',dep_url : self.onepDepUrl} }, 
       { path: 'tshoot', detail : {label: 'Troubleshoot',iconClass: 'oj-navigationlist-item-icon fa fa-search',dep_url : self.onepDepUrl} }, 
       { path: 'logfile', detail : {label: 'LogFile',iconClass: 'oj-navigationlist-item-icon fa fa-file-code-o',dep_url : self.onepDepUrl} }
      ];

      // Router setup

      let router = new CoreRouter(navData, {
        urlAdapter: new UrlParamAdapter()
      });
      router.sync();

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
        new footerLink('About SkyliftAI', 'about', 'https://1place1cloud.com/about'),
        new footerLink('Contact Us', 'contactUs', 'https://skyliftai.com/contact'),
        new footerLink('Your Privacy Rights', 'yourPrivacyRights', 'https://1place1cloud.com/privacy-policy')
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
        self.appName('1Place For BigData Targets')
      }
      else if(self.onepDepType() == 'sybase'){
        self.appName('Skylift For Sybase ASE')
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
          url: "http://54.76.132.75:9010/onepdep",
          // url: "/onepdep",
          type: 'GET',
          dataType: 'json',
          context: self,
          error: function (e) {
          },
          success: function (data) {
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
        url: "http://54.76.132.75:9010/onepdepurl",
        // url: "/onepdepurl",
        type: 'POST',
        data: JSON.stringify({
          dep: self.DepName()
      }),
        dataType: 'json',
        context: self,
        error: function (e) {
        },
        success: function (data) {
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
