(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[938],{4279:function(e,t,s){Promise.resolve().then(s.bind(s,454))},454:function(e,t,s){"use strict";s.r(t),s.d(t,{default:function(){return l}});var o=s(7437),r=s(2265),c=e=>{let{onDirectorySelect:t}=e,[s,c]=(0,r.useState)([]),[n,a]=(0,r.useState)("/"),[i,l]=(0,r.useState)(""),[d,h]=(0,r.useState)("");(0,r.useEffect)(()=>{h("".concat(window.location.protocol,"//").concat(window.location.hostname,":5005/list_directories"))},[]),(0,r.useEffect)(()=>{d&&u(n)},[d,n]);let u=async e=>{try{let t=await fetch("".concat(d,"?path=").concat(encodeURIComponent(e))),s=await t.json();t.ok?(c(s.directories),a(s.current_path)):l(s.error)}catch(e){l("Failed to fetch directories.")}},f=e=>{a(e),t(e)};return(0,o.jsxs)("div",{children:[(0,o.jsxs)("h3",{children:["Current Directory: ",n]}),i&&(0,o.jsx)("div",{style:{color:"red"},children:i}),(0,o.jsx)("ul",{children:s.map(e=>(0,o.jsx)("li",{children:(0,o.jsx)("button",{className:"bg-red-500 m-1",onClick:()=>f(e.path),children:e.name})},e.path))})]})};async function n(e,t){try{let s="".concat(window.location.protocol,"//").concat(window.location.hostname,":5005/settings"),o=await fetch(s),r=await o.json();e(r["TARGET_".concat(t,"_ADDRESSES")])}catch(e){console.error("Error fetching ".concat(t," devices:"),e)}}var a=()=>{let[e,t]=(0,r.useState)([]);return(0,r.useEffect)(()=>{n(t,"BT")},[]),(0,o.jsxs)("div",{children:[(0,o.jsx)("h3",{children:"Bluetooth Devices:"}),(0,o.jsx)("ul",{children:e.map((e,t)=>(0,o.jsxs)("li",{children:[e.name,": ",e.address]},t))})]})},i=()=>{let[e,t]=(0,r.useState)([]);return(0,r.useEffect)(()=>{n(t,"AP_MAC")},[]),(0,o.jsxs)("div",{children:[(0,o.jsx)("h3",{children:"Wi-Fi Devices:"}),(0,o.jsx)("ul",{children:e.map((e,t)=>(0,o.jsxs)("li",{children:[e.name,": ",e.address]},t))})]})},l=()=>{let[e,t]=(0,r.useState)(""),[s,n]=(0,r.useState)(""),[l,d]=(0,r.useState)({VideoSaveLocation:"Loading..."});(0,r.useEffect)(()=>{t("".concat(window.location.protocol,"//").concat(window.location.hostname,":5005/settings"))},[]),(0,r.useEffect)(()=>{(async()=>{if(e)try{console.log(e);let t=await fetch(e),s=await t.json();d(s)}catch(e){console.error("Error fetching settings info:",e),d({VideoSaveLocation:"Error loading data"})}})()},[e]);let h=async()=>{try{let t=await fetch(e,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({VideoSaveLocation:s})}),o=await t.json();t.ok?(alert("Settings updated successfully"),d(e=>({...e,VideoSaveLocation:s}))):alert(o.message||"Error updating settings")}catch(e){console.error("Error updating settings:",e),alert("Error updating settings")}};return(0,o.jsxs)("div",{className:"flex flex-col gap-5 space-y-10 px-10 pt-10",children:[(0,o.jsx)("div",{className:"border border-red-500",children:(0,o.jsx)(a,{})}),(0,o.jsx)("div",{className:"border border-red-500",children:(0,o.jsx)(i,{})}),(0,o.jsxs)("div",{className:"flex w-full border border-red-500",children:[(0,o.jsxs)("div",{children:["Video save location: ",(0,o.jsx)("span",{className:"text-blue-700",children:l.VideoSaveLocation})]}),(0,o.jsxs)("div",{className:"flex gap-5 ml-5",children:[(0,o.jsxs)("div",{children:[(0,o.jsx)("h1",{children:"Select a new directory to save the videos:"}),(0,o.jsx)(c,{onDirectorySelect:e=>{n(e)}})]}),(0,o.jsx)("button",{className:"bg-gray-200",onClick:h,children:"Update Location"})]})]}),(0,o.jsx)("div",{className:"border border-red-500 text-gray-300",children:"modular trigger sensors: TBD"})]})}}},function(e){e.O(0,[971,23,744],function(){return e(e.s=4279)}),_N_E=e.O()}]);