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
import PlayArrowIcon from "@mui/icons-material/PlayArrow";

function CourseBanner({ course, onAITutor }) {
  return (
    <Paper
      elevation={3}
      sx={{
        overflow: "hidden",
        borderRadius: 4,
        mb: 4,
      }}
    >
      {/* Banner */}
      <Box
        sx={{
          height: 250,
          background:
            "linear-gradient(135deg, #4F46E5, #7C3AED)",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <SchoolIcon
          sx={{
            color: "#fff",
            fontSize: 110,
          }}
        />
      </Box>

      {/* Content */}
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
          sx={{
            mb: 3,
            lineHeight: 1.8,
          }}
        >
          {course.description}
        </Typography>

        {/* Chips */}
        <Box
          sx={{
            display: "flex",
            flexWrap: "wrap",
            gap: 1.5,
            mb: 4,
          }}
        >
          <Chip
            color="primary"
            label={course.category}
          />

          <Chip
            color="secondary"
            label={course.difficulty}
          />

          <Chip
            color="success"
            label={`₹ ${course.price}`}
          />
        </Box>

        {/* Buttons */}
        <Stack
          direction={{
            xs: "column",
            sm: "row",
          }}
          spacing={2}
        >
          <Button
            variant="contained"
            size="large"
            startIcon={<PlayArrowIcon />}
          >
            Start Learning
          </Button>

          <Button
            variant="outlined"
            size="large"
            startIcon={<SmartToyIcon />}
            onClick={onAITutor}
          >
            AI Tutor
          </Button>
        </Stack>
      </Box>
    </Paper>
  );
}

export default CourseBanner;