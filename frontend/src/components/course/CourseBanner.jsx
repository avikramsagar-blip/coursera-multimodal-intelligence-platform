import {
  Paper,
  Box,
  Typography,
  Chip,
  Button,
  Stack,
} from "@mui/material";

import SchoolIcon from "@mui/icons-material/School";
import SmartToyIcon from "@mui/icons-material/SmartToy";

function CourseBanner({ course, onAITutor }) {
  return (
    <Paper
      elevation={3}
      sx={{
        borderRadius: 4,
        overflow: "hidden",
        mb: 4,
      }}
    >
      {/* Banner */}
      <Box
        sx={{
          height: 220,
          background:
            "linear-gradient(135deg,#1976D2,#42A5F5)",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <SchoolIcon
          sx={{
            fontSize: 90,
            color: "white",
          }}
        />
      </Box>

      <Box p={4}>

        <Typography
          variant="h4"
          fontWeight="bold"
          gutterBottom
        >
          {course.title}
        </Typography>

        <Typography
          color="text.secondary"
          mb={3}
        >
          {course.description}
        </Typography>

        <Stack
          direction="row"
          spacing={2}
          mb={3}
          flexWrap="wrap"
        >
          <Chip
            label={course.category}
            color="primary"
          />

          <Chip
            label={course.difficulty}
            color="success"
          />

          <Chip
            label={`₹ ${course.price}`}
            color="warning"
          />
        </Stack>

        <Button
          variant="contained"
          size="large"
          startIcon={<SmartToyIcon />}
          onClick={onAITutor}
          sx={{
            borderRadius: 3,
            textTransform: "none",
          }}
        >
          Open AI Tutor
        </Button>

      </Box>
    </Paper>
  );
}

export default CourseBanner;