import {
  AppBar,
  Toolbar,
  Typography,
  Button,
} from "@mui/material";

import SchoolIcon from "@mui/icons-material/School";

import { useNavigate } from "react-router-dom";

function Navbar() {

  const navigate = useNavigate();

  function logout() {

    localStorage.removeItem("token");

    navigate("/login");

  }

  return (

    <AppBar position="static">

      <Toolbar>

        <SchoolIcon sx={{ mr: 2 }} />

        <Typography
          variant="h6"
          sx={{ flexGrow: 1 }}
        >

          Coursera Multimodal Intelligence Platform

        </Typography>

        <Button
          color="inherit"
          onClick={logout}
        >

          Logout

        </Button>

      </Toolbar>

    </AppBar>

  );

}

export default Navbar;