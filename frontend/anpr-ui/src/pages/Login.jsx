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

export default function Login(){

const [email,setEmail] = useState("")
const [password,setPassword] = useState("")
const navigate = useNavigate()

const login = async ()=>{

try{

await axios.post(
"http://127.0.0.1:8000/login",
null,
{params:{email,password}}
)

localStorage.setItem("user",email)

navigate("/dashboard")

}catch{
alert("Invalid Credentials")
}

}

return(

<div style={{
height:"100vh",
display:"flex",
justifyContent:"center",
alignItems:"center",
background:"linear-gradient(135deg, #1e3c72, #2a5298)"
}}>

<Card style={{
width:"350px",
borderRadius:"15px",
boxShadow:"0 8px 30px rgba(0,0,0,0.2)"
}}>

<CardContent>

<Typography variant="h5" align="center" gutterBottom>
🚗 ANPR Login
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
onClick={login}
>
Login
</Button>

<Button
fullWidth
style={{marginTop:"10px"}}
onClick={()=>navigate("/signup")}
>
Create Account
</Button>

</CardContent>

</Card>

</div>

)

}