(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[938],{4279:function(e,t,s){Promise.resolve().then(s.bind(s,454))},454:function(e,t,s){"use strict";s.r(t),s.d(t,{default:function(){return d}});var r=s(7437),o=s(2265),n=e=>{let{onDirectorySelect:t}=e,[s,n]=(0,o.useState)([]),[a,c]=(0,o.useState)("/"),[i,d]=(0,o.useState)(""),[l,h]=(0,o.useState)("");(0,o.useEffect)(()=>{h("".concat(window.location.protocol,"//").concat(window.location.hostname,":5005/list_directories"))},[]),(0,o.useEffect)(()=>{l&&u(a)},[l,a]);let u=async e=>{try{let t=await fetch("".concat(l,"?path=").concat(encodeURIComponent(e))),s=await t.json();t.ok?(n(s.directories),c(s.current_path)):d(s.error)}catch(e){d("Failed to fetch directories.")}},x=e=>{c(e),t(e)};return(0,r.jsxs)("div",{children:[(0,r.jsxs)("h3",{children:["Current Directory: ",a]}),i&&(0,r.jsx)("div",{style:{color:"red"},children:i}),(0,r.jsx)("ul",{children:s.map(e=>(0,r.jsx)("li",{children:(0,r.jsx)("button",{className:"bg-red-500 m-1 py-1 px-2",onClick:()=>x(e.path),children:e.name})},e.path))})]})};async function a(e,t){try{let s="".concat(window.location.protocol,"//").concat(window.location.hostname,":5005/settings"),r=await fetch(s),o=await r.json();e(o["TARGET_".concat(t,"_ADDRESSES")])}catch(e){console.error("Error fetching ".concat(t," devices:"),e)}}var c=()=>{let[e,t]=(0,o.useState)([]);return(0,o.useEffect)(()=>{a(t,"BT")},[]),(0,r.jsxs)("div",{children:[(0,r.jsxs)("h3",{children:["Bluetooth Devices: ",(0,r.jsx)("span",{className:"text-xs",children:"(need to add pairing and unpairing)"})]}),(0,r.jsx)("ul",{children:e.map((e,t)=>(0,r.jsxs)("li",{children:[e.name,": ",e.address]},t))})]})},i=()=>{let[e,t]=(0,o.useState)([]);return(0,o.useEffect)(()=>{a(t,"AP_MAC")},[]),(0,r.jsxs)("div",{children:[(0,r.jsx)("h3",{children:"Wi-Fi Devices:"}),(0,r.jsx)("ul",{children:e.map((e,t)=>(0,r.jsxs)("li",{children:[e.name,": ",e.address]},t))})]})},d=()=>{let[e,t]=(0,o.useState)(""),[s,a]=(0,o.useState)(""),[d,l]=(0,o.useState)({VideoSaveLocation:"Loading..."});(0,o.useEffect)(()=>{t("".concat(window.location.protocol,"//").concat(window.location.hostname,":5005/settings"))},[]),(0,o.useEffect)(()=>{(async()=>{if(e)try{console.log(e);let t=await fetch(e),s=await t.json();l(s)}catch(e){console.error("Error fetching settings info:",e),l({VideoSaveLocation:"Error loading data"})}})()},[e]);let h=async()=>{try{let t=await fetch(e,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({VideoSaveLocation:s})}),r=await t.json();t.ok?(alert("Settings updated successfully"),l(e=>({...e,VideoSaveLocation:s}))):alert(r.message||"Error updating settings")}catch(e){console.error("Error updating settings:",e),alert("Error updating settings")}};return(0,r.jsxs)("div",{className:"flex flex-col gap-5 space-y-10 px-10 pt-10",children:[(0,r.jsx)("div",{className:"border border-red-500",children:(0,r.jsx)(c,{})}),(0,r.jsx)("div",{className:"border border-red-500",children:(0,r.jsx)(i,{})}),(0,r.jsxs)("div",{className:"flex w-full border border-red-500",children:[(0,r.jsxs)("div",{children:["Video save location: ",(0,r.jsx)("span",{className:"text-blue-700",children:d.VideoSaveLocation})]}),(0,r.jsxs)("div",{className:"flex gap-5 ml-5",children:[(0,r.jsxs)("div",{children:[(0,r.jsx)("h1",{children:"Select a new directory to save the videos:"}),(0,r.jsx)(n,{onDirectorySelect:e=>{a(e)}})]}),(0,r.jsx)("button",{className:"bg-gray-500 border rounded-md p-2 h-10 m-auto",onClick:h,children:"Update Location"})]})]}),(0,r.jsx)("div",{className:"border border-red-500 text-gray-300",children:"modular trigger sensors: TBD"})]})}}},function(e){e.O(0,[971,23,744],function(){return e(e.s=4279)}),_N_E=e.O()}]);