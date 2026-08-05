import { useState } from "react";

import {
  TextField,
  InputAdornment,
  IconButton,
} from "@mui/material";

import Visibility from "@mui/icons-material/Visibility";
import VisibilityOff from "@mui/icons-material/VisibilityOff";

function PasswordField({
  value,
  onChange,
  label = "Password",
}) {
  const [show, setShow] = useState(false);

  return (
    <TextField
      fullWidth
      margin="normal"
      label={label}
      type={show ? "text" : "password"}
      value={value}
      onChange={onChange}
      InputProps={{
        endAdornment: (
          <InputAdornment position="end">
            <IconButton
              onClick={() => setShow(!show)}
            >
              {show ? (
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