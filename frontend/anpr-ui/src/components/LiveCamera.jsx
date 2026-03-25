import { useState } from "react"

export default function LiveCamera(){

const [active,setActive] = useState(false)

return(

<div>

<h3>Live Camera</h3>

<button onClick={()=>setActive(!active)}>
{active ? "Turn OFF Live Feed" : "+ Turn ON Live Feed"}
</button>

<br/><br/>

{active ? (

<img
src="http://127.0.0.1:8000/live-camera"
width="700"
/>

) : (

<div style={{
width:"700px",
height:"400px",
background:"black",
color:"white",
display:"flex",
alignItems:"center",
justifyContent:"center"
}}>
Turn ON Live Feed
</div>

)}

</div>

)

}