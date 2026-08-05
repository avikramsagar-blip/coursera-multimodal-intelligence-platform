import { useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  InputAdornment,
  Alert,
} from "@mui/material";

import { LoadingButton } from "@mui/lab";

import Visibility from "@mui/icons-material/Visibility";
import VisibilityOff from "@mui/icons-material/VisibilityOff";
import SchoolIcon from "@mui/icons-material/School";

import api from "../api/api";

function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin() {
    if (!email.trim() || !password.trim()) {
      setError("Please enter email and password");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const response = await api.post("/login", {
        email,
        password,
      });

      localStorage.setItem(
        "token",
        response.data.access_token
      );

      navigate("/dashboard");

    } catch (err) {

      setError("Invalid Email or Password");

    } finally {

      setLoading(false);

    }
  }

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        background:
          "linear-gradient(135deg,#2563EB,#1E3A8A)",
      }}
    >
      <Paper
        elevation={12}
        sx={{
          width: 430,
          p: 5,
          borderRadius: 4,
        }}
      >
        <Box textAlign="center">

          <SchoolIcon
            sx={{
              fontSize: 60,
              color: "#2563EB",
            }}
          />

          <Typography
            variant="h4"
            fontWeight="bold"
            mt={1}
          >
            Welcome Back
          </Typography>

          <Typography
            color="text.secondary"
            mb={4}
          >
            Coursera AI Learning Platform
          </Typography>

        </Box>

        {error && (
          <Alert
            severity="error"
            sx={{ mb: 2 }}
          >
            {error}
          </Alert>
        )}

        <TextField
          fullWidth
          label="Email"
          margin="normal"
          type="email"
          value={email}
          onChange={(e) =>
            setEmail(e.target.value)
          }
        />

        <TextField
          fullWidth
          label="Password"
          margin="normal"
          type={
            showPassword
              ? "text"
              : "password"
          }
          value={password}
          onChange={(e) =>
            setPassword(e.target.value)
          }
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={() =>
                    setShowPassword(
                      !showPassword
                    )
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

        <LoadingButton
          loading={loading}
          variant="contained"
          fullWidth
          size="large"
          sx={{
            mt: 3,
            py: 1.5,
            borderRadius: 2,
            textTransform: "none",
            fontSize: "16px",
          }}
          onClick={handleLogin}
        >
          Login
        </LoadingButton>

        <Typography
          textAlign="center"
          mt={3}
        >
          Don't have an account?

          <Typography
            component="span"
            sx={{
              color: "#2563EB",
              cursor: "pointer",
              ml: 1,
              fontWeight: "bold",
            }}
            onClick={() =>
              navigate("/register")
            }
          >
            Register
          </Typography>

        </Typography>

      </Paper>
    </Box>
  );
}

export default Login;