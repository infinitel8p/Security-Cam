"use strict";(self.webpackChunkdocumentation=self.webpackChunkdocumentation||[]).push([[3976],{619:(e,r,n)=>{n.r(r),n.d(r,{assets:()=>l,contentTitle:()=>o,default:()=>d,frontMatter:()=>s,metadata:()=>h,toc:()=>a});var t=n(4848),i=n(8453);const s={sidebar_position:1},o="Intro",h={id:"intro",title:"Intro",description:"A security camera script for the Raspberry Pi Zero W using the Waveshare RPi Camera (F).",source:"@site/docs/intro.md",sourceDirName:".",slug:"/intro",permalink:"/Security-Cam/docs/intro",draft:!1,unlisted:!1,editUrl:"https://github.com/infinitel8p/Security-Cam/edit/main/documentation/docs/intro.md",tags:[],version:"current",sidebarPosition:1,frontMatter:{sidebar_position:1},sidebar:"tutorialSidebar",next:{title:"Setup",permalink:"/Security-Cam/docs/category/setup"}},l={},a=[{value:"Table of Contents",id:"table-of-contents",level:2},{value:"Prerequisites",id:"prerequisites",level:2},{value:"Setup",id:"setup",level:2},{value:"Hardware setup",id:"hardware-setup",level:3},{value:"WiFi setup",id:"wifi-setup",level:3},{value:"Bluetooth and Script setup",id:"bluetooth-and-script-setup",level:3},{value:"Usage",id:"usage",level:2},{value:"Future Enhancements",id:"future-enhancements",level:2},{value:"Troubleshooting",id:"troubleshooting",level:2},{value:"Contribution Guidelines",id:"contribution-guidelines",level:2},{value:"License",id:"license",level:2}];function c(e){const r={a:"a",br:"br",code:"code",em:"em",h1:"h1",h2:"h2",h3:"h3",li:"li",ol:"ol",p:"p",strong:"strong",ul:"ul",...(0,i.R)(),...e.components};return(0,t.jsxs)(t.Fragment,{children:[(0,t.jsx)(r.h1,{id:"intro",children:"Intro"}),"\n",(0,t.jsxs)(r.p,{children:["A security camera script for the Raspberry Pi Zero W using the Waveshare RPi Camera (F).",(0,t.jsx)(r.br,{}),"\n","The script will start recording a video when the magnetic reed switch is triggered (the door is opened) and the smartphone is not connected to the Raspberry Pi (bluetooth and/or WiFi). The recording will stop when the magnetic reed switch is triggered again (the door is closed)."]}),"\n",(0,t.jsx)(r.p,{children:"Integrations:"}),"\n",(0,t.jsxs)(r.ul,{children:["\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"Magnetic Reed Switch"}),": Integration with a magnetic reed switch to detect door open/close events and trigger recording accordingly."]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"WIFI Detection"}),": Integration with WiFi Access Point to allow user to use bluetooth or WiFi to not trigger recording. Allows user to view recorded videos in the web interface when outside of the home network."]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"Bluetooth Detection"}),": Integration with Bluetooth to allow user to use bluetooth to not trigger recording."]}),"\n"]}),"\n",(0,t.jsx)(r.h2,{id:"table-of-contents",children:"Table of Contents"}),"\n",(0,t.jsxs)(r.ul,{children:["\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.a,{href:"#intro",children:"Intro"}),"\n",(0,t.jsxs)(r.ul,{children:["\n",(0,t.jsx)(r.li,{children:(0,t.jsx)(r.a,{href:"#table-of-contents",children:"Table of Contents"})}),"\n",(0,t.jsx)(r.li,{children:(0,t.jsx)(r.a,{href:"#prerequisites",children:"Prerequisites"})}),"\n",(0,t.jsx)(r.li,{children:(0,t.jsx)(r.a,{href:"#setup",children:"Setup"})}),"\n",(0,t.jsx)(r.li,{children:(0,t.jsx)(r.a,{href:"#usage",children:"Usage"})}),"\n",(0,t.jsx)(r.li,{children:(0,t.jsx)(r.a,{href:"#future-enhancements",children:"Future Enhancements"})}),"\n",(0,t.jsx)(r.li,{children:(0,t.jsx)(r.a,{href:"#troubleshooting",children:"Troubleshooting"})}),"\n",(0,t.jsx)(r.li,{children:(0,t.jsx)(r.a,{href:"#contribution-guidelines",children:"Contribution Guidelines"})}),"\n",(0,t.jsx)(r.li,{children:(0,t.jsx)(r.a,{href:"#license",children:"License"})}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,t.jsx)(r.h2,{id:"prerequisites",children:"Prerequisites"}),"\n",(0,t.jsxs)(r.ul,{children:["\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.a,{href:"https://www.raspberrypi.com/products/raspberry-pi-zero-w/",children:"Raspberry Pi Zero W"})," (or Raspberry Pi Zero WH)"]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.a,{href:"https://amzn.eu/d/hULoAo6",children:"Headers"})," for the Raspberry Pi Zero W if you did not choose a Raspberry Pi Zero WH (if you do not feel comfortable soldering the headers you can use solderless headers such as these ",(0,t.jsx)(r.a,{href:"https://www.berrybase.de/en/solderless-stiftleiste-2x-20-polig-rm-2-54-gerade",children:"here"}),")"]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.a,{href:"https://www.berrybase.de/en/noir-kamera-fuer-raspberry-pi-mit-einstellbarem-fokus-und-infrarot-leds",children:"Waveshare RPi Camera (F)"})," or another compatible camera module"]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.a,{href:"https://www.berrybase.de/en/flexkabel-fuer-raspberry-pi-zero-und-kameramodul?number=RPIZ-FLEX-15",children:"Flexcable adapter"})," for the camera module"]}),"\n",(0,t.jsx)(r.li,{children:"Bluetooth-enabled device (e.g., a smartphone) to pair with the Raspberry Pi"}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.a,{href:"https://amzn.eu/d/grjoopD",children:"KY-025 module"})," (Magnetic reed switch)"]}),"\n",(0,t.jsxs)(r.li,{children:["a bunch of ",(0,t.jsx)(r.a,{href:"https://amzn.eu/d/6ZgE4N6",children:"Dupont Jumper Wires"})]}),"\n",(0,t.jsx)(r.li,{children:"Breadboard (optional)"}),"\n",(0,t.jsx)(r.li,{children:(0,t.jsx)(r.a,{href:"https://amzn.eu/d/ikNTko8",children:"DS3231 Real Time Clock Module"})}),"\n"]}),"\n",(0,t.jsx)(r.h2,{id:"setup",children:"Setup"}),"\n",(0,t.jsxs)(r.p,{children:["The following sections will explain how to set up the Raspberry Pi Zero W. It is assumed that the Raspberry Pi Zero W is already set up and running (Optional - set up VNC if you have a hard time working in a headless setup). If you need help setting up the Raspberry Pi Zero W, please refer to the ",(0,t.jsx)(r.a,{href:"https://www.raspberrypi.org/documentation/",children:"Raspberry Pi Documentation"}),"."]}),"\n",(0,t.jsxs)(r.ol,{children:["\n",(0,t.jsxs)(r.li,{children:["\n",(0,t.jsx)(r.h3,{id:"hardware-setup",children:"Hardware setup"}),"\n","The Instructions to the hardware setup can be found ",(0,t.jsx)(r.a,{href:"./setup/hardware",children:"here"}),". If you are new to the project, please start here.",(0,t.jsx)(r.br,{}),"\n","They explain how to connect the camera module and the magnetic reed switch to the Raspberry Pi and serve as entry point to the project."]}),"\n",(0,t.jsxs)(r.li,{children:["\n",(0,t.jsx)(r.h3,{id:"wifi-setup",children:"WiFi setup"}),"\n","The Instructions to the WiFi setup can be found ",(0,t.jsx)(r.a,{href:"./setup/wifi",children:"here"}),".",(0,t.jsx)(r.br,{}),"\n","They explain how to set up the Raspberry Pi as an access point and how to connect to it. This will be necessary to connect to the Raspberry Pi when outside of the home network and to access the web interface."]}),"\n",(0,t.jsxs)(r.li,{children:["\n",(0,t.jsx)(r.h3,{id:"bluetooth-and-script-setup",children:"Bluetooth and Script setup"}),"\n","The Instructions to the Bluetooth setup and the script setup can be found ",(0,t.jsx)(r.a,{href:"./setup/script",children:"here"}),".\nThey explain how to pair the Raspberry Pi with a Bluetooth device and how to set up the script."]}),"\n"]}),"\n",(0,t.jsx)(r.h2,{id:"usage",children:"Usage"}),"\n",(0,t.jsx)(r.p,{children:"Once the script is running, the Raspberry Pi will start recording a video when the magnetic reed switch is triggered (the door is opened) and the smartphone is not connected to the Raspberry Pi (bluetooth and/or WiFi). The recording will stop when the magnetic reed switch is triggered again (the door is closed)."}),"\n",(0,t.jsx)(r.h2,{id:"future-enhancements",children:"Future Enhancements"}),"\n",(0,t.jsxs)(r.ul,{children:["\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"Web Interface"}),": A user-friendly interface to view recorded videos. ",(0,t.jsx)(r.strong,{children:(0,t.jsx)(r.em,{children:"WIP"})}),"."]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"Captive Portal"}),": Captive portal to open Web Interface when connecting to the Raspberry Pi's WiFi."]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"System Monitor"}),": A system monitor to view the status of the Raspberry Pi (e.g., CPU temperature, CPU usage, RAM usage, etc.)."]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"Improved Error Handling"}),": Improved error handling to prevent the script from crashing, server from freezing, etc."]}),"\n"]}),"\n",(0,t.jsx)(r.h2,{id:"troubleshooting",children:"Troubleshooting"}),"\n",(0,t.jsx)(r.p,{children:(0,t.jsx)(r.em,{children:"This section will be populated with common issues and their solutions as they are identified."})}),"\n",(0,t.jsx)(r.h2,{id:"contribution-guidelines",children:"Contribution Guidelines"}),"\n",(0,t.jsx)(r.p,{children:"If you'd like to contribute to this project, please follow these guidelines:"}),"\n",(0,t.jsxs)(r.ol,{children:["\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"Fork the Repository"}),": Create a fork of this repository to your account."]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"Clone the Fork"}),": Clone the forked repository to your local machine."]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"Create a New Branch"}),": Always create a new branch for your changes."]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"Make Changes"}),": Implement your changes, enhancements, or bug fixes."]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"Commit and Push"}),": Commit your changes and push them to your fork."]}),"\n",(0,t.jsxs)(r.li,{children:[(0,t.jsx)(r.strong,{children:"Create a Pull Request"}),": Create a pull request from your fork to the main repository."]}),"\n"]}),"\n",(0,t.jsx)(r.h2,{id:"license",children:"License"}),"\n",(0,t.jsxs)(r.p,{children:["This project is licensed under the ",(0,t.jsx)(r.a,{href:"https://github.com/infinitel8p/Security-Cam/blob/main/LICENSE",children:"MIT License"}),". Please see the ",(0,t.jsx)(r.code,{children:"LICENSE"})," file for more details."]})]})}function d(e={}){const{wrapper:r}={...(0,i.R)(),...e.components};return r?(0,t.jsx)(r,{...e,children:(0,t.jsx)(c,{...e})}):c(e)}},8453:(e,r,n)=>{n.d(r,{R:()=>o,x:()=>h});var t=n(6540);const i={},s=t.createContext(i);function o(e){const r=t.useContext(s);return t.useMemo((function(){return"function"==typeof e?e(r):{...r,...e}}),[r,e])}function h(e){let r;return r=e.disableParentContext?"function"==typeof e.components?e.components(i):e.components||i:o(e.components),t.createElement(s.Provider,{value:r},e.children)}}}]);