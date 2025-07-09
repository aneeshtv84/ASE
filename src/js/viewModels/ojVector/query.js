define(['ojs/ojcore', 'knockout', 'jquery','appController','ojs/ojarraydataprovider', 'ojs/ojknockout-keyset', 'ojs/ojasyncvalidator-regexp', 'ojs/ojknockout', 
        'ojs/ojbutton', 'ojs/ojprogress-bar', 'ojs/ojmessages'],
    function (oj, ko, $,app, ArrayDataProvider, keySet, AsyncRegExpValidator) {
        class RAGQueryViewModel {
            constructor(context) {
                var self = this;
                self.DepName = context.DepName;
                self.DepType = ko.observable("")
                self.searchQuery = ko.observable("");
                self.queryContent = ko.observable("")

                const getQueryLog = ()=>{
                    $.ajax({
                        url: self.DepName() + "/getQueryLog",
                        type: 'GET',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                console.log(textStatus);
                            }
                        },
                        success: function (data) {
                            console.log(data);                            
                            let content = data || "";       
                            content = content.replace(/</g, "&lt;").replace(/>/g, "&gt;");
                            const formattedContent = `<div class="oj-panel" style="background: #f4f4f4; padding: 10px; border-radius: 6px;">
                                                        <pre id="logPreBlock" style="
                                                            padding: 10px; 
                                                            border-radius: 6px; 
                                                            font-family: monospace; 
                                                            white-space: pre-wrap;
                                                            margin: 0;
                                                            max-height: 400px;
                                                            overflow: auto;">${content}</pre>
                                                    </div>`;
                            document.getElementById("query").innerHTML = formattedContent;
                            setTimeout(() => {
                                const logBlock = document.getElementById("logPreBlock");
                                if (logBlock) {
                                    logBlock.scrollTop = logBlock.scrollHeight;
                                }
                            }, 0);
                            self.queryContent(content)
                        }
                    })   
                }

                self.getQuery = ()=>{
                    var intervalId = setInterval(()=>{
                        getQueryLog();
                    }, 1000);
                    $.ajax({
                        url: self.DepName() + "/getQueryContext",
                        type: 'POST',
                        data: JSON.stringify({
                            query: self.searchQuery(),
                        }),
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                console.log(textStatus);
                            }
                        },
                        success: function (data) {
                            clearInterval(intervalId);
                            getQueryLog();
                            console.log(data);                            
                        }
                    })
                }

                self.connected = function () { 
                    if (sessionStorage.getItem("userName")==null) {
                        oj.Router.rootInstance.go('signin');
                    }
                    else{
                        app.onAppSuccess();
                        var DepType = sessionStorage.getItem("Dep_Type");
                        if(DepType == 'sybase'){
                            self.DepType('Sybase');
                        }
                        else if (DepType == 'bda'){
                            self.DepType('BigData Targets');
                        }      
                    }
                };
            }
        }
        return RAGQueryViewModel;
    }
);
