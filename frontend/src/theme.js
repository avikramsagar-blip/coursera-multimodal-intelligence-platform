import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    primary: {
      main: "#4F46E5", // Indigo
    },

    secondary: {
      main: "#7C3AED", // Violet
    },

    success: {
      main: "#10B981",
    },

    warning: {
      main: "#F59E0B",
    },

    error: {
      main: "#EF4444",
    },

    background: {
      default: "#F8FAFC",
      paper: "#FFFFFF",
    },
  },

  shape: {
    borderRadius: 16,
  },

  typography: {
    fontFamily: `"Inter","Poppins","Roboto",sans-serif`,

    h4: {
      fontWeight: 700,
    },

    h5: {
      fontWeight: 700,
    },

    h6: {
      fontWeight: 700,
    },

    button: {
      textTransform: "none",
      fontWeight: 600,
    },
  },

  components: {

    MuiCard: {

      styleOverrides: {

        root: {

          borderRadius: 20,

          boxShadow:
            "0px 10px 30px rgba(0,0,0,.08)",

          transition: ".3s",

          "&:hover": {

            transform: "translateY(-6px)",

            boxShadow:
              "0px 18px 40px rgba(0,0,0,.15)",

          },

        },

      },

    },

    MuiButton: {

      styleOverrides: {

        root: {

          borderRadius: 12,

          paddingInline: 22,

          paddingBlock: 10,

        },

      },

    },

    MuiPaper: {

      styleOverrides: {

        root: {

          borderRadius: 18,

        },

      },

    },

  },

});

export default theme;