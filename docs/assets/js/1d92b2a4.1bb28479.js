"use strict";(self.webpackChunkdocumentation=self.webpackChunkdocumentation||[]).push([[4082],{5987:(e,t,s)=>{s.r(t),s.d(t,{assets:()=>o,contentTitle:()=>c,default:()=>u,frontMatter:()=>a,metadata:()=>i,toc:()=>d});var n=s(4848),r=s(8453);const a={sidebar_position:1},c="Start with Security-Cam",i={id:"basics/start",title:"Start with Security-Cam",description:"Now that you have set up your Raspberry Pi, you can start with the Security-Cam project.",source:"@site/docs/basics/start.mdx",sourceDirName:"basics",slug:"/basics/start",permalink:"/Security-Cam/docs/basics/start",draft:!1,unlisted:!1,editUrl:"https://github.com/infinitel8p/Security-Cam/edit/main/documentation/docs/basics/start.mdx",tags:[],version:"current",sidebarPosition:1,frontMatter:{sidebar_position:1},sidebar:"tutorialSidebar",previous:{title:"Usage",permalink:"/Security-Cam/docs/category/usage"}},o={},d=[{value:"Setup",id:"setup",level:2}];function h(e){const t={admonition:"admonition",code:"code",h1:"h1",h2:"h2",header:"header",p:"p",pre:"pre",...(0,r.R)(),...e.components};return(0,n.jsxs)(n.Fragment,{children:[(0,n.jsx)(t.header,{children:(0,n.jsx)(t.h1,{id:"start-with-security-cam",children:"Start with Security-Cam"})}),"\n",(0,n.jsx)(t.p,{children:"Now that you have set up your Raspberry Pi, you can start with the Security-Cam project."}),"\n",(0,n.jsx)(t.p,{children:"Run:"}),"\n",(0,n.jsx)(t.pre,{children:(0,n.jsx)(t.code,{className:"language-bash",children:"cd /opt/security-cam\nsudo chmod +x start.sh\nsudo ./start.sh\n"})}),"\n",(0,n.jsx)(t.h2,{id:"setup",children:"Setup"}),"\n",(0,n.jsx)(t.admonition,{type:"warning",children:(0,n.jsx)(t.p,{children:"\u26a0\ufe0f DONT FOLLOW THESE STEPS YET. \u26a0\ufe0f\nThe following steps are subject to change. They are based on the current state of the project and may be outdated.\nSince the project is still in development, the setup process may change in the future."})}),"\n",(0,n.jsx)(t.p,{children:"Allow pi to Run chmod Without Password:"}),"\n",(0,n.jsx)(t.pre,{children:(0,n.jsx)(t.code,{className:"language-bash",children:"sudo visudo\n"})}),"\n",(0,n.jsx)(t.p,{children:"Add the following line:"}),"\n",(0,n.jsx)(t.pre,{children:(0,n.jsx)(t.code,{className:"language-bash",children:"pi ALL=(ALL) NOPASSWD: /bin/chmod +x /opt/security-cam/start.sh\n"})}),"\n",(0,n.jsx)(t.p,{children:"Create the Service File"}),"\n",(0,n.jsx)(t.pre,{children:(0,n.jsx)(t.code,{className:"language-bash",children:"sudo bash -c 'cat <<EOF > /etc/systemd/system/security-cam.service\n[Unit]\nDescription=Security Cam Flask and Node.js Servers\nAfter=network.target\n\n[Service]\nType=simple\nUser=pi\nWorkingDirectory=/opt/security-cam\nExecStartPre=/usr/bin/sudo /bin/chmod +x /opt/security-cam/start.sh\nExecStart=/opt/security-cam/start.sh\nRestart=on-failure\n\n[Install]\nWantedBy=multi-user.target\nEOF'\n"})}),"\n",(0,n.jsx)(t.p,{children:"Reload the systemd manager configuration"}),"\n",(0,n.jsx)(t.pre,{children:(0,n.jsx)(t.code,{className:"language-bash",children:"sudo systemctl daemon-reload\n"})}),"\n",(0,n.jsx)(t.p,{children:"Enable the service to start on boot"}),"\n",(0,n.jsx)(t.pre,{children:(0,n.jsx)(t.code,{className:"language-bash",children:"sudo systemctl enable security-cam.service\n"})}),"\n",(0,n.jsx)(t.p,{children:"Start the service"}),"\n",(0,n.jsx)(t.pre,{children:(0,n.jsx)(t.code,{className:"language-bash",children:"sudo systemctl start security-cam.service\n"})}),"\n",(0,n.jsx)(t.p,{children:"Check the status of the service"}),"\n",(0,n.jsx)(t.pre,{children:(0,n.jsx)(t.code,{className:"language-bash",children:"sudo systemctl status security-cam.service\n"})}),"\n",(0,n.jsxs)(t.p,{children:["You should now be able to access the Security-Cam web interface by navigating to ",(0,n.jsx)(t.code,{children:"http://<raspberry-pi-ip>:5000"})," in your web browser."]}),"\n",(0,n.jsxs)(t.p,{children:["The ip address of your Raspberry Pi can vary. If you are connected to the Raspberry Pi's AP and you have followed the instructions on how to set it up, you can access the web interface by navigating to ",(0,n.jsx)(t.code,{children:"http://192.168.10.1:5000"})," in your web browser. If you are connected to the same network as the Raspberry Pi, you can find the ip address by running ",(0,n.jsx)(t.code,{children:"hostname -I"})," on the Raspberry Pi."]})]})}function u(e={}){const{wrapper:t}={...(0,r.R)(),...e.components};return t?(0,n.jsx)(t,{...e,children:(0,n.jsx)(h,{...e})}):h(e)}},8453:(e,t,s)=>{s.d(t,{R:()=>c,x:()=>i});var n=s(6540);const r={},a=n.createContext(r);function c(e){const t=n.useContext(a);return n.useMemo((function(){return"function"==typeof e?e(t):{...t,...e}}),[t,e])}function i(e){let t;return t=e.disableParentContext?"function"==typeof e.components?e.components(r):e.components||r:c(e.components),n.createElement(a.Provider,{value:t},e.children)}}}]);