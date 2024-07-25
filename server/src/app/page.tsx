import ClientVideoPlayer from "@/components/ClientVideoPlayer"

const Home = () => {
  return (
    <div className="space-y-10 mx-10">
      <div className="text-center border border-red-500">
        activity timeline - Art Zeitleiste mit activity halt, wann wie lange wer da war
      </div>

      <div className="grid grid-cols-2 border border-red-200 gap-10">
        <div className="border border-red-500 h-96">
          <ClientVideoPlayer url="https://www.youtube.com/watch?v=dQw4w9WgXcQ" />
        </div>
        <div className="border border-red-500">
          (log) monitor -  (un-)befugter zutritt als status ggfs, date time, falls bekannte person/handy auch namen,bild
          <ul className="mt-10">
            <li>Status - Date - Unknown</li>
            <li>Status - Date - Max Mustermann</li>
            <li>Status - Date - Unknown</li>
            <li>Status - Date - Unknown</li>
            <li>Status - Date - Max Musterfrau</li>
          </ul>
        </div>
      </div>

      <div className="grid grid-cols-3 border border-red-200 gap-10">
        <div className="border border-red-500">temp: 20°C</div>
        <div className="border border-red-500">cpu: 20%</div>
        <div className="border border-red-500">storage: 2.69gb / 64gb</div>
      </div>
    </div>
  )
}

export default Home
