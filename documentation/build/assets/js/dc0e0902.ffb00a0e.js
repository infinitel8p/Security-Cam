"use strict";(self.webpackChunkdocumentation=self.webpackChunkdocumentation||[]).push([[270],{8524:(e,n,s)=>{s.r(n),s.d(n,{assets:()=>a,contentTitle:()=>r,default:()=>h,frontMatter:()=>t,metadata:()=>c,toc:()=>o});var i=s(4848),l=s(8453);const t={sidebar_position:3},r="Bluetooth & Script Setup",c={id:"setup/script",title:"Bluetooth & Script Setup",description:"Install",source:"@site/docs/setup/script.mdx",sourceDirName:"setup",slug:"/setup/script",permalink:"/docs/setup/script",draft:!1,unlisted:!1,editUrl:"https://github.com/infinitel8p/Security-Cam/documentation/docs/setup/script.mdx",tags:[],version:"current",sidebarPosition:3,frontMatter:{sidebar_position:3},sidebar:"tutorialSidebar",previous:{title:"WiFi Setup",permalink:"/docs/setup/wifi"},next:{title:"Tutorial - Basics",permalink:"/docs/category/tutorial---basics"}},a={},o=[{value:"Install",id:"install",level:2},{value:"Pairing",id:"pairing",level:2},{value:"Install Node.js",id:"install-nodejs",level:2},{value:"Install GPAC",id:"install-gpac",level:2},{value:"Script Setup",id:"script-setup",level:2},{value:"Modify the Script",id:"modify-the-script",level:4},{value:"Run the Script",id:"run-the-script",level:4}];function d(e){const n={code:"code",h1:"h1",h2:"h2",h4:"h4",li:"li",ol:"ol",p:"p",pre:"pre",ul:"ul",...(0,l.R)(),...e.components};return(0,i.jsxs)(i.Fragment,{children:[(0,i.jsx)(n.h1,{id:"bluetooth--script-setup",children:"Bluetooth & Script Setup"}),"\n",(0,i.jsx)(n.h2,{id:"install",children:"Install"}),"\n",(0,i.jsx)(n.p,{children:"To set up the necessary libraries and tools, run the following commands:"}),"\n",(0,i.jsx)(n.pre,{children:(0,i.jsx)(n.code,{className:"language-bash",children:"sudo apt-get update\r\nsudo apt-get install python3-picamera\r\nsudo apt-get install python3-pip\n"})}),"\n",(0,i.jsx)(n.p,{children:"Now clone the repository and install the required Python libraries:"}),"\n",(0,i.jsx)(n.pre,{children:(0,i.jsx)(n.code,{className:"language-bash",children:"git clone https://github.com/infinitel8p/Security-Cam/\r\ncd Security-Cam\r\nsudo pip3 install -r requirements.txt\n"})}),"\n",(0,i.jsx)(n.h2,{id:"pairing",children:"Pairing"}),"\n",(0,i.jsxs)(n.ul,{children:["\n",(0,i.jsx)(n.li,{children:"Ensure your Bluetooth device's visibility is turned on."}),"\n",(0,i.jsxs)(n.li,{children:["On the Raspberry Pi, run ",(0,i.jsx)(n.code,{children:"bluetoothctl"}),"."]}),"\n",(0,i.jsxs)(n.li,{children:["In the bluetoothctl prompt, enter the following commands:","\n",(0,i.jsx)(n.pre,{children:(0,i.jsx)(n.code,{className:"language-bash",children:"agent on\r\ndefault-agent\r\nscan on\n"})}),"\n"]}),"\n",(0,i.jsxs)(n.li,{children:["Once you see the MAC address of your device, pair with it using: ",(0,i.jsx)(n.code,{children:"pair XX:XX:XX:XX:XX:XX"}),"."]}),"\n",(0,i.jsxs)(n.li,{children:["Trust the device using: ",(0,i.jsx)(n.code,{children:"trust XX:XX:XX:XX:XX:XX"}),"."]}),"\n",(0,i.jsxs)(n.li,{children:[(0,i.jsx)(n.code,{children:"exit"})," from ",(0,i.jsx)(n.code,{children:"bluetoothctl"}),"."]}),"\n"]}),"\n",(0,i.jsx)(n.h2,{id:"install-nodejs",children:"Install Node.js"}),"\n",(0,i.jsxs)(n.ul,{children:["\n",(0,i.jsxs)(n.li,{children:["Install Node.js with the following commands:","\n",(0,i.jsxs)(n.ol,{children:["\n",(0,i.jsxs)(n.li,{children:["Update the Raspberry Pi","\n",(0,i.jsx)(n.pre,{children:(0,i.jsx)(n.code,{className:"language-bash",children:"sudo apt update\r\nsudo apt upgrade\n"})}),"\n"]}),"\n",(0,i.jsxs)(n.li,{children:["Check the Node.js Version Available","\n",(0,i.jsx)(n.pre,{children:(0,i.jsx)(n.code,{className:"language-bash",children:"apt-cache policy nodejs\n"})}),"\n","The output should look like this:","\n",(0,i.jsx)(n.pre,{children:(0,i.jsx)(n.code,{className:"language-bash",children:"pi@raspberrypizero2:~ $ apt-cache policy nodejs\r\nnodejs:\r\nInstalled: (none)\r\nCandidate: 12.22.12~dfsg-1~deb11u4\r\nVersion table:\r\n   12.22.12~dfsg-1~deb11u4 500\r\n      500 http://raspbian.raspberrypi.org/raspbian bullseye/main armhf Packages\n"})}),"\n","The apt-cache policy nodejs command shows that Node.js version 12.22.12 is available for installation from the Raspberry Pi repositories, but it hasn't been installed (Installed: (none))."]}),"\n",(0,i.jsxs)(n.li,{children:["Install Node.JS and npm on the Raspberry Pi","\n",(0,i.jsx)(n.pre,{children:(0,i.jsx)(n.code,{className:"language-bash",children:"sudo apt install nodejs\r\nsudo apt install npm\n"})}),"\n"]}),"\n",(0,i.jsxs)(n.li,{children:["Check the version","\n",(0,i.jsx)(n.pre,{children:(0,i.jsx)(n.code,{className:"language-bash",children:"nodejs -v  # Checks Node.js version\r\nnpm -v     # Checks npm version\n"})}),"\n"]}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,i.jsx)(n.h2,{id:"install-gpac",children:"Install GPAC"}),"\n",(0,i.jsxs)(n.ul,{children:["\n",(0,i.jsxs)(n.li,{children:["Install GPAC with the following commands:","\n",(0,i.jsxs)(n.ol,{children:["\n",(0,i.jsxs)(n.li,{children:["Install GPAC","\n",(0,i.jsx)(n.pre,{children:(0,i.jsx)(n.code,{className:"language-bash",children:"sudo apt-get update\r\nsudo apt-get install gpac\n"})}),"\n"]}),"\n",(0,i.jsxs)(n.li,{children:["Check if GPAC is installed","\n",(0,i.jsx)(n.pre,{children:(0,i.jsx)(n.code,{className:"language-bash",children:"gpac\n"})}),"\n"]}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,i.jsx)(n.h2,{id:"script-setup",children:"Script Setup"}),"\n",(0,i.jsxs)(n.ol,{children:["\n",(0,i.jsxs)(n.li,{children:["\n",(0,i.jsx)(n.h4,{id:"modify-the-script",children:"Modify the Script"}),"\n",(0,i.jsxs)(n.ul,{children:["\n",(0,i.jsxs)(n.li,{children:["Open the ",(0,i.jsx)(n.code,{children:"config.json"})," file."]}),"\n",(0,i.jsxs)(n.li,{children:["Replace XX:XX:XX:XX:XX",":XX"," with the Bluetooth MAC address of your device (e.g., your smartphone)."]}),"\n",(0,i.jsxs)(n.li,{children:["Replace XX:XX:XX:XX:XX",":XX"," with the WiFi MAC address of your device (e.g., your smartphone)."]}),"\n"]}),"\n",(0,i.jsxs)(n.p,{children:["Your ",(0,i.jsx)(n.code,{children:"config.json"})," could look like this:"]}),"\n",(0,i.jsx)(n.pre,{children:(0,i.jsx)(n.code,{className:"language-json",children:'{\r\n"TARGET_BT_ADDRESSES": [\r\n"12:34:56:78:9A:BC",\r\n],\r\n"TARGET_AP_MAC_ADDRESSES": [\r\n"A1:B2:C3:D4:E5:F6",\r\n]\r\n}\n'})}),"\n",(0,i.jsx)(n.pre,{children:(0,i.jsx)(n.code,{className:"language-json",children:'{\r\n"TARGET_BT_ADDRESSES": [\r\n"12:34:56:78:9A:BC",\r\n"DE:F1:23:45:67:89"\r\n],\r\n"TARGET_AP_MAC_ADDRESSES": [\r\n"A1:B2:C3:D4:E5:F6",\r\n"F6:E5:D4:C3:B2:A1"\r\n]\r\n}\n'})}),"\n"]}),"\n",(0,i.jsxs)(n.li,{children:["\n",(0,i.jsx)(n.h4,{id:"run-the-script",children:"Run the Script"}),"\n",(0,i.jsxs)(n.ul,{children:["\n",(0,i.jsxs)(n.li,{children:["Start the security camera script from within the ",(0,i.jsx)(n.code,{children:"Security-Cam/"})," folder with thefollowing command:","\n",(0,i.jsx)(n.pre,{children:(0,i.jsx)(n.code,{className:"language-bash",children:"python3 main.py\n"})}),"\n"]}),"\n",(0,i.jsxs)(n.li,{children:["Now startt the server with the following command:","\n",(0,i.jsx)(n.pre,{children:(0,i.jsx)(n.code,{className:"language-bash",children:"node ./server/server.js\n"})}),"\n"]}),"\n"]}),"\n"]}),"\n"]})]})}function h(e={}){const{wrapper:n}={...(0,l.R)(),...e.components};return n?(0,i.jsx)(n,{...e,children:(0,i.jsx)(d,{...e})}):d(e)}},8453:(e,n,s)=>{s.d(n,{R:()=>r,x:()=>c});var i=s(6540);const l={},t=i.createContext(l);function r(e){const n=i.useContext(t);return i.useMemo((function(){return"function"==typeof e?e(n):{...n,...e}}),[n,e])}function c(e){let n;return n=e.disableParentContext?"function"==typeof e.components?e.components(l):e.components||l:r(e.components),i.createElement(t.Provider,{value:n},e.children)}}}]);