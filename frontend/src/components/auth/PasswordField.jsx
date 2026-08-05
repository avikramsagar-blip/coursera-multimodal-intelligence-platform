import {
  TextField,
  InputAdornment,
  IconButton,
} from "@mui/material";

import { useState } from "react";

import Visibility from "@mui/icons-material/Visibility";
import VisibilityOff from "@mui/icons-material/VisibilityOff";

function PasswordField({
  label = "Password",
  error,
  helperText,
  register,
}) {

  const [showPassword, setShowPassword] = useState(false);

  return (

    <TextField
      fullWidth
      margin="normal"
      label={label}
      type={showPassword ? "text" : "password"}

      error={error}
      helperText={helperText}

      {...register}

      InputProps={{
        endAdornment: (
          <InputAdornment position="end">

            <IconButton
              onClick={() =>
                setShowPassword(!showPassword)
              }
            >

              {showPassword ? (
                <VisibilityOff />
              ) : (
                <Visibility />
              )}

            </IconButton>

          </InputAdornment>
        ),
      }}
    />

  );

}

export default PasswordField;