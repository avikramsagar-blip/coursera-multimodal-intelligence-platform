import Navbar from "./Navbar";
import Sidebar from "./Sidebar";
import { Box } from "@mui/material";

function Layout({ children }) {
  return (
    <>
      <Navbar />

      <Box sx={{ display: "flex" }}>
        <Sidebar />

        <Box
component="main"
sx={{
flexGrow:1,
p:4,
mt:2,
backgroundColor:"#F5F7FB",
minHeight:"calc(100vh - 64px)",
}}
>
        
          {children}
        </Box>
      </Box>
    </>
  );
}

export default Layout;