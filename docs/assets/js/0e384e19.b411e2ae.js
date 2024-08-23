"use strict";(self.webpackChunkdocumentation=self.webpackChunkdocumentation||[]).push([[3976],{619:(e,r,i)=>{i.r(r),i.d(r,{assets:()=>a,contentTitle:()=>o,default:()=>c,frontMatter:()=>s,metadata:()=>d,toc:()=>l});var t=i(4848),n=i(8453);const s={sidebar_position:1},o="Intro",d={id:"intro",title:"Intro",description:"A security camera script for the Raspberry Pi Zero 2 W using the Waveshare RPi Camera (F).",source:"@site/docs/intro.md",sourceDirName:".",slug:"/intro",permalink:"/Security-Cam/docs/intro",draft:!1,unlisted:!1,editUrl:"https://github.com/infinitel8p/Security-Cam/edit/main/documentation/docs/intro.md",tags:[],version:"current",sidebarPosition:1,frontMatter:{sidebar_position:1},sidebar:"tutorialSidebar",next:{title:"Setup",permalink:"/Security-Cam/docs/category/setup"}},a={},l=[{value:"Prerequisites",id:"prerequisites",level:2},{value:"Usage",id:"usage",level:2},{value:"Future Enhancements",id:"future-enhancements",level:2},{value:"Troubleshooting",id:"troubleshooting",level:2},{value:"Contribution Guidelines",id:"contribution-guidelines",level:2},{value:"License",id:"license",level:2}];function h(e){const r={a:"a",br:"br",code:"code",em:"em",h1:"h1",h2:"h2",header:"header",li:"li",p:"p",strong:"strong",ul:"ul",...(0,n.R)(),...e.components};return(0,t.jsxs)(t.Fragment,{children:[(0,t.jsx)(r.header,{children:(0,t.jsx)(r.h1,{id:"intro",children:"Intro"})}),"\n",(0,t.jsxs)(r.p,{children:["A security camera script for the Raspberry Pi Zero 2 W using the Waveshare RPi Camera (F).",(0,t.jsx)(r.br,{}),"\n","The script will start recording a video when the magnetic reed switch is triggered (the door is opened) and the smartphone is not connected to the Raspberry Pi (bluetooth and/or WiFi). The recording will stop when the magnetic reed switch is triggered again (the door is closed)."]}),"\n",(0,t.jsx)(r.p,{children:"Integrations:"}),"\n",(0,t.jsxs)(r.ul,{children:["\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"Magnetic Reed Switch"}),": Integration with a magnetic reed switch to detect door open/close events and trigger recording accordingly."]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"WIFI Detection"}),": Integration with WiFi Access Point to allow user to use WiFi to not trigger recording. Allows user to view recorded videos in the web interface when outside of the home network."]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"Bluetooth Detection"}),": Integration with Bluetooth to allow user to use bluetooth to not trigger recording."]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"Real Time Clock"}),": Integration with a Real Time Clock to keep track of the time when the Raspberry Pi is powered off."]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"Web Dashboard"}),": A web dashboard to view the status of the Raspberry Pi and the recorded videos."]}),"\n"]}),"\n",(0,t.jsx)(r.h2,{id:"prerequisites",children:"Prerequisites"}),"\n",(0,t.jsxs)(r.ul,{children:["\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.a,{href:"https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/",children:"Raspberry Pi Zero 2 W"})," (or Raspberry Pi Zero 2 WH)"]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.a,{href:"https://amzn.eu/d/hULoAo6",children:"Headers"})," for the Raspberry Pi Zero 2 W if you did not choose a Raspberry Pi Zero 2 WH (if you do not feel comfortable soldering the headers you can use solderless headers such as these ",(0,t.jsx)(r.a,{href:"https://www.berrybase.de/en/solderless-stiftleiste-2x-20-polig-rm-2-54-gerade",children:"here"}),")"]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.a,{href:"https://www.berrybase.de/en/noir-kamera-fuer-raspberry-pi-mit-einstellbarem-fokus-und-infrarot-leds",children:"Waveshare RPi Camera (F)"})," or another compatible camera module"]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.a,{href:"https://www.berrybase.de/en/flexkabel-fuer-raspberry-pi-zero-und-kameramodul?number=RPIZ-FLEX-15",children:"Flexcable adapter"})," for the camera module"]}),"\n",(0,t.jsx)(r.li,{children:"Bluetooth-enabled device (e.g., a smartphone) to pair with the Raspberry Pi"}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.a,{href:"https://amzn.eu/d/grjoopD",children:"KY-025 module"})," (Magnetic reed switch)"]}),"\n",(0,t.jsxs)(r.li,{children:["a bunch of ",(0,t.jsx)(r.a,{href:"https://amzn.eu/d/6ZgE4N6",children:"Dupont Jumper Wires"})]}),"\n",(0,t.jsx)(r.li,{children:"Breadboard (optional)"}),"\n",(0,t.jsx)(r.li,{children:(0,t.jsx)(r.a,{href:"https://amzn.eu/d/ikNTko8",children:"DS3231 Real Time Clock Module"})}),"\n"]}),"\n",(0,t.jsx)(r.h2,{id:"usage",children:"Usage"}),"\n",(0,t.jsxs)(r.p,{children:["Once the script is running, the Raspberry Pi will start recording a video when the magnetic reed switch is triggered (the door is opened) and the smartphone is not connected to the Raspberry Pi (bluetooth and/or WiFi). The recording will stop when the magnetic reed switch is triggered again (the door is closed).\nFind out more about the usage ",(0,t.jsx)(r.a,{href:"./basics/start",children:"here"}),"."]}),"\n",(0,t.jsx)(r.h2,{id:"future-enhancements",children:"Future Enhancements"}),"\n",(0,t.jsxs)(r.ul,{children:["\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"Web Interface"}),": A user-friendly interface to view recorded videos. ",(0,t.jsx)(r.strong,{children:(0,t.jsx)(r.em,{children:"WIP"})}),"."]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"Captive Portal"}),": Captive portal to open Web Interface when connecting to the Raspberry Pi's WiFi."]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"System Monitor"}),": A system monitor to view the status of the Raspberry Pi (e.g., CPU temperature, CPU usage, RAM usage, etc.). ",(0,t.jsx)(r.strong,{children:(0,t.jsx)(r.em,{children:"WIP (included in the dashboard)"})}),"."]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"Improved Error Handling"}),": Improved error handling to prevent the script from crashing, server from freezing, etc."]}),"\n"]}),"\n",(0,t.jsx)(r.h2,{id:"troubleshooting",children:"Troubleshooting"}),"\n",(0,t.jsx)(r.p,{children:(0,t.jsx)(r.em,{children:"This section will be populated with common issues and their solutions as they are identified."})}),"\n",(0,t.jsx)(r.h2,{id:"contribution-guidelines",children:"Contribution Guidelines"}),"\n",(0,t.jsxs)(r.p,{children:["If you'd like to contribute to this project, please follow the guidelines in the ",(0,t.jsx)(r.a,{href:"https://github.com/infinitel8p/Security-Cam/blob/main/CONTRIBUTING.md",children:"CONTRIBUTING.md"})," file."]}),"\n",(0,t.jsx)(r.h2,{id:"license",children:"License"}),"\n",(0,t.jsxs)(r.p,{children:["This project is licensed under the ",(0,t.jsx)(r.a,{href:"https://github.com/infinitel8p/Security-Cam/blob/main/LICENSE",children:"MIT License"}),". Please see the ",(0,t.jsx)(r.code,{children:"LICENSE"})," file for more details."]})]})}function c(e={}){const{wrapper:r}={...(0,n.R)(),...e.components};return r?(0,t.jsx)(r,{...e,children:(0,t.jsx)(h,{...e})}):h(e)}},8453:(e,r,i)=>{i.d(r,{R:()=>o,x:()=>d});var t=i(6540);const n={},s=t.createContext(n);function o(e){const r=t.useContext(s);return t.useMemo((function(){return"function"==typeof e?e(r):{...r,...e}}),[r,e])}function d(e){let r;return r=e.disableParentContext?"function"==typeof e.components?e.components(n):e.components||n:o(e.components),t.createElement(s.Provider,{value:r},e.children)}}}]);