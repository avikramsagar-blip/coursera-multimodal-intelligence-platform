import { createTheme } from "@mui/material/styles";

const theme = createTheme({

    palette:{

        primary:{
            main:"#2563EB"
        },

        secondary:{
            main:"#14B8A6"
        },

        background:{
            default:"#F8FAFC"
        }

    },

    typography:{

        fontFamily:"Poppins"

    },

    shape:{

        borderRadius:12

    }

});

export default theme;