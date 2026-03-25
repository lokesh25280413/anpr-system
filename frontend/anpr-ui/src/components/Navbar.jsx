import { Button } from "@mui/material"
import { useNavigate } from "react-router-dom"

export default function Navbar(){

const navigate = useNavigate()

const logout = ()=>{

localStorage.removeItem("user")
navigate("/")

}

return(

<div style={{
display:"flex",
justifyContent:"space-between",
background:"#1e293b",
color:"white",
padding:"15px"
}}>

<h2>ANPR System</h2>

<Button
variant="contained"
onClick={logout}
>
Logout
</Button>

</div>

)

}