const vscode = require('vscode');
const cp = require('child_process');
const path = require('path');
const os = require('os');

function isProcessDoc(doc){return /\.process\.(ya?ml|json)$/i.test(doc.fileName)}
function runCli(args, cwd){return new Promise((resolve)=>cp.execFile('process-code',args,{cwd},(err,stdout,stderr)=>resolve({code:err?err.code||1:0,stdout,stderr})))}

function activate(context){
  const diagnostics=vscode.languages.createDiagnosticCollection('process-as-code');context.subscriptions.push(diagnostics);
  async function validate(doc){if(!doc||!isProcessDoc(doc))return;await doc.save();const result=await runCli(['validate',doc.fileName],path.dirname(doc.fileName));const items=[];for(const line of (result.stdout+'\n'+result.stderr).split(/\r?\n/)){if(line.startsWith('ERROR:')||line.startsWith('WARNING:')){const severity=line.startsWith('ERROR:')?vscode.DiagnosticSeverity.Error:vscode.DiagnosticSeverity.Warning;items.push(new vscode.Diagnostic(new vscode.Range(0,0,0,1),line.replace(/^(ERROR|WARNING):\s*/,''),severity))}}diagnostics.set(doc.uri,items);return result}
  context.subscriptions.push(vscode.commands.registerCommand('processAsCode.validate',async()=>{const doc=vscode.window.activeTextEditor?.document;if(!doc||!isProcessDoc(doc)){vscode.window.showWarningMessage('Open a *.process.yaml or *.process.json file.');return}const r=await validate(doc);if(r?.code===0)vscode.window.showInformationMessage('Process as Code: contract is valid.');else vscode.window.showErrorMessage('Process as Code: validation failed.')}));
  context.subscriptions.push(vscode.commands.registerCommand('processAsCode.preview',async()=>{const doc=vscode.window.activeTextEditor?.document;if(!doc||!isProcessDoc(doc))return;await doc.save();const target=path.join(os.tmpdir(),`process-as-code-${Date.now()}.md`);const r=await runCli(['docs',doc.fileName,'-o',target],path.dirname(doc.fileName));if(r.code!==0){vscode.window.showErrorMessage('Could not generate process documentation.');return}const preview=await vscode.workspace.openTextDocument(target);await vscode.window.showTextDocument(preview,{preview:true})}));
  context.subscriptions.push(vscode.workspace.onDidSaveTextDocument(validate));
  if(vscode.window.activeTextEditor)validate(vscode.window.activeTextEditor.document);
}
function deactivate(){}
module.exports={activate,deactivate};
