import { useState } from "react"
import axios from "axios"
import {
  TextField,
  Button,
  Card,
  CardContent,
  Typography
} from "@mui/material"
import { useNavigate } from "react-router-dom"

export default function Signup(){

const [email,setEmail] = useState("")
const [password,setPassword] = useState("")
const navigate = useNavigate()

const signup = async ()=>{

try{

await axios.post(
"http://127.0.0.1:8000/signup",
null,
{params:{email,password}}
)

localStorage.setItem("user",email)

navigate("/dashboard")

}catch{
alert("Signup failed")
}

}

return(

<div style={{
height:"100vh",
display:"flex",
justifyContent:"center",
alignItems:"center",
background:"linear-gradient(135deg, #0f2027, #203a43, #2c5364)"
}}>

<Card style={{
width:"350px",
borderRadius:"15px",
boxShadow:"0 8px 30px rgba(0,0,0,0.2)"
}}>

<CardContent>

<Typography variant="h5" align="center" gutterBottom>
Create Account
</Typography>

<TextField
label="Email"
fullWidth
margin="normal"
onChange={(e)=>setEmail(e.target.value)}
/>

<TextField
label="Password"
type="password"
fullWidth
margin="normal"
onChange={(e)=>setPassword(e.target.value)}
/>

<Button
variant="contained"
fullWidth
style={{marginTop:"20px"}}
onClick={signup}
>
Sign Up
</Button>

<Button
fullWidth
style={{marginTop:"10px"}}
onClick={()=>navigate("/")}
>
Back to Login
</Button>

</CardContent>

</Card>

</div>

)

}