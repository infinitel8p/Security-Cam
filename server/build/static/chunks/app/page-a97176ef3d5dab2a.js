(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[931],{4697:function(e,t,o){Promise.resolve().then(o.bind(o,7262)),Promise.resolve().then(o.bind(o,4589))},7262:function(e,t,o){"use strict";var r=o(7437),n=o(2265);t.default=()=>{let[e,t]=(0,n.useState)(!1),[o,s]=(0,n.useState)("");(0,n.useEffect)(()=>{s("".concat(window.location.protocol,"//").concat(window.location.hostname,":5005"))},[]);let c=async()=>{try{let r=await fetch("".concat(o,"/toggle_recording"),{method:"POST"}),n=await r.json();r.ok?(t(!e),console.log(n.message)):console.log("Failed to toggle recording")}catch(e){console.error("Error toggling recording:",e)}};return(0,r.jsxs)(r.Fragment,{children:[o&&(0,r.jsx)("img",{src:"".concat(o,"/video_feed"),alt:"Live Stream",style:{width:"100%",height:"100%"}}),(0,r.jsx)("button",{onClick:c,children:e?"Stop Recording":"Start Recording"})]})}},4589:function(e,t,o){"use strict";var r=o(7437),n=o(2265);t.default=()=>{let[e,t]=(0,n.useState)({cpu_temp_celsius:"Loading...",cpu_load_percent:"Loading...",storage_info_gb:{total_gb:"Loading...",used_gb:"Loading..."},ram_usage_mb:{total_mb:"Loading...",used_mb:"Loading..."}}),[o,s]=(0,n.useState)("");return(0,n.useEffect)(()=>{s("".concat(window.location.protocol,"//").concat(window.location.hostname,":5005/system_info"))},[]),(0,n.useEffect)(()=>{o&&(async()=>{try{let e=await fetch(o),r=await e.json();t(r)}catch(e){console.error("Error fetching system info:",e)}})()},[o]),(0,r.jsxs)("div",{className:"grid grid-cols-3 border border-red-200 gap-10",children:[(0,r.jsxs)("div",{className:"border border-red-500 text-center",children:["Temp: ",e.cpu_temp_celsius,"\xb0C"]}),(0,r.jsxs)("div",{className:"border border-red-500 text-center",children:["CPU: ",e.cpu_load_percent,"%"]}),(0,r.jsxs)("div",{className:"border border-red-500 text-center",children:["Storage: ",e.storage_info_gb.used_gb," GB / ",e.storage_info_gb.total_gb," GB"]}),(0,r.jsxs)("div",{className:"border border-red-500 text-center",children:["RAM: ",e.ram_usage_mb.used_mb," MB / ",e.ram_usage_mb.total_mb," MB"]})]})}}},function(e){e.O(0,[971,23,744],function(){return e(e.s=4697)}),_N_E=e.O()}]);