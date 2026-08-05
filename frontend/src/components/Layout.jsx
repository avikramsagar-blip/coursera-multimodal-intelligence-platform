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
            flexGrow: 1,
            padding: 3,
            backgroundColor: "#f5f7fb",
            minHeight: "100vh",
          }}
        >
          {children}
        </Box>
      </Box>
    </>
  );
}

export default Layout;