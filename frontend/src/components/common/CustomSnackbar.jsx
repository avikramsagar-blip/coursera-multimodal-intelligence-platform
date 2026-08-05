import { Snackbar, Alert } from "@mui/material";

function CustomSnackbar({
  open,
  message,
  severity,
  onClose,
}) {
  return (
    <Snackbar
      open={open}
      autoHideDuration={3000}
      onClose={onClose}
      anchorOrigin={{
        vertical: "top",
        horizontal: "right",
      }}
    >
      <Alert
        severity={severity}
        variant="filled"
        onClose={onClose}
      >
        {message}
      </Alert>
    </Snackbar>
  );
}

export default CustomSnackbar;