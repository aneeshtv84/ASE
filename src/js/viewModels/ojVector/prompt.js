define(['ojs/ojcore', 'knockout', 'jquery','appController','ojs/ojarraydataprovider', 'ojs/ojknockout-keyset', 'ojs/ojasyncvalidator-regexp', 'ojs/ojknockout', 
        'ojs/ojbutton', 'ojs/ojprogress-bar', 'ojs/ojmessages'],
    function (oj, ko, $,app, ArrayDataProvider, keySet, AsyncRegExpValidator) {
        class RAGPromptModel {
            constructor(context) {
                var self = this;
                self.DepName = context.DepName;
                self.DepType = ko.observable("")
                self.docTableContent = ko.observable("");
                self.docProcContent = ko.observable("");
                self.docCodeContent = ko.observable("");
                self.saveDbContent = ko.observable("")
                
                self.viewTablePrompt = ()=>{
                    $.ajax({
                        url: self.DepName() + "/TablePromptView",
                        type: 'GET',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                // console.log(textStatus);
                            }
                        },
                        success: function (data) {
                            let content = data.content || "";
                            content = content.replace(/</g, "&lt;").replace(/>/g, "&gt;");
                            const formattedContent = `
                                                        <div class="oj-panel" style="background: #f4f4f4; padding: 10px; border-radius: 6px;">
                                                            <h4 style="margin-top: 0;">Table Prompt</h4>
                                                            <pre style="
                                                                padding: 10px; 
                                                                border-radius: 6px; 
                                                                font-family: monospace; 
                                                                white-space: pre-wrap;
                                                                margin: 0;
                                                                max-height: 400px;
                                                                overflow: auto;">${content}</pre>
                                                        </div>`;
                            document.getElementById("tableDocDisplay").innerHTML = formattedContent;
                            self.docTableContent(content)
                        }
                    })
                }

                self.viewProcPrompt = ()=>{
                    $.ajax({
                        url: self.DepName() + "/ProcPromptView",
                        type: 'GET',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                // console.log(textStatus);
                            }
                        },
                        success: function (data) {
                            let content = data.content || "";
                            content = content.replace(/</g, "&lt;").replace(/>/g, "&gt;");
                            const formattedContent = `
                                                        <div class="oj-panel" style="background: #f4f4f4; padding: 10px; border-radius: 6px;">
                                                            <h4 style="margin-top: 0;">Procedure Prompt</h4>
                                                            <pre style="
                                                                padding: 10px; 
                                                                border-radius: 6px; 
                                                                font-family: monospace; 
                                                                white-space: pre-wrap;
                                                                margin: 0;
                                                                max-height: 400px;
                                                                overflow: auto;">${content}</pre>
                                                        </div>`;
                            document.getElementById("procDocDisplay").innerHTML = formattedContent;
                            self.docProcContent(content)
                        }
                    })
                }

                self.viewCodePrompt = ()=>{
                    $.ajax({
                        url: self.DepName() + "/CodePromptView",
                        type: 'GET',
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                // console.log(textStatus);
                            }
                        },
                        success: function (data) {
                            let content = data.content || "";
                            content = content.replace(/</g, "&lt;").replace(/>/g, "&gt;");
                            const formattedContent = `
                                                        <div class="oj-panel" style="background: #f4f4f4; padding: 10px; border-radius: 6px;">
                                                            <h4 style="margin-top: 0;">Code Prompt</h4>
                                                            <pre style="
                                                                padding: 10px; 
                                                                border-radius: 6px; 
                                                                font-family: monospace; 
                                                                white-space: pre-wrap;
                                                                margin: 0;
                                                                max-height: 400px;
                                                                overflow: auto;">${content}</pre>
                                                        </div>`;
                            document.getElementById("codeDocDisplay").innerHTML = formattedContent;
                            self.docCodeContent(content)
                        }
                    })
                }

                self.editTableDoc = ()=>{
                    document.getElementById("tableDocDisplay").style.display = "none"
                    document.getElementById("edit-table-doc").style.display = "block"
                    document.getElementById("editTableBtn").style.display = "none"
                    document.getElementById("saveTableBtn").style.display = "block"
                    document.getElementById("cancelTableBtn").style.display = "block"
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

                self.editProcDoc = ()=>{
                    document.getElementById("procDocDisplay").style.display = "none"
                    document.getElementById("edit-proc-doc").style.display = "block"
                    document.getElementById("editProcBtn").style.display = "none"
                    document.getElementById("saveProcBtn").style.display = "block"
                    document.getElementById("cancelProcBtn").style.display = "block"
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

                self.editCodeDoc = ()=>{
                    document.getElementById("codeDocDisplay").style.display = "none"
                    document.getElementById("edit-code-doc").style.display = "block"
                    document.getElementById("editCodeBtn").style.display = "none"
                    document.getElementById("saveCodeBtn").style.display = "block"
                    document.getElementById("cancelCodeBtn").style.display = "block"
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

                self.cancelTableDoc = ()=>{
                    self.viewTablePrompt();
                    document.getElementById("tableDocDisplay").style.display = "block"
                    document.getElementById("edit-table-doc").style.display = "none"
                    document.getElementById("editTableBtn").style.display = "block"
                    document.getElementById("saveTableBtn").style.display = "none"
                    document.getElementById("cancelTableBtn").style.display = "none"
                }

                self.cancelProcDoc = ()=>{
                    self.viewProcPrompt();
                    document.getElementById("procDocDisplay").style.display = "block"
                    document.getElementById("edit-proc-doc").style.display = "none"
                    document.getElementById("editProcBtn").style.display = "block"
                    document.getElementById("saveProcBtn").style.display = "none"
                    document.getElementById("cancelProcBtn").style.display = "none"
                }

                self.cancelCodeDoc = ()=>{
                    self.viewCodePrompt();
                    document.getElementById("codeDocDisplay").style.display = "block"
                    document.getElementById("edit-code-doc").style.display = "none"
                    document.getElementById("editCodeBtn").style.display = "block"
                    document.getElementById("saveCodeBtn").style.display = "none"
                    document.getElementById("cancelCodeBtn").style.display = "none"
                }

                self.saveTableDoc = ()=>{
                    $.ajax({
                        url: self.DepName() + "/saveTablePrompt",
                        type: 'POST',
                        data: JSON.stringify({
                            prompt: self.docTableContent(),
                        }),
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.getElementById("saveTableBtn").style.display = "none"  
                                document.getElementById("cancelTableBtn").style.display = "none" 
                                document.getElementById("edit-table-doc").style.display = "none"  
                                document.getElementById("editTableBtn").style.display = "block"        
                                document.getElementById("tableDocDisplay").style.display = "block"        
                                // console.log(textStatus);
                                self.messages.push({
                                    severity: 'error',
                                    summary: 'Please Check Again',
                                    autoTimeout: 5000
                                }); 
                            }
                        },
                        success: function (data) {
                            document.getElementById("edit-table-doc").style.display = "none"  
                            document.getElementById("saveTableBtn").style.display = "none"  
                            document.getElementById("cancelTableBtn").style.display = "none"
                            document.getElementById("editTableBtn").style.display = "block" 
                            document.getElementById("tableDocDisplay").style.display = "block" 
                            self.messages.push({
                                severity: 'confirmation',
                                summary: 'Table Prompt saved successfully!',
                                autoTimeout: 5000
                            });                            
                        }
                    })
                }

                self.saveProcDoc = ()=>{
                    $.ajax({
                        url: self.DepName() + "/saveProcPrompt",
                        type: 'POST',
                        data: JSON.stringify({
                            prompt: self.docProcContent(),
                        }),
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.getElementById("saveProcBtn").style.display = "none"  
                                document.getElementById("cancelProcBtn").style.display = "none" 
                                document.getElementById("edit-proc-doc").style.display = "none"  
                                document.getElementById("editProcBtn").style.display = "block"        
                                document.getElementById("procDocDisplay").style.display = "block"        
                                // console.log(textStatus);
                                self.messages.push({
                                    severity: 'error',
                                    summary: 'Please Check Again',
                                    autoTimeout: 5000
                                }); 
                            }
                        },
                        success: function (data) {
                            document.getElementById("edit-proc-doc").style.display = "none"  
                            document.getElementById("saveProcBtn").style.display = "none"  
                            document.getElementById("cancelProcBtn").style.display = "none"
                            document.getElementById("editProcBtn").style.display = "block" 
                            document.getElementById("procDocDisplay").style.display = "block" 
                            self.messages.push({
                                severity: 'confirmation',
                                summary: 'Procedure Prompt saved successfully!',
                                autoTimeout: 5000
                            });                            
                        }
                    })
                }

                self.saveCodeDoc = ()=>{
                    $.ajax({
                        url: self.DepName() + "/saveCodePrompt",
                        type: 'POST',
                        data: JSON.stringify({
                            prompt: self.docCodeContent(),
                        }),
                        dataType: 'json',
                        timeout: sessionStorage.getItem("timeInetrval"),
                        context: self,
                        error: function (xhr, textStatus, errorThrown) {
                            if(textStatus == 'timeout' || textStatus == 'error'){
                                document.getElementById("saveCodeBtn").style.display = "none"  
                                document.getElementById("cancelCodeBtn").style.display = "none" 
                                document.getElementById("edit-code-doc").style.display = "none"  
                                document.getElementById("editCodeBtn").style.display = "block"        
                                document.getElementById("codeDocDisplay").style.display = "block"        
                                // console.log(textStatus);
                                self.messages.push({
                                    severity: 'error',
                                    summary: 'Please Check Again',
                                    autoTimeout: 5000
                                }); 
                            }
                        },
                        success: function (data) {
                            document.getElementById("edit-code-doc").style.display = "none"  
                            document.getElementById("saveCodeBtn").style.display = "none"  
                            document.getElementById("cancelCodeBtn").style.display = "none"
                            document.getElementById("editCodeBtn").style.display = "block" 
                            document.getElementById("codeDocDisplay").style.display = "block" 
                            self.messages.push({
                                severity: 'confirmation',
                                summary: 'Code Prompt saved successfully!',
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
                        self.viewTablePrompt();
                        self.viewCodePrompt();
                        self.viewProcPrompt();
                    }
                };
            }
        }
        return RAGPromptModel;
    }
);
