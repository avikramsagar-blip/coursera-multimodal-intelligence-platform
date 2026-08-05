import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Stack,
  Box,
} from "@mui/material";

import SchoolIcon from "@mui/icons-material/School";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";

function CourseCard({ course, onOpen }) {
  return (
    <Card
      sx={{
        borderRadius: 5,
        overflow: "hidden",
        boxShadow: 4,
        height: "100%",
        transition: "all .3s ease",

        "&:hover": {
          transform: "translateY(-8px)",
          boxShadow: 10,
        },
      }}
    >
      {/* Banner */}
      <Box
        sx={{
          height: 155,
          background:
            "linear-gradient(135deg,#1976D2,#42A5F5)",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <SchoolIcon
          sx={{
            color: "#fff",
            fontSize: 70,
          }}
        />
      </Box>

      <CardContent>

        <Typography
          variant="h6"
          fontWeight="bold"
          gutterBottom
        >
          {course.title}
        </Typography>

        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            minHeight: 60,
            mb: 2,
          }}
        >
          {course.description}
        </Typography>

        <Stack
          direction="row"
          spacing={1}
          mb={2}
          flexWrap="wrap"
        >
          <Chip
            label={course.category}
            color="primary"
            size="small"
          />

          <Chip
            label={course.difficulty}
            color="success"
            size="small"
          />
        </Stack>

        <Typography
          variant="h5"
          fontWeight="bold"
          color="primary"
        >
          ₹ {course.price}
        </Typography>

      </CardContent>

      <CardActions
        sx={{
          p: 2,
          pt: 0,
        }}
      >
        <Button
          fullWidth
          size="large"
          variant="contained"
          endIcon={<ArrowForwardIcon />}
          onClick={onOpen}
          sx={{
            borderRadius: 3,
            py: 1.2,
            textTransform: "none",
            fontWeight: "bold",
          }}
        >
          Open Course
        </Button>
      </CardActions>
    </Card>
  );
}

export default CourseCard;