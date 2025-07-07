define(['ojs/ojcore', 'knockout', 'jquery','appController','ojs/ojarraydataprovider', 'ojs/ojknockout-keyset', 'ojs/ojasyncvalidator-regexp', 'ojs/ojknockout', 
        'ojs/ojbutton', 'ojs/ojprogress-bar', 'ojs/ojmessages'],
    function (oj, ko, $,app, ArrayDataProvider, keySet, AsyncRegExpValidator) {
        class RAGTrainViewModel {
            constructor(context) {
                var self = this;
                self.DepName = context.DepName;
                self.DepType = ko.observable("")
                self.docContent = ko.observable("");
                self.saveDbContent = ko.observable("")
                
                self.viewDoc = ()=>{
                    $.ajax({
                        url: self.DepName() + "/RagDocumentView",
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
                            let content = data.content || "";
                            content = content.replace(/</g, "&lt;").replace(/>/g, "&gt;");
                            const formattedContent = `
                                                        <div class="oj-panel" style="background: #f4f4f4; padding: 10px; border-radius: 6px;">
                                                            <h4 style="margin-top: 0;">Sybase to Oracle Conversion</h4>
                                                            <pre style="
                                                                padding: 10px; 
                                                                border-radius: 6px; 
                                                                font-family: monospace; 
                                                                white-space: pre-wrap;
                                                                margin: 0;
                                                                max-height: 400px;
                                                                overflow: auto;">${content}</pre>
                                                        </div>`;
                            document.getElementById("docDisplay").innerHTML = formattedContent;
                            self.docContent(content)
                        }
                    })
                }

                self.editDoc = ()=>{
                    document.getElementById("docDisplay").style.display = "none"
                    document.getElementById("edit-doc").style.display = "block"
                    document.getElementById("editBtn").style.display = "none"
                    document.getElementById("saveBtn").style.display = "block"
                    document.getElementById("cancelBtn").style.display = "block"
                    setTimeout(() => {
                        const textArea = document.getElementById("text-area");

                        if (textArea) {
                            const innerTextArea = textArea.querySelector("textarea"); 
                            if (innerTextArea) {
                                innerTextArea.scrollTop = innerTextArea.scrollHeight;
                            }
                        }
                    }, 100); 
                }

                self.cancelDoc = ()=>{
                    self.viewDoc();
                    document.getElementById("docDisplay").style.display = "block"
                    document.getElementById("edit-doc").style.display = "none"
                    document.getElementById("editBtn").style.display = "block"
                    document.getElementById("saveBtn").style.display = "none"
                    document.getElementById("cancelBtn").style.display = "none"
                }

                const saveDbLog = ()=>{
                    $.ajax({
                        url: self.DepName() + "/readSaveDBFile",
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
                            let content = data || "";      
                            document.getElementById("edit-doc").style.display = "none" 
                            document.getElementById("saveDoc").style.display = "block"             
                            content = content.replace(/</g, "&lt;").replace(/>/g, "&gt;");
                            const formattedContent = `
                                                        <div class="oj-panel" style="background: #f4f4f4; padding: 10px; border-radius: 6px;">
                                                            <h4 style="margin-top: 0;">Vector DB Save..</h4>
                                                            <pre id="logPreBlock" style="
                                                                padding: 10px; 
                                                                border-radius: 6px; 
                                                                font-family: monospace; 
                                                                white-space: pre-wrap;
                                                                margin: 0;
                                                                max-height: 400px;
                                                                overflow: auto;">${content}</pre>
                                                            <div style="margin-top: 10px;">
                                                            <oj-progress-bar 
                                                                id="progressBar"
                                                                class="oj-sm-margin-2x-top"
                                                                value="-1"
                                                                max="100"
                                                                mode="indeterminate"
                                                                aria-label="Loading...">
                                                            </oj-progress-bar>
                                                        </div>
                                                        </div>`;
                            document.getElementById("saveDoc").innerHTML = formattedContent;
                            setTimeout(() => {
                                const logBlock = document.getElementById("logPreBlock");
                                if (logBlock) {
                                    logBlock.scrollTop = logBlock.scrollHeight;
                                }
                            }, 0);
                            self.saveDbContent(content)
                        }
                    })
                }

                self.saveDoc = ()=>{
                    var intervalId = setInterval(saveDbLog(), 1000);
                    $.ajax({
                        url: self.DepName() + "/saveChromaDB",
                        type: 'POST',
                        data: JSON.stringify({
                            content: self.docContent(),
                        }),
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                clearInterval(intervalId);
                                document.getElementById("saveDoc").style.display = "none"
                                document.getElementById("saveBtn").style.display = "none"  
                                document.getElementById("cancelBtn").style.display = "none" 
                                document.getElementById("editBtn").style.display = "block"        
                                document.getElementById("docDisplay").style.display = "block"        
                                console.log(textStatus);
                            }
                        },
                        success: function (data) {
                            clearInterval(intervalId);
                            document.getElementById("saveDoc").style.display = "none"
                            document.getElementById("saveBtn").style.display = "none"  
                            document.getElementById("cancelBtn").style.display = "none"
                            document.getElementById("editBtn").style.display = "block" 
                            document.getElementById("docDisplay").style.display = "block"  
                            self.messages.push({
                                severity: 'confirmation',
                                summary: 'Vector DB saved successfully!',
                                autoTimeout: 5000
                            });                            
                        }
                    })
                }

                self.messages = ko.observableArray([]);
                self.messagesDataprovider = new ArrayDataProvider(self.messages, { keyAttributes: 'summary' });

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
                        self.viewDoc();
                    }
                };
            }
        }
        return RAGTrainViewModel;
    }
);
