import { useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  TextField,
  Checkbox,
  FormControlLabel,
  Link,
  Box,
} from "@mui/material";

import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import * as yup from "yup";

import api from "../../api/api";
import PasswordField from "./PasswordField";
import LoadingButton from "../common/LoadingButton";
import CustomSnackbar from "../common/CustomSnackbar";

const schema = yup.object({
  email: yup
    .string()
    .email("Enter a valid email")
    .required("Email is required"),

  password: yup
    .string()
    .required("Password is required"),
});

function LoginForm() {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(false);

  const [snackbar, setSnackbar] = useState({
    open: false,
    message: "",
    severity: "success",
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm({
    resolver: yupResolver(schema),
  });

  async function onSubmit(data) {
    try {
      setLoading(true);

      const response = await api.post("/login", data);

      localStorage.setItem(
        "token",
        response.data.access_token
      );

      setSnackbar({
        open: true,
        message: "Login Successful",
        severity: "success",
      });

      setTimeout(() => {
        navigate("/dashboard");
      }, 1000);
    } catch (error) {
      setSnackbar({
        open: true,
        message: "Invalid Email or Password",
        severity: "error",
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <form onSubmit={handleSubmit(onSubmit)}>

        <TextField
          label="Email"
          fullWidth
          margin="normal"
          {...register("email")}
          error={!!errors.email}
          helperText={errors.email?.message}
        />

        <PasswordField
          value={watch("password") || ""}
          onChange={() => {}}
        />

        <input
          type="hidden"
          {...register("password")}
        />

        <TextField
          sx={{ display: "none" }}
          {...register("password")}
        />

        <FormControlLabel
          control={<Checkbox />}
          label="Remember Me"
        />

        <Box
          textAlign="right"
          mb={2}
        >
          <Link
            href="#"
            underline="hover"
          >
            Forgot Password?
          </Link>
        </Box>

        <LoadingButton
          type="submit"
          loading={loading}
        >
          Sign In
        </LoadingButton>

      </form>

      <Box mt={3} textAlign="center">

        <Link
          component="button"
          onClick={() => navigate("/register")}
        >
          Don't have an account? Register
        </Link>

      </Box>

      <CustomSnackbar
        open={snackbar.open}
        message={snackbar.message}
        severity={snackbar.severity}
        onClose={() =>
          setSnackbar({
            ...snackbar,
            open: false,
          })
        }
      />
    </>
  );
}

export default LoginForm;