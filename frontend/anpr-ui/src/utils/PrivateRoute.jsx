import { Navigate } from "react-router-dom"

export default function PrivateRoute({children}){

const token = localStorage.getItem("user")

if(!token){
return <Navigate to="/" />
}

return children

}