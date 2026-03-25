import { useState } from "react"
import UploadVideo from "../components/UploadVideo"
import LiveCamera from "../components/LiveCamera"

export default function Dashboard(){

const [mode,setMode] = useState("upload")

return(

<div style={{padding:"30px"}}>

<h1>🚗 ANPR Dashboard</h1>

<div style={{marginBottom:"20px"}}>

<button onClick={()=>setMode("upload")}>
Recorded Video
</button>

<button onClick={()=>setMode("live")}>
Live Feed
</button>

</div>

{mode === "upload" && <UploadVideo />}
{mode === "live" && <LiveCamera />}

</div>

)

}