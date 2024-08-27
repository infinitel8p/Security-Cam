import React from "react";
import ClientVideoPlayer from "@/components/ClientVideoPlayer";
import SystemMonitor from "@/components/SystemMonitor";

const Home = () => {

  return (
    <div className="space-y-10 mx-10">
      <div className="text-center border border-red-500">
        activity timeline - Art Zeitleiste mit activity halt, wann wie lange wer da war
      </div>

      <div className="grid grid-cols-2 border border-red-200 gap-10">
        <div className="border border-red-500 h-96">
          <ClientVideoPlayer />
        </div>
        {/* <div className="border border-red-500">
          (log) monitor -  (un-)befugter zutritt als status ggfs, date time, falls bekannte person/handy auch namen,bild <br></br>
          JSON?
          <ul className="mt-10">
            <li>Status - Date - Unknown</li>
            <li>Status - Date - Max Mustermann</li>
            <li>Status - Date - Unknown</li>
            <li>Status - Date - Unknown</li>
            <li>Status - Date - Max Musterfrau</li>
          </ul>
        </div> */}

        <div className="border border-red-500">
          <table className="w-full border-collapse bg-white text-left text-sm text-gray-500">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-4 font-medium text-gray-900">Name</th>
                <th scope="col" className="px-6 py-4 font-medium text-gray-900">Date</th>
                <th scope="col" className="px-6 py-4 font-medium text-gray-900">Time</th>
                <th scope="col" className="px-6 py-4 font-medium text-gray-900">State</th>
                <th scope="col" className="px-6 py-4 font-medium text-gray-900"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 border-t border-gray-100">
              <tr className="hover:bg-gray-50">
                <th className="px-6 py-4 font-medium text-gray-900">Helen Howard</th>
                <td className="px-6 py-4">Nov.4 2022</td>
                <td className="px-6 py-4">12:24:59</td>
                <td className="px-6 py-4">
                  <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2 py-1 text-xs font-semibold text-green-600">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-3 w-3">
                      <path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clip-rule="evenodd" />
                    </svg>
                    Authorized
                  </span>
                </td>
                <td className="flex justify-end px-6 py-4 font-medium"><a href="" className="text-primary-700">Edit</a></td>
              </tr>
              <tr className="hover:bg-gray-50">
                <th className="px-6 py-4 font-medium text-gray-900">Helen Howard</th>
                <td className="px-6 py-4">Nov.4 2022</td>
                <td className="px-6 py-4">12:24:59</td>
                <td className="px-6 py-4">
                  <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2 py-1 text-xs font-semibold text-green-600">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-3 w-3">
                      <path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clip-rule="evenodd" />
                    </svg>
                    Authorized
                  </span>
                </td>
                <td className="flex justify-end gap-4 px-6 py-4 font-medium"><a href="" className="text-primary-700">Edit</a></td>
              </tr>
              <tr className="hover:bg-gray-50">
                <th className="px-6 py-4 font-medium text-gray-900">Unknown</th>
                <td className="px-6 py-4">Nov.4 2022</td>
                <td className="px-6 py-4">12:24:59</td>
                <td className="px-6 py-4">
                  <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2 py-1 text-xs font-semibold text-red-600">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-3 w-3">
                      <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                    </svg>
                    Unauthorized
                  </span>
                </td>
                <td className="flex justify-end gap-4 px-6 py-4 font-medium"><a href="" className="text-primary-700">Edit</a></td>
              </tr>
              <tr className="hover:bg-gray-50">
                <th className="px-6 py-4 font-medium text-gray-900">Tom Howard</th>
                <td className="px-6 py-4">Nov.4 2022</td>
                <td className="px-6 py-4">12:24:59</td>
                <td className="px-6 py-4">
                  <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2 py-1 text-xs font-semibold text-green-600">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-3 w-3">
                      <path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clip-rule="evenodd" />
                    </svg>
                    Authorized
                  </span>
                </td>
                <td className="flex justify-end gap-4 px-6 py-4 font-medium"><a href="" className="text-primary-700">Edit</a></td>
              </tr>
              <tr className="hover:bg-gray-50">
                <th className="px-6 py-4 font-medium text-gray-900">Unknown</th>
                <td className="px-6 py-4">Nov.4 2022</td>
                <td className="px-6 py-4">12:24:59</td>
                <td className="px-6 py-4">
                  <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2 py-1 text-xs font-semibold text-green-600">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-3 w-3">
                      <path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clip-rule="evenodd" />
                    </svg>
                    Authorized
                  </span>
                </td>
                <td className="flex justify-end gap-4 px-6 py-4 font-medium"><a href="" className="text-primary-700">Edit</a></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <SystemMonitor />
    </div>
  );
};

export default Home;
