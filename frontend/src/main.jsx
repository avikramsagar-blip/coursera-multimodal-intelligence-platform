import React from "react";
import ReactDOM from "react-dom/client";
import "@fontsource/poppins";
import App from "./App";
import "./styles/global.css";
import { ThemeProvider } from "@mui/material/styles";

import CssBaseline from "@mui/material/CssBaseline";

import theme from "./theme";

ReactDOM.createRoot(document.getElementById("root")).render(

    <ThemeProvider theme={theme}>

        <CssBaseline />

        <App />

    </ThemeProvider>

);
