import { useState } from "react"
import axios from "axios"

export default function UploadVideo(){

const [file,setFile] = useState(null)
const [plates,setPlates] = useState([])
const [loading,setLoading] = useState(false)

const upload = async ()=>{

if(!file){
alert("Please select a video")
return
}

setLoading(true)
setPlates([])

try{

const formData = new FormData()
formData.append("file",file)

const res = await axios.post(
"http://127.0.0.1:8000/upload-video",
formData
)

setPlates(res.data.plates || [])

}catch(e){
alert("Error processing video")
}

setLoading(false)
}

return(

<div style={{padding:"20px"}}>

<h2>🎥 Upload Video</h2>

<input
type="file"
onChange={(e)=>setFile(e.target.files[0])}
/>

<br/><br/>

<button onClick={upload}>
Start Analysis
</button>

<br/><br/>

{/* LOADING */}
{loading && (
<h3 style={{color:"orange"}}>
⏳ Analyzing video... please wait
</h3>
)}

{/* RESULTS */}
{!loading && plates.length > 0 && (
<div>
<h3>Detected Plates:</h3>

{plates.map((p,i)=>(
<div key={i} style={{
background:"#222",
color:"white",
padding:"10px",
margin:"10px 0",
borderRadius:"8px"
}}>
🚗 {p.plate} <br/>
🕒 {p.time}
</div>
))}

</div>
)}

{/* NO RESULT */}
{!loading && plates.length === 0 && (
<p>No vehicles detected</p>
)}

</div>

)

}