import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Avatar,
} from "@mui/material";

import SchoolIcon from "@mui/icons-material/School";
import LogoutIcon from "@mui/icons-material/Logout";
import { useNavigate } from "react-router-dom";

function Navbar() {
  const navigate = useNavigate();

  function logout() {
    localStorage.removeItem("token");
    navigate("/login");
  }

  return (
    <AppBar
      position="fixed"
      elevation={2}
      sx={{
        backgroundColor: "#1976D2",
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar>

        {/* Left Logo */}
        <Avatar
          sx={{
            bgcolor: "white",
            color: "#1976D2",
            mr: 2,
          }}
        >
          <SchoolIcon />
        </Avatar>

        {/* Center Title */}
        <Box
          sx={{
            flex: 1,
            display: "flex",
            justifyContent: "center",
          }}
        >
          <Typography
            variant="h6"
            fontWeight="bold"
            sx={{
              textAlign: "center",
            }}
          >
            Coursera Multimodal Intelligence Platform
          </Typography>
        </Box>

        {/* Right Button */}
        <Button
          variant="outlined"
sx={{
color:"#fff",
borderColor:"#fff",

"&:hover":{

borderColor:"#fff",

background:"rgba(255,255,255,.12)"

}
}}
          startIcon={<LogoutIcon />}
          onClick={logout}
          sx={{
            borderRadius: 2,
            textTransform: "none",
          }}
        >
          Logout
        </Button>

      </Toolbar>
    </AppBar>
  );
}

export default Navbar;