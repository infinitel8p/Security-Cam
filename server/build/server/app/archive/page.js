(()=>{var e={};e.id=467,e.ids=[467],e.modules={7849:e=>{"use strict";e.exports=require("next/dist/client/components/action-async-storage.external")},2934:e=>{"use strict";e.exports=require("next/dist/client/components/action-async-storage.external.js")},5403:e=>{"use strict";e.exports=require("next/dist/client/components/request-async-storage.external")},4580:e=>{"use strict";e.exports=require("next/dist/client/components/request-async-storage.external.js")},4749:e=>{"use strict";e.exports=require("next/dist/client/components/static-generation-async-storage.external")},5869:e=>{"use strict";e.exports=require("next/dist/client/components/static-generation-async-storage.external.js")},399:e=>{"use strict";e.exports=require("next/dist/compiled/next-server/app-page.runtime.prod.js")},1017:e=>{"use strict";e.exports=require("path")},7310:e=>{"use strict";e.exports=require("url")},1389:(e,t,r)=>{"use strict";r.r(t),r.d(t,{GlobalError:()=>a.a,__next_app__:()=>p,originalPathname:()=>u,pages:()=>c,routeModule:()=>h,tree:()=>d}),r(2946),r(7881),r(5866);var s=r(3191),o=r(8716),i=r(7922),a=r.n(i),n=r(5231),l={};for(let e in n)0>["default","tree","pages","GlobalError","originalPathname","__next_app__","routeModule"].indexOf(e)&&(l[e]=()=>n[e]);r.d(t,l);let d=["",{children:["archive",{children:["__PAGE__",{},{page:[()=>Promise.resolve().then(r.bind(r,2946)),"C:\\Users\\Ludo\\Desktop\\Security Cam\\server\\src\\app\\archive\\page.tsx"]}]},{metadata:{icon:[async e=>(await Promise.resolve().then(r.bind(r,3881))).default(e)],apple:[],openGraph:[],twitter:[],manifest:void 0}}]},{layout:[()=>Promise.resolve().then(r.bind(r,7881)),"C:\\Users\\Ludo\\Desktop\\Security Cam\\server\\src\\app\\layout.tsx"],"not-found":[()=>Promise.resolve().then(r.t.bind(r,5866,23)),"next/dist/client/components/not-found-error"],metadata:{icon:[async e=>(await Promise.resolve().then(r.bind(r,3881))).default(e)],apple:[],openGraph:[],twitter:[],manifest:void 0}}],c=["C:\\Users\\Ludo\\Desktop\\Security Cam\\server\\src\\app\\archive\\page.tsx"],u="/archive/page",p={require:r,loadChunk:()=>Promise.resolve()},h=new s.AppPageRouteModule({definition:{kind:o.x.APP_PAGE,page:"/archive/page",pathname:"/archive",bundlePath:"",filename:"",appPaths:[]},userland:{loaderTree:d}})},7893:(e,t,r)=>{Promise.resolve().then(r.t.bind(r,2994,23)),Promise.resolve().then(r.t.bind(r,6114,23)),Promise.resolve().then(r.t.bind(r,9727,23)),Promise.resolve().then(r.t.bind(r,9671,23)),Promise.resolve().then(r.t.bind(r,1868,23)),Promise.resolve().then(r.t.bind(r,4759,23))},6183:(e,t,r)=>{Promise.resolve().then(r.t.bind(r,9404,23))},7972:(e,t,r)=>{Promise.resolve().then(r.bind(r,9058))},9058:(e,t,r)=>{"use strict";r.r(t),r.d(t,{default:()=>i});var s=r(326),o=r(7577);let i=()=>{let[e,t]=(0,o.useState)([]),[r,i]=(0,o.useState)("");(0,o.useEffect)(()=>{},[]),(0,o.useEffect)(()=>{(async()=>{if(r)try{let e=await fetch(r);if(!e.ok)throw Error("Network response was not ok");let s=await e.json();t(s)}catch(e){console.error("Error fetching videos:",e)}})()},[r]);let a=e=>{console.log(`Delete video: ${e}`)};return s.jsx("div",{className:"grid grid-cols-3 gap-5 text-center",children:e.length>0?e.map((e,t)=>{let r,o;let i=e.split("/").pop();if(!i)return null;let n=i.match(/\d+/g);if(n){let[e,t]=n;r=`${e.slice(0,4)}-${e.slice(4,6)}-${e.slice(6,8)}`,o=`${t.slice(0,2)}:${t.slice(2,4)}:${t.slice(4,6)}`}else console.error("No match found in the filename");return(0,s.jsxs)("div",{className:"border border-red-500 flex flex-col justify-between m-2 p-2",children:[(0,s.jsxs)("video",{controls:!0,className:"w-full",onLoadedMetadata:e=>{let r=e.target.duration;document.getElementById(`duration-${t}`).textContent=`Duration: ${Math.floor(r/60)}m ${Math.floor(r%60)}s`},children:[s.jsx("source",{src:`${window.location.protocol}//${window.location.hostname}:5005/stream_video?video_path=${encodeURIComponent(e)}`,type:"video/mp4"}),"Your browser does not support the video tag."]}),(0,s.jsxs)("div",{children:[s.jsx("p",{children:i}),(0,s.jsxs)("p",{children:["Recorded on ",r,", ",o]}),s.jsx("p",{id:`duration-${t}`,children:"Loading duration..."}),(0,s.jsxs)("div",{className:"flex justify-around mt-2",children:[s.jsx("button",{className:"bg-red-500 text-white px-4 py-2",onClick:()=>a(e),children:"Delete"}),s.jsx("a",{href:`${window.location.protocol}//${window.location.hostname}:5005/stream_video?video_path=${encodeURIComponent(e)}`,className:"bg-blue-500 text-white px-4 py-2",download:e.split("/").pop(),children:"Download"})]})]})]},t)}):s.jsx("p",{children:0===e.length?"No videos available.":"Loading videos..."})})}},2946:(e,t,r)=>{"use strict";r.r(t),r.d(t,{$$typeof:()=>a,__esModule:()=>i,default:()=>n});var s=r(8570);let o=(0,s.createProxy)(String.raw`C:\Users\Ludo\Desktop\Security Cam\server\src\app\archive\page.tsx`),{__esModule:i,$$typeof:a}=o;o.default;let n=(0,s.createProxy)(String.raw`C:\Users\Ludo\Desktop\Security Cam\server\src\app\archive\page.tsx#default`)},7881:(e,t,r)=>{"use strict";r.r(t),r.d(t,{default:()=>c,metadata:()=>d});var s=r(9510),o=r(5384),i=r.n(o);r(5023);var a=r(7371);let n=({title:e,slug:t})=>s.jsx("li",{children:s.jsx(a.default,{href:t,className:"w-full hover:bg-blue-500 bg-amber-50 py-2 px-4 border border-blue-500 hover:border-red-500 rounded-md text-zinc-950",children:e})}),l=()=>(0,s.jsxs)("div",{className:"p-6 bg-zinc-950 text-white lg:h-screen lg:fixed lg:w-40 lg:l-0 lg:flex flex-col items-center justify-between",children:[s.jsx("p",{children:"Security-Cam Dashboard"}),s.jsx("nav",{children:(0,s.jsxs)("ul",{className:"flex flex-col gap-y-10",children:[s.jsx(n,{title:"Home",slug:"/"}),s.jsx(n,{title:"Archive",slug:"/archive"})]})}),s.jsx("div",{children:s.jsx("ul",{children:s.jsx(n,{title:"Settings",slug:"/settings"})})})]}),d={title:"Security-Cam Dashboard",description:"A dashboard for your security camera."};function c({children:e}){return s.jsx("html",{lang:"en",children:(0,s.jsxs)("body",{className:i().className,children:[s.jsx(l,{}),s.jsx("div",{className:"ml-40",children:e})]})})}},3881:(e,t,r)=>{"use strict";r.r(t),r.d(t,{default:()=>o});var s=r(6621);let o=e=>[{type:"image/x-icon",sizes:"16x16",url:(0,s.fillMetadataSegment)(".",e.params,"favicon.ico")+""}]},5023:()=>{}};var t=require("../../webpack-runtime.js");t.C(e);var r=e=>t(t.s=e),s=t.X(0,[948,737,621],()=>r(1389));module.exports=s})();