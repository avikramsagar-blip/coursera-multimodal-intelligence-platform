import { Box, Typography } from "@mui/material";

function DashboardHeader() {
  return (
    <Box mb={4}>
      <Typography
        variant="h4"
        fontWeight="bold"
      >
        🎓 Learning Dashboard
      </Typography>

      <Typography
        color="text.secondary"
        mt={1}
      >
        Continue your AI-powered learning journey.
      </Typography>
    </Box>
  );
}

export default DashboardHeader;