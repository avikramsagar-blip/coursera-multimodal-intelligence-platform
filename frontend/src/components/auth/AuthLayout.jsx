import { Box, Paper, Typography } from "@mui/material";
import SchoolIcon from "@mui/icons-material/School";

function AuthLayout({ title, subtitle, children }) {
  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        background:
          "linear-gradient(135deg, #2563EB 0%, #1E3A8A 100%)",
        p: 2,
      }}
    >
      <Paper
        elevation={10}
        sx={{
          width: 450,
          p: 5,
          borderRadius: 4,
        }}
      >
        <Box
          display="flex"
          justifyContent="center"
          mb={2}
        >
          <SchoolIcon
            sx={{
              fontSize: 60,
              color: "#2563EB",
            }}
          />
        </Box>

        <Typography
          variant="h4"
          fontWeight="bold"
          textAlign="center"
        >
          {title}
        </Typography>

        <Typography
          textAlign="center"
          color="gray"
          mb={4}
        >
          {subtitle}
        </Typography>

        {children}
      </Paper>
    </Box>
  );
}

export default AuthLayout;